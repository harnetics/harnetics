# API Contract: Draft

**Domain**: 草稿生成（创建、查看、列表）
**Base Path**: `/api/draft`

---

## POST /api/draft/generate

生成对齐草稿——检索相关文档、调用 LLM、解析引注、运行 Evaluator。

**Content-Type**: `application/json`

**Request Body**:
```json
{
  "requester_department": "动力系统部",
  "doc_type": "TestPlan",
  "system_level": "Subsystem",
  "subject": "TQ-12液氧甲烷发动机地面全工况热试车测试大纲",
  "parent_doc_id": "DOC-SYS-001",
  "template_id": "DOC-TPL-001",
  "related_doc_ids": ["DOC-ICD-001", "DOC-DES-001", "DOC-TST-001"],
  "constraints": []
}
```

| Field                  | Type     | Required | Description                    |
|------------------------|----------|----------|--------------------------------|
| `requester_department` | string   | Yes      | 请求部门                       |
| `doc_type`             | string   | Yes      | 目标文档类型                    |
| `system_level`         | string   | Yes      | 系统层级                       |
| `subject`              | string   | Yes      | 主题描述（自然语言）            |
| `parent_doc_id`        | string   | No       | 上级文档编号                    |
| `template_id`          | string   | No       | 文档模板编号                    |
| `related_doc_ids`      | string[] | No       | 用户确认的相关文档列表          |
| `constraints`          | string[] | No       | 额外约束（预留）                |

**Response 200**:
```json
{
  "draft_id": "DRAFT-20260405-001",
  "status": "completed",
  "content_md": "# TQ-12 液氧甲烷发动机地面全工况热试车测试大纲\n\n## 1. 测试目的\n...",
  "sections": [
    {
      "heading": "1. 测试目的",
      "content": "本试验旨在验证 TQ-12 液氧甲烷发动机...",
      "citations": [
        {
          "source_doc_id": "DOC-SYS-001",
          "source_section_id": "sec-3.2",
          "source_text_snippet": "动力系统地面推力 ≥ 650 kN...",
          "relation": "需求依据"
        }
      ],
      "confidence": 0.92
    }
  ],
  "conflicts": [
    {
      "parameter": "地面推力",
      "doc_a": {"doc_id": "DOC-ICD-001", "version": "v2.3"},
      "value_a": "650 kN",
      "doc_b": {"doc_id": "DOC-TST-003", "version": "v1.1"},
      "value_b": "600 kN",
      "resolution": "DOC-TST-003 引用的是 ICD v2.1 版本，应更新至 v2.3"
    }
  ],
  "eval_results": [
    {"evaluator": "EA.1", "name": "引注完整性", "status": "pass", "level": "block", "detail": "所有技术指标有来源引用"},
    {"evaluator": "EA.2", "name": "引用真实性", "status": "pass", "level": "block", "detail": "所有引用文档真实存在"},
    {"evaluator": "EA.3", "name": "版本最新", "status": "warn", "level": "warn", "detail": "DOC-TST-003 引用 ICD v2.1 已过期"},
    {"evaluator": "EA.4", "name": "无循环引用", "status": "pass", "level": "block", "detail": "DFS 检测无环"},
    {"evaluator": "EA.5", "name": "覆盖率", "status": "pass", "level": "warn", "detail": "引注覆盖率 92%"},
    {"evaluator": "EB.1", "name": "ICD一致性", "status": "pass", "level": "block", "detail": "参数值与 ICD 一致"},
    {"evaluator": "ED.1", "name": "无捏造指标", "status": "pass", "level": "block", "detail": "所有数字有源文档支撑"},
    {"evaluator": "ED.3", "name": "冲突已标记", "status": "pass", "level": "block", "detail": "所有冲突已在正文标记"}
  ],
  "stats": {
    "related_docs_used": 7,
    "sections_retrieved": 42,
    "icd_params_extracted": 12,
    "generation_time_seconds": 95
  },
  "created_at": "2026-04-05T14:30:00"
}
```

**Response 400**:
```json
{
  "error": "EMPTY_DOCUMENT_STORE",
  "detail": "请先导入至少一份参考文档"
}
```

**Response 503**:
```json
{
  "error": "LLM_UNAVAILABLE",
  "detail": "Ollama 服务未启动，请运行: ollama serve"
}
```

**Performance**: <3 minutes for 10-doc context

**Processing Flow**:
1. 按 metadata filter (department, doc_type) + 向量检索找到相关文档章节
2. 提取 ICD 约束参数
3. 组装 system prompt + context + user request
4. 调用 LLM 生成草稿
5. 解析引注标记 [📎 DOC-XXX-XXX §X.X]
6. 运行冲突检测
7. 运行全部 8 个 Evaluator
8. 返回完整结果

---

## GET /api/draft/{draft_id}

获取草稿详情。

**Path Parameters**: `draft_id` — 草稿编号

**Response 200**: 与 POST 生成结果结构相同

**Response 404**:
```json
{
  "error": "NOT_FOUND",
  "detail": "草稿 DRAFT-20260405-999 不存在"
}
```

---

## GET /api/drafts

草稿列表。

**Query Parameters**:

| Param    | Type   | Required | Description          |
|----------|--------|----------|----------------------|
| `status` | string | No       | 按状态筛选            |
| `page`   | int    | No       | 页码，默认 1          |
| `per_page`| int   | No       | 每页数量，默认 20     |

**Response 200**:
```json
{
  "drafts": [
    {
      "draft_id": "DRAFT-20260405-001",
      "subject": "TQ-12液氧甲烷发动机地面全工况热试车测试大纲",
      "status": "completed",
      "eval_summary": {"pass": 6, "warn": 2, "fail": 0, "block": 0},
      "created_at": "2026-04-05T14:30:00"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20
}
```

---

## GET /api/draft/{draft_id}/export

导出草稿为 Markdown 文件下载。

**Path Parameters**: `draft_id` — 草稿编号

**Response 200**: `Content-Type: text/markdown; charset=utf-8`, `Content-Disposition: attachment; filename="DRAFT-20260405-001.md"`

**Response 403**:
```json
{
  "error": "EXPORT_BLOCKED",
  "detail": "Evaluator 阻断项未通过，无法导出",
  "blocking_evaluators": ["EA.1", "EB.1"]
}
```
