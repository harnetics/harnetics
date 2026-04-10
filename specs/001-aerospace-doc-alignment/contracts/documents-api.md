# API Contract: Documents

**Domain**: 文档管理（上传、浏览、详情、删除）
**Base Path**: `/api/documents`

---

## POST /api/documents/upload

上传并解析文档。

**Content-Type**: `multipart/form-data`

**Request Fields**:

| Field              | Type   | Required | Description                     |
|--------------------|--------|----------|---------------------------------|
| `file`             | File   | Yes      | Markdown (.md) 或 YAML (.yaml/.yml) 文件 |
| `doc_id`           | string | Yes      | 文档编号（DOC-XXX-NNN 格式）     |
| `title`            | string | Yes      | 文档标题                        |
| `doc_type`         | string | Yes      | 文档类型（见枚举）               |
| `department`       | string | No       | 所属部门                        |
| `system_level`     | string | No       | 系统层级（见枚举）               |
| `engineering_phase`| string | No       | 工程阶段（见枚举）               |
| `version`          | string | Yes      | 版本号                          |
| `is_icd`           | bool   | No       | 是否为 ICD 文档（启用参数提取）   |

**doc_type 枚举**: `ICD`, `Requirement`, `Design`, `TestPlan`, `TestReport`, `Analysis`, `Status`, `Template`, `QualityPlan`, `FMEA`, `OverallDesign`

**system_level 枚举**: `Mission`, `System`, `Subsystem`, `Unit`, `Component`

**engineering_phase 枚举**: `Requirement`, `Design`, `Integration`, `Test`, `Operation`

**Response 200**:
```json
{
  "doc_id": "DOC-SYS-001",
  "title": "天行一号运载火箭系统级需求文档",
  "doc_type": "Requirement",
  "department": "系统工程部",
  "version": "v3.1",
  "status": "Approved",
  "sections_count": 12,
  "icd_parameters_count": 0,
  "edges_created": 3,
  "message": "文档导入成功"
}
```

**Response 400**:
```json
{
  "error": "UNSUPPORTED_FORMAT",
  "detail": "MVP 仅支持 Markdown 和 YAML 格式"
}
```

**Response 409**:
```json
{
  "error": "DOC_EXISTS",
  "detail": "文档 DOC-SYS-001 已存在，当前版本 v3.0",
  "current_version": "v3.0",
  "action_required": "请选择覆盖或取消"
}
```

**Performance**: <5s per document

---

## GET /api/documents

文档列表（支持筛选）。

**Query Parameters**:

| Param        | Type   | Required | Description          |
|--------------|--------|----------|----------------------|
| `department` | string | No       | 按部门筛选            |
| `doc_type`   | string | No       | 按类型筛选            |
| `system_level`| string| No       | 按层级筛选            |
| `status`     | string | No       | 按状态筛选            |
| `q`          | string | No       | 关键词搜索（标题+内容）|
| `page`       | int    | No       | 页码，默认 1          |
| `per_page`   | int    | No       | 每页数量，默认 20     |

**Response 200**:
```json
{
  "documents": [
    {
      "doc_id": "DOC-SYS-001",
      "title": "天行一号运载火箭系统级需求文档",
      "doc_type": "Requirement",
      "department": "系统工程部",
      "system_level": "System",
      "version": "v3.1",
      "status": "Approved",
      "updated_at": "2026-04-05T10:00:00"
    }
  ],
  "total": 10,
  "page": 1,
  "per_page": 20
}
```

---

## GET /api/documents/{doc_id}

文档详情（含 sections）。

**Path Parameters**: `doc_id` — 文档编号

**Response 200**:
```json
{
  "doc_id": "DOC-SYS-001",
  "title": "天行一号运载火箭系统级需求文档",
  "doc_type": "Requirement",
  "department": "系统工程部",
  "system_level": "System",
  "engineering_phase": "Requirement",
  "version": "v3.1",
  "status": "Approved",
  "content_hash": "sha256:abc123...",
  "created_at": "2026-04-05T10:00:00",
  "updated_at": "2026-04-05T10:00:00",
  "sections": [
    {
      "section_id": "DOC-SYS-001-sec-3.2",
      "heading": "3.2 动力系统性能需求",
      "content": "REQ-SYS-003 地面推力 ≥ 650 kN ±3%...",
      "level": 2,
      "order_index": 5
    }
  ],
  "upstream_docs": [
    {"doc_id": "DOC-ICD-001", "relation": "derived_from", "confidence": 1.0}
  ],
  "downstream_docs": [
    {"doc_id": "DOC-DES-001", "relation": "traces_to", "confidence": 1.0},
    {"doc_id": "DOC-TST-001", "relation": "traces_to", "confidence": 0.85}
  ]
}
```

**Response 404**:
```json
{
  "error": "NOT_FOUND",
  "detail": "文档 DOC-XXX-999 不存在"
}
```

---

## DELETE /api/documents/{doc_id}

删除文档（级联删除 sections、edges、icd_parameters）。

**Path Parameters**: `doc_id` — 文档编号

**Response 200**:
```json
{
  "doc_id": "DOC-SYS-001",
  "message": "文档已删除",
  "sections_deleted": 12,
  "edges_deleted": 3
}
```

---

## GET /api/documents/{doc_id}/sections

获取文档所有章节。

**Path Parameters**: `doc_id` — 文档编号

**Response 200**:
```json
{
  "doc_id": "DOC-SYS-001",
  "sections": [
    {
      "section_id": "DOC-SYS-001-sec-1",
      "heading": "1. 文档说明",
      "content": "...",
      "level": 1,
      "order_index": 0
    }
  ]
}
```

---

## GET /api/icd/parameters

所有 ICD 参数列表。

**Response 200**:
```json
{
  "parameters": [
    {
      "param_id": "ICD-PRP-001",
      "doc_id": "DOC-ICD-001",
      "name": "地面推力",
      "interface_type": "Propellant",
      "subsystem_a": "发动机",
      "subsystem_b": "测试台",
      "value": "650 kN",
      "unit": "kN",
      "range": "630.5~669.5 kN (±3%)",
      "owner_department": "动力系统部",
      "version": "v2.3"
    }
  ],
  "total": 12
}
```

---

## GET /api/icd/parameters/{param_id}

单个 ICD 参数详情。

**Path Parameters**: `param_id` — 参数编号（ICD-XXX-NNN）

**Response 200**:
```json
{
  "param_id": "ICD-PRP-001",
  "doc_id": "DOC-ICD-001",
  "name": "地面推力",
  "interface_type": "Propellant",
  "subsystem_a": "发动机",
  "subsystem_b": "测试台",
  "value": "650 kN",
  "unit": "kN",
  "range": "630.5~669.5 kN (±3%)",
  "owner_department": "动力系统部",
  "version": "v2.3",
  "referencing_docs": [
    {"doc_id": "DOC-DES-001", "section": "§3.1"},
    {"doc_id": "DOC-TST-001", "section": "§3.1"}
  ]
}
```
