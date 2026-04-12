# Data Model: 草稿工作台增强

**Feature**: 006-draft-workbench-enhancement
**Date**: 2026-04-12

## Existing Entities (无 schema 变更)

### Draft (drafts 表)
| 字段 | 类型 | 说明 |
|------|------|------|
| draft_id | TEXT PK | DRAFT-YYYYMMDDHHMMSS-HEXHEX |
| request_json | TEXT | 完整请求 dict JSON，含 subject 字段 |
| content_md | TEXT | 生成的 Markdown 正文 |
| citations_json | TEXT | Citation[] JSON |
| conflicts_json | TEXT | Conflict[] JSON |
| eval_results_json | TEXT | EvalResult[] JSON（本次改为生成时自动填充）|
| status | TEXT | "completed" / "blocked" / "eval_pass" |
| generated_by | TEXT | LLM 模型标识 |
| created_at | TEXT | ISO 时间戳 |
| reviewed_at | TEXT | 可选审查时间 |

### Citation (嵌入 citations_json)
| 字段 | 类型 | 说明 |
|------|------|------|
| source_doc_id | str | 引用文档 ID |
| source_section_id | str | 引用章节 ID |
| quote | str | **本次修改**: 回填章节 heading + 内容前 200 字符 |
| confidence | float | 置信度 (默认 1.0) |

### EvalResult (嵌入 eval_results_json)
| 字段 | 类型 | 说明 |
|------|------|------|
| evaluator_id | str | EA.1, EB.1 等 |
| name | str | 评估器名称 |
| status | str | pass / fail / warn / skip |
| level | str | **本次修改**: 映射后的展示标签 "Pass" / "Warning" / "Blocker" |
| detail | str | 详细说明 |
| locations | str[] | 问题位置 |

## New Frontend Types

### DraftSummary (扩展)
```typescript
interface DraftSummary {
  draft_id: string
  status: string
  generated_by: string
  created_at: string
  subject: string           // 新增: 从 request_json 提取
  eval_summary: {           // 新增: 评估结果统计
    pass: number
    warn: number
    block: number
  } | null
}
```

## 注意事项

- 无 SQLite schema 变更，所有扩展通过 JSON 字段内部结构和查询时计算实现
- eval_results_json 中的 level 字段从后端 EvalLevel (block/warn) 映射为前端标签 (Pass/Warning/Blocker)
- quote 字段从空字符串变为实际内容摘要，兼容已有空值草稿
