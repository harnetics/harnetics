# API Contracts: 草稿工作台增强

**Feature**: 006-draft-workbench-enhancement
**Date**: 2026-04-12

## POST /api/draft/generate

### Request (不变)
```json
{
  "subject": "string",
  "related_doc_ids": ["string"],
  "template_id": "string",
  "source_report_id": "string",
  "extra": {}
}
```

### Response (扩展)
```json
{
  "draft_id": "DRAFT-20260412...",
  "status": "completed | blocked | eval_pass",
  "content_md": "# Markdown content...",
  "citations": [
    {
      "source_doc_id": "DOC-FMA-001",
      "source_section_id": "sec-1",
      "quote": "§1. 变更影响概述\n本节概要说明 DOC-FMA-001 v1.4 变更...",
      "confidence": 1.0
    }
  ],
  "conflicts": [...],
  "eval_results": [
    {
      "evaluator_id": "EA.1",
      "name": "CitationCompleteness",
      "status": "pass",
      "level": "Pass",
      "detail": "All technical paragraphs have citation markers",
      "locations": []
    },
    {
      "evaluator_id": "EA.2",
      "name": "CitationReality",
      "status": "fail",
      "level": "Blocker",
      "detail": "Cited DOC-XXX-999 not found in graph store",
      "locations": ["paragraph 3"]
    }
  ],
  "generated_by": "openai/claude-sonnet-4-6",
  "created_at": "2026-04-12T07:26:04Z"
}
```

**变更说明**:
- 新增 `eval_results` 数组（生成后自动评估）
- 新增 `created_at` 字段
- `citations[].quote` 从空字符串变为章节内容摘要
- `eval_results[].level` 值为前端展示标签: "Pass" / "Warning" / "Blocker"
- `status` 基于评估结果自动设定: 有 BLOCK 级失败 → "blocked"，否则 → "eval_pass"

---

## GET /api/draft (列表)

### Response (扩展)
```json
[
  {
    "draft_id": "DRAFT-20260412...",
    "status": "eval_pass",
    "generated_by": "openai/claude-sonnet-4-6",
    "created_at": "2026-04-12T07:26:04Z",
    "subject": "接口变更测试",
    "eval_summary": {
      "pass": 6,
      "warn": 1,
      "block": 1
    }
  }
]
```

**变更说明**:
- 新增 `subject` 字段（从 request_json 提取）
- 新增 `eval_summary` 对象（从 eval_results_json 统计）

---

## GET /api/draft/{draft_id} (详情, 不变)

响应结构不变，eval_results 已包含在内。level 字段的值在评估时已映射为 "Pass"/"Warning"/"Blocker"。

---

## GET /api/draft/{draft_id}/export (不变)

响应: `text/plain` 原始 Markdown 文本。前端补充下载触发逻辑。
