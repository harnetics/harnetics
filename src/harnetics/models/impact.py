# [INPUT]: 依赖 dataclasses
# [OUTPUT]: 对外提供 ImpactReport, ImpactedDoc, SectionDiff
# [POS]: models 包的变更影响子域，描述变更波及报告
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SectionDiff:
    section_id: str
    heading: str
    change_type: str
    summary: str = ""


@dataclass(slots=True)
class ImpactedDoc:
    doc_id: str
    title: str
    relation: str
    affected_sections: list[str] = field(default_factory=list)
    severity: str = "info"


@dataclass(slots=True)
class ImpactReport:
    report_id: str
    trigger_doc_id: str
    old_version: str
    new_version: str
    changed_sections: list[SectionDiff] = field(default_factory=list)
    impacted_docs: list[ImpactedDoc] = field(default_factory=list)
    summary: str = ""
    created_at: str = ""
