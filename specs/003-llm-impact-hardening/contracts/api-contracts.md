# API Contracts: LLM Connectivity and Impact Localization Hardening

## POST /api/draft/generate

### Request

```json
{
  "subject": "推进与结构接口规格草稿",
  "related_doc_ids": ["DOC-SYS-001", "DOC-ICD-001"],
  "template_id": "DOC-TPL-001",
  "extra": {}
}
```

### Behavioral Contract

- MUST 使用当前应用 settings 中的 `llm_model` / `llm_base_url`
- MUST 支持 `gemma4:26b` 这种裸 Ollama 模型名
- On success: 返回现有 `draft_id/status/content_md/citations/conflicts` 结构
- On failure: `detail` MUST 包含模型名、base URL 和异常类型，便于诊断 LLM 配置问题

### Error Example

```json
{
  "detail": "LLM generation failed for model=ollama/gemma4:26b api_base=http://localhost:11434: BadRequestError: ..."
}
```

## GET /api/status and GET /api/dashboard/stats

### Behavioral Contract

- MUST 继续返回相同 JSON 字段
- `llm_available` 对 Ollama MUST 基于目标模型是否存在，而不只是 endpoint 可达
- MUST 使用与草稿生成相同的 `llm_model` / `llm_base_url` 解析规则

## POST /api/impact/analyze

### Request

```json
{
  "doc_id": "DOC-SYS-001",
  "old_version": "v3.0",
  "new_version": "v3.1",
  "changed_section_ids": []
}
```

### Behavioral Contract

- MUST 保持现有响应结构不变
- `impacted_docs[].affected_sections` MUST 优先来自 section-aware edges
- 当旧边缺少 target/source section 时，MUST 回退到章节文本锚点匹配，而不是一律返回空数组
- BFS 传播 MUST 继续支持多跳下游文档