# [INPUT]: 依赖 llm.client, llm.prompts, graph.store, graph.embeddings, models.draft
# [OUTPUT]: 对外提供 DraftGenerator
# [POS]: engine 包的草稿生成核心，检索→组装→生成→解析引注→冲突检测
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

        # ---- 调用 LLM ----
        context = build_context(sections, icd_params, template_content)
        logger.info(
            "draft.generator.context draft_id=%s sections=%d icd_params=%d template_chars=%d context_chars=%d",
            draft_id,
            len(sections),
            len(icd_params),
            len(template_content),
            len(context),
        )
        content_md = self._llm.generate_draft(DRAFT_SYSTEM_PROMPT, context, subject)

        # ---- 解析引注 ----
        citations = _parse_citations(content_md)

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

        try:
            with store.get_connection() as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO drafts
                       (draft_id, request_json, content_md, citations_json, conflicts_json,
                        eval_results_json, status, generated_by)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (draft_id, request_json, content_md, citations_json, conflicts_json,
                     "[]", "completed", generated_by),
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

        return AlignedDraft(
            draft_id=draft_id,
            content_md=content_md,
            citations=citations,
            conflicts=conflicts,
            status="completed",
            generated_by=generated_by,
        )


def _llm_identifier(llm: object) -> str:
    model = getattr(llm, "model", "")
    if isinstance(model, str) and model.strip():
        return model
    return llm.__class__.__name__


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
