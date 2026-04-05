<!--
[INPUT]: 依赖当前 Repository 实现的 SQLite 表结构
[OUTPUT]: 对外提供当前运行时数据库 schema 与表所有权说明
[POS]: generated/ 的结构化工件入口，记录已落地的持久化边界
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->

# DB Schema

`Repository` 是唯一的 SQLite 边界，启动时会初始化下列表。

| 表 | 归属记录 | 作用 | 关键约束 |
| --- | --- | --- | --- |
| `documents` | `DocumentRecord` | 文档元数据与版本索引 | `UNIQUE(doc_id, version)` |
| `sections` | `SectionRecord` | 文档分段内容与检索切片 | `document_id -> documents.id ON DELETE CASCADE` |
| `templates` | `TemplateRecord` | 文档模板与结构约束 | `document_id UNIQUE`，`document_id -> documents.id ON DELETE CASCADE` |
| `drafts` | `DraftRecord` | 生成草稿的主体记录 | `exported_at` 可空 |
| `citations` | `CitationRecord` | 草稿到源 section 的引用 | `draft_id -> drafts.id ON DELETE CASCADE`，`section_id -> sections.id ON DELETE CASCADE` |
| `validation_issues` | `ValidationIssueRecord` | 草稿校验问题与来源 | `owner_type` + `owner_id` 定位 owner |
| `generation_runs` | `GenerationRunRecord` | 草稿生成运行日志 | `draft_id -> drafts.id ON DELETE CASCADE` |

字段约定：
- 所有主键都是 `INTEGER PRIMARY KEY AUTOINCREMENT`。
- 所有外键在 `Repository.connect()` 中启用 `PRAGMA foreign_keys = ON`。
- `trace_refs`、`source_refs`、`content_markdown` 这类文本字段直接存储原始字符串，不做二次拆分。
- `selected_document_ids` 以逗号分隔字符串保存，保持生成流程最小可用。
