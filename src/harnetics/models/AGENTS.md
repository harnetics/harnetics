# harnetics/models/
> L2 | 父级: src/harnetics/AGENTS.md

成员清单
__init__.py: 统一导入入口，聚合新领域模型 + 旧版 record 类型。
document.py: DocumentNode, Section, DocumentEdge — 文档节点与关系边。
icd.py: ICDParameter — ICD 参数条目。
draft.py: DraftRequest, AlignedDraft, Citation, Conflict — 草稿子域。
impact.py: ImpactReport, ImpactedDoc, SectionDiff — 变更影响报告。
records.py: 旧版 DocumentRecord/SectionRecord 等 — repository/importer/drafts 兼容层。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
