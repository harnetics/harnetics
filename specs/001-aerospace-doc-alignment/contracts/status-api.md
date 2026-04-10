# API Contract: Status

**Domain**: 系统状态概览
**Base Path**: `/api/status`

---

## GET /api/status

系统健康和统计信息——仪表盘数据源。

**Response 200**:
```json
{
  "status": "ok",
  "documents_count": 10,
  "sections_count": 87,
  "edges_count": 15,
  "icd_parameters_count": 12,
  "drafts_count": 1,
  "stale_references_count": 1,
  "ollama_available": true,
  "ollama_model": "gemma4:26b-it-a4b-q4_K_M",
  "chromadb_sections_indexed": 87,
  "database_size_mb": 2.3,
  "recent_activity": [
    {
      "timestamp": "2026-04-05T14:30:00",
      "action": "draft_generated",
      "detail": "生成草稿「TQ-12 地面试车测试大纲」",
      "entity_id": "DRAFT-20260405-001"
    },
    {
      "timestamp": "2026-04-05T14:00:00",
      "action": "document_imported",
      "detail": "导入文档 DOC-ICD-001 v2.3",
      "entity_id": "DOC-ICD-001"
    }
  ],
  "eval_pass_rate": {
    "total_checks": 8,
    "pass": 7,
    "warn": 1,
    "fail": 0,
    "rate": 0.875
  },
  "health": {
    "citation_freshness": 0.78,
    "icd_consistency": 1.0,
    "citation_coverage": 0.72
  }
}
```

**Field Details**:

| Field                    | Description                                            |
|--------------------------|--------------------------------------------------------|
| `status`                 | 系统总体状态: `ok` / `degraded` (LLM 不可用) / `error` |
| `documents_count`        | 文档库总文档数                                          |
| `sections_count`         | 全部章节数                                              |
| `edges_count`            | 文档关系总数                                            |
| `icd_parameters_count`   | ICD 参数总数                                            |
| `drafts_count`           | 已生成草稿总数                                          |
| `stale_references_count` | 过期引用数                                              |
| `ollama_available`       | Ollama 服务是否可达                                     |
| `ollama_model`           | 当前 LLM 模型标识                                       |
| `chromadb_sections_indexed`| 已索引章节数                                          |
| `database_size_mb`       | SQLite 数据库文件大小                                    |
| `recent_activity`        | 最近 10 条操作记录                                      |
| `eval_pass_rate`         | 最近一次 Evaluator 运行的通过率统计                      |
| `health`                 | 文档健康度指标 (0.0~1.0)                                 |

**Degraded Mode**: 当 `ollama_available = false`，`status` 变为 `"degraded"`，文档库和图谱功能正常可用，草稿生成不可用。
