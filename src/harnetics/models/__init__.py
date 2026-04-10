# [INPUT]: 聚合 document/icd/draft/impact/records 子模块的公共类型
# [OUTPUT]: 对外提供全部领域 dataclass + 旧版 record 类型的统一导入入口
# [POS]: models 包的门面，让消费者写 `from harnetics.models import X` 即可
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

# ---- 新领域模型 ----
from .document import DocumentEdge, DocumentNode, Section
from .draft import AlignedDraft, Citation, Conflict, DraftRequest
from .icd import ICDParameter
from .impact import ImpactedDoc, ImpactReport, SectionDiff

# ---- 旧版 record 类型（repository / importer / drafts 依赖） ----
from .records import (
    CitationRecord,
    DocumentRecord,
    DraftRecord,
    GenerationRunRecord,
    SectionRecord,
    TemplateRecord,
    ValidationIssueRecord,
)

__all__ = [
    # 新领域模型
    "AlignedDraft",
    "Citation",
    "CitationRecord",
    "Conflict",
    "DocumentEdge",
    "DocumentNode",
    "DocumentRecord",
    "DraftRecord",
    "DraftRequest",
    "GenerationRunRecord",
    "ICDParameter",
    "ImpactedDoc",
    "ImpactReport",
    "Section",
    "SectionDiff",
    "SectionRecord",
    "TemplateRecord",
    "ValidationIssueRecord",
]
