"""
# [INPUT]: 依赖 graph.store (get_document, get_sections, get_edges_for_doc)、models.impact
# [OUTPUT]: 对外提供 ImpactAnalyzer 类，analyze() 返回 ImpactReport
# [POS]: engine 包的影响分析器，BFS 遍历下游依赖图，按深度/关系类型评定危险等级
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""
from __future__ import annotations

import json
import re
import uuid
from collections import deque
from datetime import datetime, timezone

from harnetics.graph import store
from harnetics.models.impact import ImpactReport, ImpactedDoc, SectionDiff

# ---- 关系类型 → 影响传播权重 ----------------------------------------
_HIGH_RISK_RELATIONS = {"constrained_by", "traces_to", "implements", "derived_from"}
_MEDIUM_RISK_RELATIONS = {"references", "supersedes", "allocated_to"}
_TRACE_TOKEN_RE = re.compile(r"\b(?:REQ-[A-Z]+-\d+|ICD-[A-Z]+-\d+|TH1-[A-Z]+-\d+)\b")
_SECTION_REF_RE = re.compile(r"(?:DOC-[A-Z]{3}-\d{3}\s*)?§\s*([0-9]+(?:\.[0-9]+)*)")
_HEADING_REF_RE = re.compile(r"^([0-9]+(?:\.[0-9]+)*)\b")


def _severity(depth: int, relation: str | None) -> str:
    """根据 BFS 深度和关系类型返回危险等级。"""
    if depth == 1 and (relation in _HIGH_RISK_RELATIONS):
        return "critical"
    if depth == 1:
        return "major"
    if depth == 2:
        return "major"
    return "minor"


class ImpactAnalyzer:
    """BFS 遍历下游依赖，评估文档变更波及范围。"""

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
        """
        分析 doc_id 的一次版本变更会影响哪些下游文档。

        Parameters
        ----------
        doc_id:               触发文档 ID
        old_version:          变更前版本号（记录用，不影响计算）
        new_version:          变更后版本号
        changed_section_ids:  明确变更的章节 ID 列表；为空则默认全量章节
        """
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

        impacted_docs = self._bfs_downstream(doc_id, changed_sections_source)

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
        )

        self._persist(report)
        return report

    # ----------------------------------------------------------------
    # 内部方法
    # ----------------------------------------------------------------

    def _bfs_downstream(
        self, start_doc_id: str, changed_sections: list[store.Section]  # type: ignore[attr-defined]
    ) -> list[ImpactedDoc]:
        """BFS 遍历所有依赖 start_doc_id 的下游文档（最大深度 6）。"""
        visited: dict[str, ImpactedDoc] = {}
        queue: deque[tuple[str, int, str, str, list]] = deque()

        # 入队首层下游：谁引用了 start_doc_id，谁就会被它影响。
        upstream, _ = store.get_edges_for_doc(start_doc_id)
        for edge in upstream:
            if edge.source_doc_id == start_doc_id:
                continue
            queue.append(
                (
                    edge.source_doc_id,
                    1,
                    edge.relation or "references",
                    start_doc_id,
                    changed_sections,
                )
            )

        while queue:
            current_doc_id, depth, relation, upstream_doc_id, upstream_sections = queue.popleft()

            if depth > 6:
                continue

            current_doc = store.get_document(current_doc_id)
            if current_doc is None:
                continue

            severity = _severity(depth, relation)
            affected_sections = self._find_affected_sections(
                current_doc_id=current_doc_id,
                upstream_doc_id=upstream_doc_id,
                upstream_sections=upstream_sections,
            )
            should_propagate = self._merge_impacted_doc(
                visited=visited,
                doc_id=current_doc_id,
                title=current_doc.title,
                relation=relation,
                severity=severity,
                affected_sections=affected_sections,
            )

            # 继续向下游传播
            if depth < 6 and should_propagate:
                next_changed_sections = self._select_sections(
                    current_doc_id,
                    affected_sections,
                )
                if not next_changed_sections:
                    next_changed_sections = store.get_sections(current_doc_id)
                next_upstream, _ = store.get_edges_for_doc(current_doc_id)
                for edge in next_upstream:
                    if edge.source_doc_id == current_doc_id:
                        continue
                    queue.append(
                        (
                            edge.source_doc_id,
                            depth + 1,
                            edge.relation or "references",
                            current_doc_id,
                            next_changed_sections,
                        )
                    )

        # 按危险等级降序排列
        return sorted(
            visited.values(),
            key=lambda d: _sev_rank(d.severity),
            reverse=True,
        )

    def _find_affected_sections(
        self,
        current_doc_id: str,
        upstream_doc_id: str,
        upstream_sections: list,
    ) -> list[str]:
        """优先用 section-aware 边，再回退到章节内容信号定位。"""
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

        return sorted(edge_hits)

    def _merge_impacted_doc(
        self,
        *,
        visited: dict[str, ImpactedDoc],
        doc_id: str,
        title: str,
        relation: str,
        severity: str,
        affected_sections: list[str],
    ) -> bool:
        normalized_sections = sorted(set(affected_sections))
        if doc_id not in visited:
            visited[doc_id] = ImpactedDoc(
                doc_id=doc_id,
                title=title,
                relation=relation,
                affected_sections=normalized_sections,
                severity=severity,
            )
            return True

        existing = visited[doc_id]
        previous_sections = set(existing.affected_sections)
        merged_sections = sorted(previous_sections | set(normalized_sections))
        if _sev_rank(severity) > _sev_rank(existing.severity):
            existing.severity = severity
            existing.relation = relation
        changed = merged_sections != existing.affected_sections
        existing.affected_sections = merged_sections
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
        """将影响分析报告序列化后写入 impact_reports 表。"""
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
                    "affected_sections": d.affected_sections,
                    "severity": d.severity,
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
            # 持久化失败不阻断主流程；日志由调用方负责
            pass


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
