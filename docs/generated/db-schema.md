<!--
[INPUT]: 依赖当前 Repository 实现的 SQLite 表结构
[OUTPUT]: 对外提供当前运行时数据库 schema 与表所有权说明
[POS]: generated/ 的结构化工件入口，记录已落地的持久化边界
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->

# DB Schema

`Repository` 是唯一的 SQLite 边界。当前运行时已经真实使用这些表完成导入、检索辅助、草稿生成、校验与导出工作流。

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

运行时对应关系：
- 导入阶段写入 `documents`、`sections`，模板文档额外写入 `templates`。
- 生成阶段写入 `drafts`、`citations`、`generation_runs`。
- 校验阶段写入 `validation_issues`，并回写 `drafts.status` 为 `ready`、`warning` 或 `blocked`。
- 导出阶段更新 `drafts.exported_at` 并返回 `drafts.content_markdown`，让最终交付有可追踪时间戳。
