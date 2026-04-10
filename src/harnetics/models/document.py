# [INPUT]: 依赖 dataclasses
# [OUTPUT]: 对外提供 DocumentNode, Section, DocumentEdge
# [POS]: models 包的文档子域，描述文档节点、章节与关系边
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DocumentNode:
    doc_id: str
    title: str
    doc_type: str
    department: str
    system_level: str
    engineering_phase: str
    version: str
    status: str = "draft"
    content_hash: str = ""
    file_path: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass(slots=True)
class Section:
    section_id: str
    doc_id: str
    heading: str
    content: str
    level: int = 1
    order_index: int = 0
    tags: str = ""


@dataclass(slots=True)
class DocumentEdge:
    source_doc_id: str
    source_section_id: str
    target_doc_id: str
    target_section_id: str
    relation: str
    confidence: float = 1.0
    created_by: str = "system"
    edge_id: int | None = None
    created_at: str = ""
