"""
# [INPUT]: 依赖 graph.store、graph.embeddings.EmbeddingStore、llm.client.HarneticsLLM、models.impact
# [OUTPUT]: 对外提供 ImpactAnalyzer 类，analyze() 返回 ImpactReport (heuristic / ai_vector 双模式)
# [POS]: engine 包的影响分析器，BFS 遍历下游依赖图，支持 AI 向量粗筛 + LLM 精判
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""
from __future__ import annotations

import json
import re
import uuid
from collections import deque
from datetime import datetime, timezone

from harnetics.graph import store
from harnetics.models.impact import AffectedSection, ImpactReport, ImpactedDoc, SectionDiff

# ---- 关系类型 → 影响传播权重 ----------------------------------------
_HIGH_RISK_RELATIONS = {"constrained_by", "traces_to", "implements", "derived_from"}
_MEDIUM_RISK_RELATIONS = {"references", "supersedes", "allocated_to"}
_TRACE_TOKEN_RE = re.compile(r"\b(?:REQ-[A-Z]+-\d+|ICD-[A-Z]+-\d+|TH1-[A-Z]+-\d+)\b")
_SECTION_REF_RE = re.compile(r"(?:DOC-[A-Z]{3}-\d{3}\s*)?§\s*([0-9]+(?:\.[0-9]+)*)")
_HEADING_REF_RE = re.compile(r"^([0-9]+(?:\.[0-9]+)*)\b")

# ---- AI 向量分析阈值 ------------------------------------------------
_VECTOR_SIMILARITY_THRESHOLD = 0.65
_MAX_LLM_CANDIDATES = 15

# ---- LLM 精判 prompt ------------------------------------------------
_JUDGE_SYSTEM = (
    "你是航天领域文档影响分析专家。给定一段变更内容和一个候选章节，"
    "判断候选章节是否受变更内容影响。仅输出 JSON: "
    '{\"affected\": true/false, \"reason\": \"一句话理由\"}'
)


def _severity(depth: int, relation: str | None) -> str:
    if depth == 1 and (relation in _HIGH_RISK_RELATIONS):
        return "critical"
    if depth == 1:
        return "major"
    if depth == 2:
        return "major"
    return "minor"


class ImpactAnalyzer:
    """BFS 遍历下游依赖，评估文档变更波及范围。支持 AI 向量分析与 heuristic 降级。"""

    def __init__(
        self,
        embedding_store=None,
        llm=None,
    ) -> None:
        self._emb = embedding_store
        self._llm = llm

    @property
    def _ai_available(self) -> bool:
        return self._emb is not None

    # ----------------------------------------------------------------
    # 公共接口
    # ----------------------------------------------------------------

    def analyze(
        self,
        doc_id: str,
        old_version: str = "",
        new_version: str = "",
        changed_section_ids: list[str] | None = None,
    ) -> ImpactReport:
        doc = store.get_document(doc_id)
        if doc is None:
            raise ValueError(f"document not found: {doc_id}")

        sections = store.get_sections(doc_id)
        requested_changed_ids = set(changed_section_ids or [])
        changed_sections_source = [s for s in sections if s.section_id in requested_changed_ids]
        if not changed_sections_source:
            changed_sections_source = sections

        changed_sections = [
            SectionDiff(
                section_id=s.section_id,
                heading=s.heading,
                change_type="modified",
                summary=f"章节 '{s.heading}' 发生变更",
            )
            for s in changed_sections_source
        ]

        analysis_mode = "ai_vector" if self._ai_available else "heuristic"
        impacted_docs = self._bfs_downstream(doc_id, changed_sections_source, analysis_mode)

        summary_lines = [
            f"文档 {doc_id}（{doc.title}）从版本 {old_version} → {new_version}",
            f"变更章节：{len(changed_sections)} 个，影响下游文档：{len(impacted_docs)} 个",
        ]
        critical = [d for d in impacted_docs if d.severity == "critical"]
        major = [d for d in impacted_docs if d.severity == "major"]
        minor = [d for d in impacted_docs if d.severity == "minor"]
        if impacted_docs:
            summary_lines.append(
                f"影响等级分布：critical {len(critical)} / major {len(major)} / minor {len(minor)}"
            )
        else:
            summary_lines.append(
                "未发现依赖该文档的下游文档；当前图谱中没有任何文档把它作为引用目标。"
            )
        if critical:
            summary_lines.append(
                "高危影响：" + "、".join(d.doc_id for d in critical)
            )

        report_id = str(uuid.uuid4())
        report = ImpactReport(
            report_id=report_id,
            trigger_doc_id=doc_id,
            old_version=old_version,
            new_version=new_version,
            changed_sections=changed_sections,
            impacted_docs=impacted_docs,
            summary="\n".join(summary_lines),
            created_at=datetime.now(timezone.utc).isoformat(),
            analysis_mode=analysis_mode,
        )

        self._persist(report)
        return report

    # ----------------------------------------------------------------
    # BFS 遍历
    # ----------------------------------------------------------------

    def _bfs_downstream(
        self, start_doc_id: str, changed_sections: list, analysis_mode: str,
    ) -> list[ImpactedDoc]:
        visited: dict[str, ImpactedDoc] = {}
        queue: deque[tuple[str, int, str, str, list]] = deque()

        upstream, _ = store.get_edges_for_doc(start_doc_id)
        for edge in upstream:
            if edge.source_doc_id == start_doc_id:
                continue
            queue.append(
                (edge.source_doc_id, 1, edge.relation or "references", start_doc_id, changed_sections)
            )

        while queue:
            current_doc_id, depth, relation, upstream_doc_id, upstream_sections = queue.popleft()
            if depth > 6:
                continue

            current_doc = store.get_document(current_doc_id)
            if current_doc is None:
                continue

            severity = _severity(depth, relation)

            if analysis_mode == "ai_vector":
                affected_sections = self._ai_find_affected_sections(
                    current_doc_id, upstream_sections,
                )
                if not affected_sections:
                    affected_sections = self._heuristic_find_affected_sections(
                        current_doc_id,
                        upstream_doc_id,
                        upstream_sections,
                    )
            else:
                affected_sections = self._heuristic_find_affected_sections(
                    current_doc_id, upstream_doc_id, upstream_sections,
                )

            should_propagate = self._merge_impacted_doc(
                visited=visited,
                doc_id=current_doc_id,
                title=current_doc.title,
                relation=relation,
                severity=severity,
                affected_sections=affected_sections,
                analysis_mode=analysis_mode,
            )

            if depth < 6 and should_propagate:
                section_ids = [a.section_id for a in affected_sections]
                next_changed_sections = self._select_sections(current_doc_id, section_ids)
                if not next_changed_sections:
                    next_changed_sections = store.get_sections(current_doc_id)
                next_upstream, _ = store.get_edges_for_doc(current_doc_id)
                for edge in next_upstream:
                    if edge.source_doc_id == current_doc_id:
                        continue
                    queue.append(
                        (edge.source_doc_id, depth + 1, edge.relation or "references",
                         current_doc_id, next_changed_sections)
                    )

        return sorted(
            visited.values(),
            key=lambda d: _sev_rank(d.severity),
            reverse=True,
        )

    # ----------------------------------------------------------------
    # AI 向量分析路径
    # ----------------------------------------------------------------

    def _ai_find_affected_sections(
        self,
        current_doc_id: str,
        upstream_sections: list,
    ) -> list[AffectedSection]:
        """向量粗筛 + LLM 精判，返回真正受影响的章节。"""
        change_text = "\n".join(
            _section_text(s.heading, s.content) for s in upstream_sections
        )
        if not change_text.strip():
            return []

        # ---- 向量粗筛：查找 current_doc 中与 change_text 相似的章节 ----
        all_hits = self._emb.search_similar(
            query=change_text,
            top_k=_MAX_LLM_CANDIDATES * 2,
            filters={"doc_id": current_doc_id},
        )

        candidates: list[dict] = []
        for hit in all_hits:
            distance = hit.get("distance", 999.0)
            score = max(0.0, 1.0 - distance)
            if score >= _VECTOR_SIMILARITY_THRESHOLD:
                candidates.append(hit)
        candidates = candidates[:_MAX_LLM_CANDIDATES]

        if not candidates:
            return []

        # ---- LLM 精判 ----
        if self._llm is None:
            return [
                AffectedSection(
                    section_id=c["section_id"],
                    heading=c.get("heading", ""),
                    reason="向量相似度匹配（无 LLM 精判）",
                )
                for c in candidates
            ]

        results: list[AffectedSection] = []
        for candidate in candidates:
            candidate_text = candidate.get("text", "")[:800]
            user_msg = (
                f"## 变更内容\n{change_text[:1500]}\n\n"
                f"## 候选章节\n{candidate_text}"
            )
            try:
                raw = self._llm.generate_draft(
                    system_prompt=_JUDGE_SYSTEM,
                    context="",
                    user_request=user_msg,
                )
                verdict = _parse_judge_response(raw)
                if verdict.get("affected"):
                    results.append(AffectedSection(
                        section_id=candidate["section_id"],
                        heading=candidate.get("heading", ""),
                        reason=verdict.get("reason", "AI 判定受影响"),
                    ))
            except Exception:
                results.append(AffectedSection(
                    section_id=candidate["section_id"],
                    heading=candidate.get("heading", ""),
                    reason="向量相似度匹配（LLM 调用失败）",
                ))
        return results

    # ----------------------------------------------------------------
    # Heuristic 降级路径 (原有逻辑)
    # ----------------------------------------------------------------

    def _heuristic_find_affected_sections(
        self,
        current_doc_id: str,
        upstream_doc_id: str,
        upstream_sections: list,
    ) -> list[AffectedSection]:
        upstream_section_ids = {section.section_id for section in upstream_sections}
        whole_doc_change = self._covers_whole_doc(upstream_doc_id, upstream_section_ids)
        edge_hits: set[str] = set()
        needs_fallback = False

        with store.get_connection() as conn:
            rows = conn.execute(
                """SELECT source_section_id, target_section_id
                   FROM edges
                   WHERE source_doc_id = ? AND target_doc_id = ?""",
                (current_doc_id, upstream_doc_id),
            ).fetchall()

        for row in rows:
            source_section_id = row["source_section_id"] or ""
            target_section_id = row["target_section_id"] or ""
            if source_section_id and target_section_id and target_section_id in upstream_section_ids:
                edge_hits.add(source_section_id)
                continue
            if source_section_id and not target_section_id and whole_doc_change:
                edge_hits.add(source_section_id)
                needs_fallback = True
                continue
            needs_fallback = True

        if not rows:
            needs_fallback = True

        heuristic_hits = self._find_affected_sections_by_signals(
            current_doc_id=current_doc_id,
            upstream_doc_id=upstream_doc_id,
            upstream_sections=upstream_sections,
            whole_doc_change=whole_doc_change,
        )
        if needs_fallback:
            edge_hits.update(heuristic_hits)

        section_map = {s.section_id: s for s in store.get_sections(current_doc_id)}
        return [
            AffectedSection(
                section_id=sid,
                heading=section_map[sid].heading if sid in section_map else "",
                reason="规则引擎匹配",
            )
            for sid in sorted(edge_hits)
        ]

    # ----------------------------------------------------------------
    # 辅助方法
    # ----------------------------------------------------------------

    def _merge_impacted_doc(
        self,
        *,
        visited: dict[str, ImpactedDoc],
        doc_id: str,
        title: str,
        relation: str,
        severity: str,
        affected_sections: list[AffectedSection],
        analysis_mode: str = "heuristic",
    ) -> bool:
        if doc_id not in visited:
            visited[doc_id] = ImpactedDoc(
                doc_id=doc_id,
                title=title,
                relation=relation,
                affected_sections=list(affected_sections),
                severity=severity,
                analysis_mode=analysis_mode,
            )
            return True

        existing = visited[doc_id]
        existing_ids = {a.section_id for a in existing.affected_sections}
        new_items = [a for a in affected_sections if a.section_id not in existing_ids]
        if _sev_rank(severity) > _sev_rank(existing.severity):
            existing.severity = severity
            existing.relation = relation
        changed = bool(new_items)
        existing.affected_sections.extend(new_items)
        existing.affected_sections.sort(key=lambda a: a.section_id)
        return changed

    def _select_sections(self, doc_id: str, section_ids: list[str]) -> list:
        sections = store.get_sections(doc_id)
        selected_ids = set(section_ids)
        if not selected_ids:
            return []
        return [section for section in sections if section.section_id in selected_ids]

    def _covers_whole_doc(self, doc_id: str, section_ids: set[str]) -> bool:
        if not section_ids:
            return False
        all_sections = {section.section_id for section in store.get_sections(doc_id)}
        return bool(all_sections) and section_ids == all_sections

    def _find_affected_sections_by_signals(
        self,
        *,
        current_doc_id: str,
        upstream_doc_id: str,
        upstream_sections: list,
        whole_doc_change: bool,
    ) -> set[str]:
        upstream_tokens: set[str] = set()
        upstream_section_refs: set[str] = set()
        for section in upstream_sections:
            text = _section_text(section.heading, section.content)
            upstream_tokens.update(_extract_trace_tokens(text))
            upstream_section_refs.update(_extract_section_refs(text))

        affected: set[str] = set()
        for section in store.get_sections(current_doc_id):
            text = _section_text(section.heading, section.content)
            section_tokens = _extract_trace_tokens(text)
            section_refs = _extract_section_refs(text)
            mentions_doc = upstream_doc_id in text

            strong_match = bool((section_tokens & upstream_tokens) or (section_refs & upstream_section_refs))
            if strong_match:
                affected.add(section.section_id)
                continue
            if whole_doc_change and mentions_doc:
                affected.add(section.section_id)

        return affected

    def _persist(self, report: ImpactReport) -> None:
        changed_json = json.dumps(
            [
                {
                    "section_id": s.section_id,
                    "heading": s.heading,
                    "change_type": s.change_type,
                    "summary": s.summary,
                }
                for s in report.changed_sections
            ],
            ensure_ascii=False,
        )
        impacted_json = json.dumps(
            [
                {
                    "doc_id": d.doc_id,
                    "title": d.title,
                    "relation": d.relation,
                    "affected_sections": [
                        {"section_id": a.section_id, "heading": a.heading, "reason": a.reason}
                        for a in d.affected_sections
                    ],
                    "severity": d.severity,
                    "analysis_mode": d.analysis_mode,
                }
                for d in report.impacted_docs
            ],
            ensure_ascii=False,
        )
        try:
            with store.get_connection() as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO impact_reports
                       (report_id, trigger_doc_id, old_version, new_version,
                        changed_sections_json, impacted_docs_json, summary, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        report.report_id,
                        report.trigger_doc_id,
                        report.old_version,
                        report.new_version,
                        changed_json,
                        impacted_json,
                        report.summary,
                        report.created_at,
                    ),
                )
        except Exception:
            pass


def _parse_judge_response(raw: str) -> dict:
    """从 LLM 返回文本中提取 JSON verdict。"""
    raw = raw.strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            pass
    return {"affected": False, "reason": ""}


def _sev_rank(severity: str) -> int:
    return {"critical": 3, "major": 2, "minor": 1, "info": 0}.get(severity, 0)


def _section_text(heading: str, content: str) -> str:
    return "\n".join(part for part in (heading, content) if part)


def _extract_trace_tokens(text: str) -> set[str]:
    return {match.group(0) for match in _TRACE_TOKEN_RE.finditer(text)}


def _extract_section_refs(text: str) -> set[str]:
    refs = {match.group(1) for match in _SECTION_REF_RE.finditer(text)}
    heading_ref = _extract_heading_ref(text.strip())
    if heading_ref:
        refs.add(heading_ref)
    return refs


def _extract_heading_ref(text: str) -> str | None:
    match = _HEADING_REF_RE.match(text)
    return match.group(1) if match else None
