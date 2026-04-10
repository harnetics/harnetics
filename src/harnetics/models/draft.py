# [INPUT]: 依赖 dataclasses
# [OUTPUT]: 对外提供 DraftRequest, AlignedDraft, Citation, Conflict
# [POS]: models 包的草稿子域，描述草稿请求、输出、引注与冲突
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class DraftRequest:
    request_json: str
    draft_id: str = ""
    status: str = "pending"


@dataclass(slots=True)
class Citation:
    source_doc_id: str
    source_section_id: str
    quote: str
    confidence: float = 1.0


@dataclass(slots=True)
class Conflict:
    doc_a_id: str
    doc_b_id: str
    section_a_id: str
    section_b_id: str
    description: str
    severity: str = "warning"


@dataclass(slots=True)
class AlignedDraft:
    draft_id: str
    content_md: str
    citations: list[Citation] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    eval_results_json: str = ""
    status: str = "generated"
    generated_by: str = ""
    created_at: str = ""
    reviewed_at: str = ""
