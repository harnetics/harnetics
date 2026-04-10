# API Contract: Impact

**Domain**: 变更影响分析（分析、报告查看）
**Base Path**: `/api/impact`

---

## POST /api/impact/analyze

分析文档变更影响——对比新旧版本，识别受影响下游文档。

**Content-Type**: `application/json`

**Request Body**:
```json
{
  "doc_id": "DOC-ICD-001",
  "old_version": "v2.1",
  "new_version": "v2.3"
}
```

| Field         | Type   | Required | Description          |
|---------------|--------|----------|----------------------|
| `doc_id`      | string | Yes      | 变更文档编号          |
| `old_version` | string | No       | 旧版本（默认从 versions 表取上一版本） |
| `new_version` | string | No       | 新版本（默认当前版本）  |

**Response 200**:
```json
{
  "report_id": "IMPACT-20260405-001",
  "trigger_doc_id": "DOC-ICD-001",
  "old_version": "v2.1",
  "new_version": "v2.3",
  "changed_sections": [
    {
      "section_id": "DOC-ICD-001-sec-param-ICD-PRP-001",
      "heading": "ICD-PRP-001 地面推力",
      "change_type": "modified",
      "old_value": "600 kN",
      "new_value": "650 kN"
    },
    {
      "section_id": "DOC-ICD-001-sec-param-ICD-PRP-004",
      "heading": "ICD-PRP-004 燃烧室压力",
      "change_type": "modified",
      "old_value": "9.5 MPa",
      "new_value": "10.0 MPa"
    }
  ],
  "impacted_docs": [
    {
      "doc_id": "DOC-DES-001",
      "title": "TQ-12 液氧甲烷发动机分系统设计文档",
      "department": "动力系统部",
      "severity": "Critical",
      "affected_sections": ["§3.1 推力设计点"],
      "recommendation": "更新",
      "reason": "直接引用 ICD-PRP-001 推力参数"
    },
    {
      "doc_id": "DOC-TST-001",
      "title": "TQ-12 发动机额定工况热试车测试大纲",
      "department": "动力系统部",
      "severity": "Critical",
      "affected_sections": ["§3.1 额定推力性能试验"],
      "recommendation": "更新",
      "reason": "测试判据引用推力 650 kN"
    },
    {
      "doc_id": "DOC-TST-003",
      "title": "TQ-12 推力室点火试验测试大纲",
      "department": "动力系统部",
      "severity": "Critical",
      "affected_sections": ["§2.1 试验参数"],
      "recommendation": "更新",
      "reason": "引用 ICD v2.1 推力值 600 kN，与 v2.3 不一致"
    },
    {
      "doc_id": "DOC-OVR-001",
      "title": "天行一号运载火箭总体设计方案",
      "department": "总体设计部",
      "severity": "Major",
      "affected_sections": ["§4.2 动力系统指标"],
      "recommendation": "审查",
      "reason": "间接引用动力指标"
    }
  ],
  "summary": "ICD 推力参数从 600→650 kN、室压从 9.5→10.0 MPa，影响 4 份下游文档，其中 3 份 Critical、1 份 Major",
  "created_at": "2026-04-05T15:00:00"
}
```

**Severity Rules**:
- **Critical**: 直接引用变更参数（edge depth=1, relation=constrained_by/traces_to）
- **Major**: 间接引用（edge depth=2）或 references 关系
- **Minor**: edge depth ≥3 或弱关联

**Performance**: <30 seconds

---

## GET /api/impact/{report_id}

获取影响报告详情。

**Path Parameters**: `report_id` — 报告编号

**Response 200**: 与 POST 分析结果结构相同

**Response 404**:
```json
{
  "error": "NOT_FOUND",
  "detail": "影响报告 IMPACT-20260405-999 不存在"
}
```

---

## GET /api/impact/{report_id}/export

导出影响报告为 Markdown 文件。

**Path Parameters**: `report_id` — 报告编号

**Response 200**: `Content-Type: text/markdown; charset=utf-8`, `Content-Disposition: attachment; filename="IMPACT-20260405-001.md"`

Export format:
```markdown
# 变更影响分析报告

## 变更源
- 文档: DOC-ICD-001 天行一号全局接口控制文档
- 版本: v2.1 → v2.3

## 变更内容
| 参数 | 旧值 | 新值 |
|------|------|------|
| ICD-PRP-001 地面推力 | 600 kN | 650 kN |

## 受影响文档
| 文档 | 部门 | 级别 | 受影响章节 | 建议 |
|------|------|------|-----------|------|
| DOC-DES-001 | 动力系统部 | 🔴 Critical | §3.1 推力设计点 | 更新 |
...
```
