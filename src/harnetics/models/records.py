# [INPUT]: 依赖 dataclasses
# [OUTPUT]: 对外提供 Repository 与 services 共用的 record 类型（原 models.py 迁入）
# [POS]: models 包的旧版记录定义，供 repository/importer/drafts 继续引用
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from dataclasses import dataclass


@dataclass(slots=True)
class DocumentRecord:
    id: int | None
    doc_id: str
    title: str
    department: str
    doc_type: str
    system_level: str
    engineering_phase: str
    version: str
    status: str
    source_path: str
    imported_at: str


@dataclass(slots=True)
class SectionRecord:
    id: int | None
    document_id: int
    heading: str
    level: int
    sequence: int
    content: str
    trace_refs: str


@dataclass(slots=True)
class TemplateRecord:
    id: int | None
    document_id: int
    name: str
    required_sections: str
    structure: str


@dataclass(slots=True)
class DraftRecord:
    id: int | None
    topic: str
    department: str
    target_doc_type: str
    target_system_level: str
    status: str
    content_markdown: str
    exported_at: str | None


@dataclass(slots=True)
class CitationRecord:
    id: int | None
    draft_id: int
    draft_anchor: str
    section_id: int
    quote_excerpt: str


@dataclass(slots=True)
class ValidationIssueRecord:
    id: int | None
    owner_type: str
    owner_id: int
    severity: str
    message: str
    source_refs: str


@dataclass(slots=True)
class GenerationRunRecord:
    id: int | None
    draft_id: int
    selected_document_ids: str
    selected_template_id: int
    status: str
    duration_ms: int
    input_summary: str


__all__ = [
    "CitationRecord",
    "DocumentRecord",
    "DraftRecord",
    "GenerationRunRecord",
    "SectionRecord",
    "TemplateRecord",
    "ValidationIssueRecord",
]
