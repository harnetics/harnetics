"""
# [INPUT]: 依赖 config.get_settings、llm.client.HarneticsLLM、models.document.Section、chromadb（临时集合）、sentence-transformers、comparison_analyzer 的报告辅助
# [OUTPUT]: 对外提供 Comparison4StepEngine 类，analyze_4step_streaming() 生成器，yield 四步 SSE 事件与最终 Markdown 报告
# [POS]: engine 包的四步比对引擎，与 comparison_analyzer 并列，通过向量预筛选与全局校验提升审查精准度
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""

from __future__ import annotations

import json
import logging
from typing import Generator

from harnetics.llm.client import HarneticsLLM
from harnetics.models.document import Section
from harnetics.engine.comparison_4step_support import (
    _LOCAL_EMBED_MODEL,
    _STEP1_SYSTEM_PROMPT,
    _STEP1_USER_REQUEST,
    _STEP3_SYSTEM_PROMPT,
    _STEP4_SYSTEM_PROMPT,
    _VECTOR_TOP_K,
    align_batch_findings,
    build_4step_analysis_md,
    build_step3_request,
    coerce_compliance_rate,
    fallback_requirements,
    keyword_fallback_match,
    parse_json_array,
    parse_json_object,
    render_sections,
    text,
    validate_scanned_requirements,
)

logger = logging.getLogger("harnetics.comparison_4step")


class Comparison4StepEngine:
    """四步比对引擎：需求扫描 → 向量匹配 → 批评估 → 全局校验。

    每步通过 analyze_4step_streaming() 生成器 yield SSE 事件 dict。
    """

    def __init__(
        self,
        llm: HarneticsLLM | None = None,
        embedding_model: str = "",
        embedding_api_key: str = "",
        embedding_base_url: str = "",
    ) -> None:
        self._llm = llm or HarneticsLLM()
        self._embedding_model = embedding_model
        self._embedding_api_key = embedding_api_key
        self._embedding_base_url = embedding_base_url

    # ------------------------------------------------------------------
    # 主生成器
    # ------------------------------------------------------------------

    def analyze_4step_streaming(
        self,
        session_id: str,
        req_sections: list[Section],
        resp_sections: list[Section],
        req_filename: str,
        resp_filename: str,
    ) -> Generator[dict, None, None]:
        """四步流水线生成器，yield SSE 事件 dict。

        事件类型：
          step_started      — 步骤开始
          scanning_done     — 步骤1完成，含需求列表
          matching_progress — 步骤2进度
          finding_batch     — 步骤3每批结果
          review_done       — 步骤4完成
          completed         — 全部完成
          error             — 错误
        """
        all_findings: list[dict] = []

        # ---- Step 1: 需求扫描 ----
        yield {"type": "step_started", "step": 1, "label": "识别需求条款"}
        requirements = self._step1_scan_requirements(req_sections)

        logger.info(
            "4step.step1_done session_id=%s requirements=%d",
            session_id, len(requirements),
        )
        yield {
            "type": "scanning_done",
            "step": 1,
            "total_requirements": len(requirements),
            "requirements": requirements,
        }

        # ---- Step 2: 向量匹配 ----
        yield {"type": "step_started", "step": 2, "label": "向量匹配应答章节"}
        matches: dict[int, list[dict]] = {}
        total_req = len(requirements)

        for idx, req in enumerate(requirements):
            candidates = self._step2_match_one(req, resp_sections)
            matches[idx] = candidates
            if (idx + 1) % 5 == 0 or idx == total_req - 1:
                yield {
                    "type": "matching_progress",
                    "step": 2,
                    "matched": idx + 1,
                    "total": total_req,
                }

        logger.info("4step.step2_done session_id=%s matched=%d", session_id, len(matches))

        # ---- Step 3: LLM 逐项评估 ----
        yield {"type": "step_started", "step": 3, "label": "LLM 逐项评估覆盖度"}
        evaluated = 0

        for batch_findings in self._step3_evaluate_batched(requirements, matches, resp_sections):
            start_index = len(all_findings) + 1
            for offset, finding in enumerate(batch_findings, start=start_index):
                finding["finding_id"] = f"F{offset:03d}"
            all_findings.extend(batch_findings)
            evaluated += len(batch_findings)
            yield {
                "type": "finding_batch",
                "step": 3,
                "findings": batch_findings,
                "evaluated": evaluated,
                "total": total_req,
            }

        logger.info(
            "4step.step3_done session_id=%s findings=%d",
            session_id, len(all_findings),
        )

        # ---- Step 4: 全局校验 ----
        yield {"type": "step_started", "step": 4, "label": "全局校验"}
        try:
            global_result = self._step4_global_review(all_findings)
        except Exception as exc:  # noqa: BLE001
            logger.warning("4step.step4_error session_id=%s exc=%s", session_id, exc)
            global_result = {
                "compliance_rate": self._calc_compliance_rate(all_findings),
                "summary": "全局校验步骤发生异常，以自动计算结果替代。",
                "corrections": [],
            }

        compliance_rate = coerce_compliance_rate(
            global_result.get("compliance_rate"), all_findings, self._calc_compliance_rate
        )
        summary = text(global_result.get("summary"))
        raw_corrections = global_result.get("corrections", [])
        corrections = raw_corrections if isinstance(raw_corrections, list) else []
        yield {
            "type": "review_done",
            "step": 4,
            "compliance_rate": compliance_rate,
            "summary": summary,
            "corrections": corrections,
        }

        analysis_md = build_4step_analysis_md(
            all_findings, req_filename, resp_filename, compliance_rate, summary, corrections
        )

        yield {
            "type": "completed",
            "session_id": session_id,
            "total_findings": len(all_findings),
            "findings": all_findings,
            "analysis_md": analysis_md,
            "compliance_rate": compliance_rate,
            "summary": summary,
            "corrections": corrections,
        }

    # ------------------------------------------------------------------
    # Step 1 — 需求扫描
    # ------------------------------------------------------------------

    def _step1_scan_requirements(self, req_sections: list[Section]) -> list[dict]:
        """LLM 解析审查大纲，返回结构化需求列表。JSON 失败时降级为 heading 列表。"""
        from harnetics.config import get_settings

        settings = get_settings()
        req_text = render_sections(req_sections, max_chars=200_000)
        try:
            raw = self._llm.generate_draft(
                system_prompt=_STEP1_SYSTEM_PROMPT,
                context=f"## 【审查大纲】\n\n{req_text}",
                user_request=_STEP1_USER_REQUEST,
                max_tokens=settings.comparison_step1_max_tokens,
            )
            parsed = validate_scanned_requirements(parse_json_array(raw), req_sections)
            if parsed:
                logger.info("4step.step1_llm_ok requirements=%d", len(parsed))
                return parsed
        except Exception as exc:  # noqa: BLE001
            logger.warning("4step.step1_llm_error exc=%s", exc)

        # 降级：直接用章节 heading 列表
        logger.info("4step.step1_fallback req_sections=%d", len(req_sections))
        return fallback_requirements(req_sections)

    # ------------------------------------------------------------------
    # Step 2 — 向量匹配（单条需求）
    # ------------------------------------------------------------------

    def _step2_match_one(self, requirement: dict, resp_sections: list[Section]) -> list[dict]:
        """为单条需求检索最相关应答章节，失败时降级关键词匹配。"""
        try:
            return self._vector_search(requirement, resp_sections)
        except Exception as exc:  # noqa: BLE001
            logger.warning("4step.step2_vector_error exc=%s falling_back=True", exc)
            return keyword_fallback_match(requirement, resp_sections)

    def _vector_search(self, requirement: dict, resp_sections: list[Section]) -> list[dict]:
        """使用 ChromaDB EphemeralClient 做向量检索。

        按请求懒初始化临时集合（同一引擎实例复用，节省重复建索引开销）。
        """
        collection = self._get_or_build_temp_collection(resp_sections)
        query = str(requirement.get("content") or requirement.get("heading") or "")
        if not query:
            return []

        results = collection.query(query_texts=[query], n_results=min(_VECTOR_TOP_K, max(1, collection.count())))
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        candidates: list[dict] = []
        for doc, meta, dist in zip(docs, metas, dists):
            candidates.append({
                "section_id": str(meta.get("section_id", "")),
                "heading": str(meta.get("heading", "")),
                "text": str(doc)[:500],
                "distance": float(dist),
            })
        return candidates

    def _get_or_build_temp_collection(self, resp_sections: list[Section]):
        """懒初始化临时 ChromaDB 集合（按引擎实例缓存，避免重复建索引）。"""
        if hasattr(self, "_temp_collection"):
            return self._temp_collection  # type: ignore[attr-defined]

        import chromadb  # noqa: PLC0415

        client = chromadb.EphemeralClient()

        # 选择 embedding function
        ef = self._build_embedding_function()

        collection = client.get_or_create_collection("temp_resp_016", embedding_function=ef)

        # 批量 upsert 应答章节
        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict] = []
        for sec in resp_sections:
            if not sec.content.strip():
                continue
            ids.append(sec.section_id)
            documents.append(f"{sec.heading}\n{sec.content}"[:2000])
            metadatas.append({
                "section_id": sec.section_id,
                "heading": sec.heading,
                "order_index": sec.order_index,
            })

        if ids:
            # ChromaDB upsert 每批不超过 5461 条
            batch_size = 500
            for i in range(0, len(ids), batch_size):
                collection.upsert(
                    ids=ids[i : i + batch_size],
                    documents=documents[i : i + batch_size],
                    metadatas=metadatas[i : i + batch_size],
                )
            logger.info("4step.temp_collection_built sections=%d", len(ids))

        self._temp_collection = collection  # type: ignore[attr-defined]
        return collection

    def _build_embedding_function(self):
        """根据配置选择本地或云端 embedding function。"""
        model = self._embedding_model.strip()
        api_key = self._embedding_api_key.strip()
        base_url = self._embedding_base_url.strip()

        if model and (api_key or base_url):
            # 云端 OpenAI-compatible embedding
            from harnetics.graph.embeddings import _OpenAICompatibleEmbeddingFunction  # noqa: PLC0415
            logger.info("4step.embedding=remote model=%s", model)
            return _OpenAICompatibleEmbeddingFunction(model=model, api_key=api_key, base_url=base_url)

        # 本地 sentence-transformers
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction  # noqa: PLC0415
        logger.info("4step.embedding=local model=%s", _LOCAL_EMBED_MODEL)
        return SentenceTransformerEmbeddingFunction(model_name=_LOCAL_EMBED_MODEL)

    # ------------------------------------------------------------------
    # Step 3 — LLM 批评估
    # ------------------------------------------------------------------

    def _step3_evaluate_batched(
        self,
        requirements: list[dict],
        matches: dict[int, list[dict]],
        resp_sections: list[Section],
    ) -> Generator[list[dict], None, None]:
        """按配置批大小打包需求做 LLM 评估，yield 本批 findings。"""
        from harnetics.config import get_settings

        batch_size = get_settings().comparison_4step_batch_size
        for batch_start in range(0, len(requirements), batch_size):
            batch_reqs = requirements[batch_start : batch_start + batch_size]
            batch_matches = {
                i: matches.get(batch_start + i, [])
                for i in range(len(batch_reqs))
            }
            try:
                batch_findings = self._evaluate_one_batch(batch_reqs, batch_matches)
                if not batch_findings:
                    batch_findings = [self._placeholder_finding(req) for req in batch_reqs]
            except Exception as exc:  # noqa: BLE001
                logger.warning("4step.step3_batch_error batch_start=%d exc=%s", batch_start, exc)
                batch_findings = [self._placeholder_finding(req) for req in batch_reqs]
            aligned, missing_filled, extra_ignored = align_batch_findings(
                batch_reqs, batch_findings, self._placeholder_finding
            )
            if missing_filled or extra_ignored:
                logger.warning(
                    "4step.step3_batch_aligned batch_start=%d missing_filled=%d extra_ignored=%d",
                    batch_start, missing_filled, extra_ignored,
                )
            yield aligned

    def _evaluate_one_batch(
        self,
        batch_reqs: list[dict],
        batch_matches: dict[int, list[dict]],
    ) -> list[dict]:
        """构造单批 LLM 评估请求，解析结果；必要时自动重试。"""
        # 构建上下文：逐条需求 + 其 top-k 候选章节
        parts: list[str] = []
        for i, req in enumerate(batch_reqs):
            candidates = batch_matches.get(i, [])
            cand_text = ""
            for j, cand in enumerate(candidates, start=1):
                cand_text += f"  候选章节{j}「{cand.get('heading', '')}」：{cand.get('text', '')[:300]}\n"
            parts.append(
                f"【需求 {req.get('id', f'R{i+1}')}】{req.get('heading', '')}\n"
                f"需求内容：{req.get('content', '')[:200]}\n"
                f"所在位置：{req.get('section_ref', '')}\n"
                f"候选应答章节：\n{cand_text or '（未找到候选章节）'}\n"
            )
        context = "\n".join(parts)
        expected = len(batch_reqs)
        max_tokens = max(4096, min(16_384, expected * 700))

        for attempt in range(1, 4):
            raw = self._llm.generate_draft(
                system_prompt=_STEP3_SYSTEM_PROMPT,
                context=context,
                user_request=build_step3_request(batch_reqs, attempt),
                max_tokens=max_tokens,
            )
            parsed = parse_json_array(raw)
            aligned, missing_filled, extra_ignored = align_batch_findings(
                batch_reqs, parsed, self._placeholder_finding
            )
            if missing_filled == 0 and extra_ignored == 0 and len(aligned) == expected:
                return aligned
            logger.warning(
                "4step.step3_retry attempt=%d expected=%d parsed=%d missing=%d extra=%d raw_head=%r",
                attempt,
                expected,
                len(parsed),
                missing_filled,
                extra_ignored,
                raw[:200],
            )
        return []

    @staticmethod
    def _placeholder_finding(req: dict) -> dict:
        """为单条需求生成 unclear 占位 finding。"""
        return {
            "requirement_id": req.get("id", ""),
            "chapter": req.get("section_ref", req.get("heading", "")),
            "requirement_heading": req.get("heading", ""),
            "requirement_content": str(req.get("content", ""))[:100],
            "status": "unclear",
            "detail": "评估步骤异常，此条需人工复核。",
            "requirement_ref": req.get("section_ref", ""),
            "response_ref": "未评估",
            "_step3_placeholder": True,
        }

    # ------------------------------------------------------------------
    # Step 4 — 全局校验
    # ------------------------------------------------------------------

    def _step4_global_review(self, findings: list[dict]) -> dict:
        """LLM 基于 findings 摘要做全局评估。"""
        from harnetics.config import get_settings

        settings = get_settings()
        # 只传 heading+status 摘要，避免超出上下文
        summary_lines = [
            f"{f.get('finding_id', '')} {f.get('requirement_heading', '')} → {f.get('status', '')}"
            for f in findings
        ]
        summary_text = "\n".join(summary_lines[:300])  # 最多300条

        covered = sum(1 for f in findings if f.get("status") == "covered")
        partial = sum(1 for f in findings if f.get("status") == "partial")
        missing = sum(1 for f in findings if f.get("status") == "missing")
        unclear = sum(1 for f in findings if f.get("status") == "unclear")

        context = (
            f"审查大纲需求总数：{len(findings)}\n"
            f"已覆盖：{covered}，部分覆盖：{partial}，未覆盖：{missing}，待明确：{unclear}\n\n"
            f"逐条审查结果摘要：\n{summary_text}"
        )
        user_request = "请基于上述审查结果做全局评估，输出 JSON 对象："

        raw = self._llm.generate_draft(
            system_prompt=_STEP4_SYSTEM_PROMPT,
            context=context,
            user_request=user_request,
            max_tokens=settings.comparison_step4_max_tokens,
        )
        result = parse_json_object(raw)
        if not result:
            result = {
                "compliance_rate": self._calc_compliance_rate(findings),
                "summary": f"自动计算：{covered}项已覆盖，{partial}项部分覆盖，{missing}项未覆盖，{unclear}项待明确。",
                "corrections": [],
            }
        return result

    @staticmethod
    def _calc_compliance_rate(findings: list[dict]) -> float:
        """按 covered=1.0, partial=0.5, missing/unclear=0.0 计算符合性比率。"""
        if not findings:
            return 0.0
        score = sum(
            1.0 if f.get("status") == "covered" else
            0.5 if f.get("status") == "partial" else 0.0
            for f in findings
        )
        return round(score / len(findings), 4)
