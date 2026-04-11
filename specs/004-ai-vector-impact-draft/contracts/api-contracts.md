# API Contracts: AI 向量驱动的影响分析与草稿联动

## POST /api/impact/analyze (扩展)

**Request** — 不变：
```json
{
  "doc_id": "DOC-FMA-001",
  "old_version": "3.0",
  "new_version": "3.1",
  "changed_section_ids": []
}
```

**Response** — 扩展 `affected_sections` 和新增 `analysis_mode`：
```json
{
  "report_id": "uuid",
  "trigger_doc_id": "DOC-FMA-001",
  "old_version": "3.0",
  "new_version": "3.1",
  "analysis_mode": "ai_vector",
  "summary": "文档 DOC-FMA-001 ... 影响 4 个下游文档",
  "changed_sections": [
    { "section_id": "DOC-FMA-001-sec-4", "heading": "4 动力系统故障模式", "change_type": "modified", "summary": "..." }
  ],
  "impacted_docs": [
    {
      "doc_id": "DOC-TST-001",
      "title": "TQ-12 液氧甲烷发动机额定工况热试车测试大纲",
      "relation": "constrained_by",
      "affected_sections": [
        { "section_id": "DOC-TST-001-sec-3", "heading": "3 测试项目", "reason": "故障模式分类变更影响测试覆盖范围" },
        { "section_id": "DOC-TST-001-sec-5", "heading": "5 判定准则", "reason": "故障判定阈值依赖已修改的故障等级" }
      ],
      "severity": "major"
    }
  ],
  "created_at": "2026-04-11T..."
}
```

**变更点**:
- `analysis_mode` 新增字段 ("ai_vector" | "heuristic")
- `affected_sections` 从 `string[]` 改为 `AffectedSection[]`
- 向后兼容：前端 fallback 处理 string 和 object 两种格式

---

## GET /api/documents/search (新增)

**Request**:
```
GET /api/documents/search?q=涡轮泵性能试验&top_k=10
```

**Query Parameters**:
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| q | string | required | 搜索关键词（向量语义检索） |
| top_k | int | 10 | 返回最相关的文档数量 |

**Response**:
```json
{
  "results": [
    {
      "doc_id": "DOC-TST-002",
      "title": "TQ-12 涡轮泵组件性能试验测试大纲",
      "doc_type": "TestPlan",
      "department": "试验与验证部",
      "version": "v1.0",
      "relevance_score": 0.92
    },
    {
      "doc_id": "DOC-TST-001",
      "title": "TQ-12 液氧甲烷发动机额定工况热试车测试大纲",
      "doc_type": "TestPlan",
      "department": "试验与验证部",
      "version": "v2.0",
      "relevance_score": 0.78
    }
  ],
  "analysis_mode": "ai_vector"
}
```

**Fallback**: 当向量索引不可用时，退化为标题关键词匹配，`analysis_mode` 返回 "keyword"。

---

## POST /api/draft/generate (扩展)

**Request** — 新增可选预填字段：
```json
{
  "subject": "DOC-TST-001 对齐更新：响应 DOC-FMA-001 v3.1 变更",
  "related_doc_ids": ["DOC-FMA-001", "DOC-TST-001"],
  "template_id": "",
  "source_report_id": "uuid"
}
```

**变更点**:
- `source_report_id` 新增可选字段，追溯草稿来源的影响报告

---

## GET /api/status (扩展)

**Response** — 新增 embedding 状态：
```json
{
  "status": "ok",
  "llm_available": true,
  "llm_model": "deepseek/deepseek-chat",
  "embedding_available": true,
  "embedding_model": "text-embedding-3-small",
  "documents_indexed": 10,
  "sections_indexed": 156
}
```
