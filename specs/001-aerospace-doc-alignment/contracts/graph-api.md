# API Contract: Graph

**Domain**: 文档图谱查询（完整图谱、上下游追溯、过期引用、横向关联）
**Base Path**: `/api/graph`

---

## GET /api/graph

完整图谱数据（vis-network.js 格式）。

**Query Parameters**:

| Param        | Type   | Required | Description          |
|--------------|--------|----------|----------------------|
| `department` | string | No       | 按部门过滤节点        |
| `system_level`| string| No       | 按层级过滤节点        |

**Response 200**:
```json
{
  "nodes": [
    {
      "id": "DOC-SYS-001",
      "label": "DOC-SYS-001\n系统需求",
      "title": "天行一号运载火箭系统级需求文档 v3.1",
      "group": "系统工程部",
      "shape": "dot",
      "size": 20
    },
    {
      "id": "DOC-ICD-001",
      "label": "DOC-ICD-001\n全局ICD",
      "title": "天行一号全局接口控制文档 v2.3",
      "group": "技术负责人",
      "shape": "diamond",
      "size": 30
    }
  ],
  "edges": [
    {
      "from": "DOC-SYS-001",
      "to": "DOC-ICD-001",
      "label": "derived_from",
      "title": "derived_from (confidence: 1.0)",
      "dashes": false,
      "arrows": "to"
    }
  ],
  "groups": {
    "系统工程部": {"color": "#3B82F6"},
    "动力系统部": {"color": "#EF4444"},
    "试验与验证部": {"color": "#22C55E"},
    "技术负责人": {"color": "#F97316"},
    "总体设计部": {"color": "#8B5CF6"},
    "质量与可靠性部": {"color": "#06B6D4"}
  },
  "stats": {
    "nodes_count": 10,
    "edges_count": 15
  }
}
```

**vis-network.js 集成说明**:
- `nodes[].group` 映射到 `groups` 对象中的颜色
- `nodes[].shape`: ICD 文档用 `diamond`（菱形，突出枢纽地位），其他用 `dot`
- `nodes[].size`: ICD 文档 size=30（更大），其他 size=20
- `edges[].dashes`: `references` 关系用虚线，其他用实线
- `edges[].arrows`: 始终 `"to"`，从 source 指向 target

---

## GET /api/graph/upstream/{doc_id}

上游追溯——找到指定文档的所有"依据"文档（递归到根）。

**Path Parameters**: `doc_id` — 文档编号

**Query Parameters**:

| Param  | Type | Required | Description            |
|--------|------|----------|------------------------|
| `depth`| int  | No       | 最大追溯深度，默认 5    |

**Response 200**:
```json
{
  "doc_id": "DOC-TST-001",
  "upstream": [
    {
      "doc_id": "DOC-DES-001",
      "relation": "traces_to",
      "depth": 1,
      "confidence": 1.0
    },
    {
      "doc_id": "DOC-SYS-001",
      "relation": "traces_to",
      "depth": 2,
      "confidence": 1.0
    },
    {
      "doc_id": "DOC-ICD-001",
      "relation": "constrained_by",
      "depth": 1,
      "confidence": 1.0
    }
  ]
}
```

---

## GET /api/graph/downstream/{doc_id}

下游追溯——找到指定文档的所有"受影响"文档（递归向下）。

**Path Parameters**: `doc_id` — 文档编号

**Query Parameters**:

| Param  | Type | Required | Description            |
|--------|------|----------|------------------------|
| `depth`| int  | No       | 最大追溯深度，默认 5    |

**Response 200**:
```json
{
  "doc_id": "DOC-SYS-001",
  "downstream": [
    {
      "doc_id": "DOC-ICD-001",
      "relation": "derived_from",
      "depth": 1,
      "confidence": 1.0
    },
    {
      "doc_id": "DOC-DES-001",
      "relation": "traces_to",
      "depth": 1,
      "confidence": 1.0
    },
    {
      "doc_id": "DOC-TST-001",
      "relation": "traces_to",
      "depth": 2,
      "confidence": 0.85
    }
  ]
}
```

---

## GET /api/graph/stale

过期引用列表——找到引用了 Superseded 版本文档的关系。

**Response 200**:
```json
{
  "stale_references": [
    {
      "edge_id": 14,
      "source_doc_id": "DOC-TST-003",
      "target_doc_id": "DOC-ICD-001",
      "relation": "constrained_by",
      "referenced_version": "v2.1",
      "current_version": "v2.3",
      "severity": "warn"
    }
  ],
  "total": 1
}
```

---

## GET /api/graph/related/{doc_id}

横向关联——找到与指定文档共享引用源或相同 ICD 参数的文档。

**Path Parameters**: `doc_id` — 文档编号

**Response 200**:
```json
{
  "doc_id": "DOC-TST-001",
  "related": [
    {
      "doc_id": "DOC-TST-002",
      "shared_sources": ["DOC-DES-001", "DOC-ICD-001"],
      "shared_params": ["ICD-PRP-001", "ICD-PRP-002"],
      "relation_strength": 0.85
    },
    {
      "doc_id": "DOC-TST-003",
      "shared_sources": ["DOC-DES-001"],
      "shared_params": ["ICD-PRP-001"],
      "relation_strength": 0.70
    }
  ]
}
```
