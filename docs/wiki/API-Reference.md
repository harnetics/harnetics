# API Reference

这页面向第一次阅读 Harnetics API 的贡献者，聚焦最常用的核心 `/api` 路由。示例默认假设本地服务运行在 `http://localhost:8000`。

> 对照源码：`src/harnetics/api/routes/`

## 1. `GET /api/dashboard/stats`

**用途**
- 获取仪表盘摘要
- 快速确认文档、草稿、影响分析、向量索引与 LLM/Embedding 状态

**主要输入**
- 无请求体

**主要输出**
- `documents` / `drafts` / `impact_reports`
- `llm_available` / `embedding_available`
- `sections_indexed` / `stale_references`

**最小示例**
```bash
curl http://localhost:8000/api/dashboard/stats
```

```json
{
  "documents": 8,
  "drafts": 3,
  "impact_reports": 1,
  "stale_references": 0,
  "llm_available": true,
  "embedding_available": true,
  "sections_indexed": 124
}
```

---

## 2. `GET /api/documents`

**用途**
- 分页列出文档库中的文档
- 支持按部门、文档类型、系统层级、状态和关键词过滤

**主要输入（Query）**
- `department`
- `doc_type`
- `system_level`
- `status`
- `q`
- `page`（默认 `1`）
- `per_page`（默认 `50`）

**主要输出**
- `total` / `page` / `per_page`
- `documents[]`（文档摘要）

**最小示例**
```bash
curl "http://localhost:8000/api/documents?page=1&per_page=20"
```

```json
{
  "total": 2,
  "page": 1,
  "per_page": 20,
  "documents": [
    {
      "doc_id": "DOC-SYS-001",
      "title": "总体系统需求",
      "doc_type": "requirement",
      "department": "system",
      "version": "v1.0"
    }
  ]
}
```

---

## 3. `GET /api/documents/{doc_id}`

**用途**
- 查看单篇文档详情
- 一次拿到文档元信息、章节、上下游引用边和 ICD 参数

**主要输入（Path）**
- `doc_id`

**主要输出**
- `document`
- `sections[]`
- `upstream[]`
- `downstream[]`
- `icd_parameters[]`

**最小示例**
```bash
curl http://localhost:8000/api/documents/DOC-SYS-001
```

```json
{
  "document": {
    "doc_id": "DOC-SYS-001",
    "title": "总体系统需求"
  },
  "sections": [
    {
      "section_id": "1.0",
      "heading": "任务概述"
    }
  ],
  "upstream": [],
  "downstream": []
}
```

---

## 4. `POST /api/documents/upload`

**用途**
- 上传并导入文档
- 支持 `.md` / `.yaml` / `.yml` / `.docx` / `.xlsx` / `.csv` / `.pdf`
- 导入后自动尝试写入向量索引

**主要输入（FormData）**
- `file`（必填）
- `doc_id`
- `title`
- `doc_type`
- `department`
- `system_level`
- `engineering_phase`
- `version`

**主要输出**
- `status`
- `doc_id`
- `title`

**最小示例**
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@fixtures/samples/DOC-SYS-001.md" \
  -F "doc_id=DOC-SYS-001" \
  -F "title=总体系统需求"
```

```json
{
  "status": "ok",
  "doc_id": "DOC-SYS-001",
  "title": "总体系统需求"
}
```

---

## 5. `POST /api/draft/generate`

**用途**
- 基于图谱上下文生成带引注的 Markdown 草稿
- 可关联模板文档或已有影响分析报告

**主要输入（JSON）**
- `subject`
- `related_doc_ids[]`
- `template_id`
- `source_report_id`
- `extra`（可选扩展字段）

**主要输出**
- `draft_id`
- `status`
- `content_md`
- `citations[]`
- `conflicts[]`
- `eval_results[]`

**最小示例**
```bash
curl -X POST http://localhost:8000/api/draft/generate \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "推进系统联调测试申请",
    "related_doc_ids": ["DOC-SYS-001", "DOC-ICD-001"],
    "template_id": "DOC-TPL-001"
  }'
