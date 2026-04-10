# API Contract: Evaluate

**Domain**: Evaluator 质量门（运行检查、查看结果）
**Base Path**: `/api/evaluate`

---

## POST /api/evaluate/{draft_id}

对指定草稿运行全部 Evaluator 检查。

**Path Parameters**: `draft_id` — 草稿编号

**Query Parameters**:

| Param        | Type     | Required | Description                     |
|--------------|----------|----------|---------------------------------|
| `evaluators` | string   | No       | 逗号分隔的 Evaluator ID，默认全部 |

**Response 200**:
```json
{
  "draft_id": "DRAFT-20260405-001",
  "results": [
    {
      "evaluator_id": "EA.1",
      "name": "引注完整性",
      "status": "pass",
      "level": "block",
      "detail": "20/20 个技术段落有引注标记",
      "locations": []
    },
    {
      "evaluator_id": "EA.2",
      "name": "引用真实性",
      "status": "pass",
      "level": "block",
      "detail": "15/15 个引用文档在文档库中存在",
      "locations": []
    },
    {
      "evaluator_id": "EA.3",
      "name": "版本最新",
      "status": "warn",
      "level": "warn",
      "detail": "1 个引用版本非最新",
      "locations": ["DOC-TST-003 引用 ICD v2.1，当前版本 v2.3"]
    },
    {
      "evaluator_id": "EA.4",
      "name": "无循环引用",
      "status": "pass",
      "level": "block",
      "detail": "DFS 检测无环",
      "locations": []
    },
    {
      "evaluator_id": "EA.5",
      "name": "引注覆盖率",
      "status": "pass",
      "level": "warn",
      "detail": "覆盖率 92% (≥80% 阈值)",
      "locations": []
    },
    {
      "evaluator_id": "EB.1",
      "name": "ICD 参数一致性",
      "status": "pass",
      "level": "block",
      "detail": "8/8 个 ICD 参数值与 ICD 表一致",
      "locations": []
    },
    {
      "evaluator_id": "ED.1",
      "name": "无捏造技术指标",
      "status": "pass",
      "level": "block",
      "detail": "所有数字可在源文档中找到",
      "locations": []
    },
    {
      "evaluator_id": "ED.3",
      "name": "冲突已标记",
      "status": "pass",
      "level": "block",
      "detail": "1/1 个冲突已在正文中标记",
      "locations": []
    }
  ],
  "summary": {
    "total": 8,
    "pass": 7,
    "warn": 1,
    "fail": 0,
    "skip": 0,
    "has_blocking_failures": false,
    "export_allowed": true
  }
}
```

---

## GET /api/evaluate/results/{eval_id}

获取单次检查结果详情。

**Path Parameters**: `eval_id` — 评估记录 ID（格式: `{draft_id}-{evaluator_id}`）

**Response 200**:
```json
{
  "eval_id": "DRAFT-20260405-001-EA.3",
  "draft_id": "DRAFT-20260405-001",
  "evaluator_id": "EA.3",
  "name": "版本最新",
  "status": "warn",
  "level": "warn",
  "detail": "1 个引用版本非最新",
  "locations": [
    "DOC-TST-003 引用 ICD v2.1，当前版本 v2.3"
  ],
  "checked_at": "2026-04-05T14:31:00"
}
```

---

## Evaluator Reference

| ID   | 名称             | 级别  | 检查逻辑                                            |
|------|------------------|-------|-----------------------------------------------------|
| EA.1 | 引注完整性       | block | 正则匹配含数字/参数的段落，检查 📎 标记存在          |
| EA.2 | 引用真实性       | block | 提取 DOC-XXX-XXX 编号，查询 documents 表存在         |
| EA.3 | 版本最新         | warn  | 比对引注中的版本与 documents 表最新 non-Superseded 版本 |
| EA.4 | 无循环引用       | block | 对 edges 表执行 DFS 环检测                           |
| EA.5 | 引注覆盖率 ≥80% | warn  | 技术段落数(含数字) / 有引注段落数                    |
| EB.1 | ICD 参数一致性   | block | 草稿中参数名+值 vs icd_parameters 表值              |
| ED.1 | 无捏造技术指标   | block | 草稿中每个数字交叉验证源文档章节                    |
| ED.3 | 冲突已标记       | block | conflicts 列表条目 vs 草稿正文 ⚠️ 标记存在          |

**Export Gate**: 当 `has_blocking_failures = true`（即任何 `level=block` 且 `status=fail` 的 Evaluator 存在），草稿导出接口返回 403。
