# Data Model: LLM Connectivity and Impact Localization Hardening

## ResolvedLlmConfig

表示运行期最终使用的 LLM 配置。

| Field | Type | Description |
|-------|------|-------------|
| `model` | `str` | 归一化后的 provider/model，例如 `ollama/gemma4:26b` |
| `api_base` | `str | None` | 最终有效的 provider base URL |
| `api_key` | `str | None` | 云端 provider 凭证；本地 Ollama 可为空 |
| `provider` | derived | 由 `model` 与 `api_base` 推导出的 provider 语义 |

## ReferenceSignal

从章节内容抽取出来的稳定引用锚点集合。

| Field | Type | Description |
|-------|------|-------------|
| `doc_ids` | `set[str]` | 文本里出现的文档编号，如 `DOC-SYS-001` |
| `anchors` | `set[str]` | 需求号/ICD 参数号等锚点，如 `REQ-SYS-003` |
| `section_refs` | `set[str]` | 显式章节号，如 `3.2` |

## SectionAwareEdge

图谱边的章节级版本。

| Field | Type | Description |
|-------|------|-------------|
| `source_doc_id` | `str` | 当前下游文档编号 |
| `source_section_id` | `str` | 引用发生的下游章节 |
| `target_doc_id` | `str` | 被引用的上游文档编号 |
| `target_section_id` | `str` | 若能推断则指向上游章节，否则为空 |
| `relation` | `str` | `references` / `derived_from` / `constrained_by` 等 |

## LocalizedImpact

影响分析对单个受影响文档的定位结果。

| Field | Type | Description |
|-------|------|-------------|
| `doc_id` | `str` | 受影响文档编号 |
| `severity` | `str` | critical / major / minor |
| `relation` | `str` | 传播到该文档的边关系 |
| `affected_sections` | `list[str]` | 被定位出的章节 ID 列表 |
| `upstream_context` | derived | 来自上游变更章节的锚点集合，用于 fallback 匹配 |

## State Transitions

1. 上传/导入文档时，indexer 把原始章节解析成 `Section`
2. 每个章节抽取 `ReferenceSignal`，构建 `SectionAwareEdge`
3. 影响分析从触发文档的变更章节出发，沿 BFS 传播
4. 对每个受影响文档，优先利用 `SectionAwareEdge` 回溯 `affected_sections`
5. 当边不完整时，回退到 `ReferenceSignal` 与章节内容匹配生成 `affected_sections`