```

```json
{
  "draft_id": "draft_123",
  "status": "eval_pass",
  "content_md": "# 推进系统联调测试申请...",
  "citations": [],
  "conflicts": [],
  "eval_results": []
}
```

---

## 6. `GET /api/draft` 与 `GET /api/draft/{draft_id}`

**用途**
- `GET /api/draft`：列出历史草稿摘要
- `GET /api/draft/{draft_id}`：查看单条草稿完整详情

**主要输入**
- 列表：无请求体
- 详情：路径参数 `draft_id`

**主要输出**
- 列表包含：`draft_id`、`status`、`subject`、`eval_summary`
- 详情包含：`content_md`、`citations[]`、`conflicts[]`、`eval_results[]`

**最小示例**
```bash
curl http://localhost:8000/api/draft
curl http://localhost:8000/api/draft/draft_123
```

---

## 7. `POST /api/impact/analyze`

**用途**
- 对指定文档触发变更影响分析
- 沿引用图定位受影响文档与章节

**主要输入（JSON）**
- `doc_id`
- `old_version`
- `new_version`
- `changed_section_ids[]`

**主要输出**
- `report_id`
- `summary`
- `analysis_mode`
- `changed_sections[]`
- `impacted_docs[]`

**最小示例**
```bash
curl -X POST http://localhost:8000/api/impact/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "DOC-SYS-001",
    "old_version": "v1.0",
    "new_version": "v1.1",
    "changed_section_ids": ["3.2", "4.1"]
  }'
```

```json
{
  "report_id": "impact_123",
  "summary": "检测到 2 篇受影响文档",
  "analysis_mode": "ai_vector",
  "changed_sections": [],
  "impacted_docs": []
}
```

---

## 8. `GET /api/impact` 与 `GET /api/impact/{report_id}`

**用途**
- `GET /api/impact`：列出历史影响分析报告
- `GET /api/impact/{report_id}`：查看单条报告详情

**主要输入**
- 列表：无请求体
- 详情：路径参数 `report_id`

**主要输出**
- 列表：`report_id`、`trigger_doc_id`、`summary`、`created_at`
- 详情：`changed_sections[]`、`impacted_docs[]`

**最小示例**
```bash
curl http://localhost:8000/api/impact
curl http://localhost:8000/api/impact/impact_123
```

---

## 9. `GET /api/graph` 与 `GET /api/graph/edges`

**用途**
- `GET /api/graph`：返回前端图谱页面使用的全量图结构
- `GET /api/graph/edges`：返回更适合调试或二次处理的原始边列表

**主要输入（Query）**
- `department`
- `system_level`

**主要输出**
- `/api/graph`：`nodes[]`、`edges[]`
- `/api/graph/edges`：每条边的 `source_doc_id`、`target_doc_id`、`relation`、`confidence`

**最小示例**
```bash
curl http://localhost:8000/api/graph
curl http://localhost:8000/api/graph/edges
```

```json
[
  {
    "edge_id": "edge_1",
    "source_doc_id": "DOC-SYS-001",
    "target_doc_id": "DOC-ICD-001",
    "relation": "references",
    "confidence": 0.92
  }
]
```

---

## 10. 相关辅助路由

如果你在补测试或做前端联调，下面几个端点也很常用：

- `GET /api/documents/search`：语义检索优先，失败时降级为关键词检索
- `POST /api/documents/reindex`：重建 ChromaDB 章节向量索引
- `GET /api/status`：与 `/api/dashboard/stats` 共享同一套系统状态载荷
- `GET /api/settings` / `PUT /api/settings`：读取或更新运行时 LLM/Embedding 配置

## 进一步阅读

- [Quick Start](Quick-Start)
- [Architecture Overview](Architecture-Overview)
- [Contributor Guide](Contributor-Guide)
- 仓库 `README.md` 的「API 路由」章节
