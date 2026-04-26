# [INPUT]: 依赖 llm.client, llm.prompts, graph.store, graph.embeddings, models.draft, evaluators, engine.evolution
# [OUTPUT]: 对外提供 DraftGenerator
# [POS]: engine 包的草稿生成核心，检索→组装→生成→解析引注→回填引文→自动评估→冲突检测→持久化→写进化信号
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone

from harnetics.graph import store
from harnetics.llm.client import HarneticsLLM
from harnetics.llm.prompts import DRAFT_SYSTEM_PROMPT, build_context
from harnetics.models.draft import AlignedDraft, Citation, Conflict, DraftRequest
from harnetics.evaluators import build_default_bus

# [📎 DOC-XXX-XXX §section_id]
_CITATION_RE = re.compile(r"\[📎\s*(DOC-[A-Z]{3}-\d{3})\s*§([\w.-]+)\]")
logger = logging.getLogger("uvicorn.error")


class DraftGenerator:
    """检索→组装→生成→解析引注→冲突检测流水线。"""

    def __init__(self, llm: HarneticsLLM | None = None, embedding_store=None) -> None:
        self._llm = llm or HarneticsLLM()
        self._emb = embedding_store  # EmbeddingStore，可选

    def generate(self, request: dict) -> AlignedDraft:
        draft_id = f"DRAFT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        generated_by = _llm_identifier(self._llm)
        subject = request.get("subject", "")
        related_doc_ids: list[str] = request.get("related_doc_ids", [])
        template_id: str = request.get("template_id", "")
        logger.info(
            "draft.generator.start draft_id=%s subject=%r related_doc_count=%d template_id=%s generated_by=%s",
            draft_id,
            subject,
            len(related_doc_ids),
            template_id or "<none>",
            generated_by,
        )

        # ---- 检索相关章节 ----
        sections: list[dict] = []
        if self._emb and subject:
            try:
                sections = self._emb.search_similar(subject, top_k=12)
            except Exception as exc:
                logger.warning(
                    "draft.generator.embedding_search_failed draft_id=%s error_type=%s error=%s",
                    draft_id,
                    type(exc).__name__,
                    exc,
                )
                pass
        # 如果没有 embedding，fallback 到直接取指定文档的章节
        if not sections and related_doc_ids:
            for doc_id in related_doc_ids[:5]:
                for sec in store.get_sections(doc_id):
                    sections.append({
                        "doc_id": sec.doc_id,
                        "section_id": sec.section_id,
                        "heading": sec.heading,
                        "text": sec.content,
                    })

        # ---- 提取 ICD 参数 ----
        icd_params: list[dict] = []
        for doc_id in related_doc_ids:
            doc = store.get_document(doc_id)
            if doc and doc.doc_type == "ICD":
                for p in store.get_icd_parameters(doc_id):
                    icd_params.append({
                        "param_id": p.param_id, "name": p.name,
                        "value": p.value, "unit": p.unit,
                        "subsystem_a": p.subsystem_a, "subsystem_b": p.subsystem_b,
                    })

        # ---- 获取模板内容 ----
        template_content = ""
        if template_id:
            template_secs = store.get_sections(template_id)
            template_content = "\n\n".join(
                f"{'#' * s.level} {s.heading}\n{s.content}" for s in template_secs
            )

        # ---- 调用 LLM（含演化上下文注入） ----
        context = build_context(sections, icd_params, template_content)
        system_prompt = _build_system_prompt_with_evolution()
        logger.info(
            "draft.generator.context draft_id=%s sections=%d icd_params=%d template_chars=%d context_chars=%d",
            draft_id,
            len(sections),
            len(icd_params),
            len(template_content),
            len(context),
        )
        content_md = self._llm.generate_draft(system_prompt, context, subject)

        # ---- 解析引注 + 回填章节内容 ----
        citations = _parse_citations(content_md)
        _backfill_citation_quotes(citations)

        # ---- 冲突检测 ----
        from harnetics.engine.conflict_detector import ConflictDetector
        conflicts = ConflictDetector().detect(related_doc_ids, icd_params)
        logger.info(
            "draft.generator.result draft_id=%s content_chars=%d citations=%d conflicts=%d",
            draft_id,
            len(content_md),
            len(citations),
            len(conflicts),
        )

        # ---- 自动评估 ----
        draft_dict = {
            "draft_id": draft_id,
            "content_md": content_md,
            "citations": [
                {"source_doc_id": c.source_doc_id, "source_section_id": c.source_section_id,
                 "quote": c.quote, "confidence": c.confidence}
                for c in citations
            ],
            "conflicts": [
                {"doc_a_id": c.doc_a_id, "doc_b_id": c.doc_b_id,
                 "description": c.description, "severity": c.severity}
                for c in conflicts
            ],
            "request": request,
        }
        bus = build_default_bus()
        eval_results = bus.run_all(draft_dict)
        has_blocking = bus.has_blocking_failures(eval_results)
        eval_status = "blocked" if has_blocking else "eval_pass"

        eval_results_payload = [
            {
                "evaluator_id": r.evaluator_id,
                "name": r.name,
                "status": r.status.value,
                "level": _map_eval_level(r),
                "detail": r.detail,
                "locations": r.locations,
            }
            for r in eval_results
        ]

        # ---- 持久化 ----
        request_json = json.dumps(request, ensure_ascii=False)
        citations_json = json.dumps([
            {"source_doc_id": c.source_doc_id, "source_section_id": c.source_section_id,
             "quote": c.quote, "confidence": c.confidence}
            for c in citations
        ], ensure_ascii=False)
        conflicts_json = json.dumps([
            {"doc_a_id": c.doc_a_id, "doc_b_id": c.doc_b_id,
             "description": c.description, "severity": c.severity}
            for c in conflicts
        ], ensure_ascii=False)
        eval_results_json = json.dumps(eval_results_payload, ensure_ascii=False)

        try:
            with store.get_connection() as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO drafts
                       (draft_id, request_json, content_md, citations_json, conflicts_json,
                        eval_results_json, status, generated_by)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (draft_id, request_json, content_md, citations_json, conflicts_json,
                     eval_results_json, eval_status, generated_by),
                )
        except Exception as exc:
            logger.error(
                "draft.generator.persist_failed draft_id=%s generated_by=%s error_type=%s error=%s",
                draft_id,
                generated_by,
                type(exc).__name__,
                exc,
            )
            raise

        logger.info("draft.generator.persisted draft_id=%s generated_by=%s", draft_id, generated_by)

        # ---- 写入进化信号（供 evolver 下次扫描） ----
        try:
            from harnetics.engine.evolution import write_draft_signal
            write_draft_signal(
                draft_id=draft_id,
                subject=subject,
                eval_results=eval_results_payload,
                has_blocking=has_blocking,
                sections_used=len(sections),
                icd_params_used=len(icd_params),
            )
        except Exception:
            pass  # 进化信号写入失败不中断主流程

        return AlignedDraft(
            draft_id=draft_id,
            content_md=content_md,
            citations=citations,
            conflicts=conflicts,
            eval_results_json=eval_results_json,
            status=eval_status,
            generated_by=generated_by,
        )


def _llm_identifier(llm: object) -> str:
    model = getattr(llm, "model", "")
    if isinstance(model, str) and model.strip():
        return model
    return llm.__class__.__name__


def _map_eval_level(result) -> str:
    """将 EvalResult 的 (status, level) 映射为前端展示标签。"""
    from harnetics.evaluators.base import EvalStatus, EvalLevel
    if result.status in (EvalStatus.PASS, EvalStatus.SKIP):
        return "Pass"
    if result.level == EvalLevel.BLOCK:
        return "Blocker"
    return "Warning"


def _parse_citations(content: str) -> list[Citation]:
    seen: set[tuple[str, str]] = set()
    citations: list[Citation] = []
    for m in _CITATION_RE.finditer(content):
        doc_id, sec_id = m.group(1), m.group(2)
        key = (doc_id, sec_id)
        if key not in seen:
            seen.add(key)
            citations.append(Citation(
                source_doc_id=doc_id,
                source_section_id=sec_id,
                quote="",
                confidence=1.0,
            ))
    return citations


def _backfill_citation_quotes(citations: list[Citation]) -> None:
    """从 graph store 查询章节内容，回填 quote 字段（heading + 前 200 字符）。"""
    for cit in citations:
        try:
            sections = store.get_sections(cit.source_doc_id)
            matched = [s for s in sections if s.section_id == cit.source_section_id]
            if matched:
                sec = matched[0]
                heading = sec.heading or ""
                body = (sec.content or "")[:200]
                cit.quote = f"{heading}\n{body}".strip() if heading else body.strip()
            else:
                cit.quote = "原始内容不可用"
        except Exception:
            cit.quote = "原始内容不可用"


def _build_system_prompt_with_evolution() -> str:
    """构建注入了 GEP 演化上下文的 system prompt。

    调用 evolver CLI 获取基于历史信号的 Gene 指导；evolver 未安装时
    回退到原始 DRAFT_SYSTEM_PROMPT，保持零侵入。
    """
    try:
        from harnetics.engine.evolution import get_evolution_context
        evo_context = get_evolution_context()
    except Exception:
        evo_context = ""

    if not evo_context:
        return DRAFT_SYSTEM_PROMPT

    return (
        DRAFT_SYSTEM_PROMPT
        + "\n\n## 🧬 演化上下文（GEP 协议）\n\n"
        + "以下是基于历史草稿质量信号的演化指导，请在生成时参考：\n\n"
        + evo_context
    )
