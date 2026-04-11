# Data Model: AI 向量驱动的影响分析与草稿联动

## Entity: AffectedSection (新增)

替代原 `affected_sections: list[str]`，承载 AI 分析结果。

| Field | Type | Description |
|-------|------|-------------|
| section_id | str | 章节唯一 ID (如 DOC-TST-001-sec-3) |
| heading | str | 章节标题 (如 "3.2 动力系统测试用例") |
| reason | str | AI 生成的影响理由 (1 句话) |

**JSON 表示**:
```json
{
  "section_id": "DOC-TST-001-sec-3",
  "heading": "3.2 动力系统测试用例",
  "reason": "source 文档修改了故障模式分类，直接影响此章节的测试覆盖范围"
}
```

## Entity: Settings (扩展)

新增 embedding 配置字段：

| Field | Type | Default | Env Var |
|-------|------|---------|---------|
| embedding_model | str | "paraphrase-multilingual-MiniLM-L12-v2" | HARNETICS_EMBEDDING_MODEL |
| embedding_api_key | str | "" | HARNETICS_EMBEDDING_API_KEY |
| embedding_base_url | str | "" | HARNETICS_EMBEDDING_BASE_URL |
| llm_api_key | str | "" | HARNETICS_LLM_API_KEY |

## Entity: ImpactedDoc (扩展)

`affected_sections` 字段从 `list[str]` 变为 `list[AffectedSection]`。

新增字段：

| Field | Type | Description |
|-------|------|-------------|
| analysis_mode | str | "ai_vector" 或 "heuristic"，标识本次分析使用的模式 |

## Entity: DocumentSearchResult (新增)

候选文档向量检索结果。

| Field | Type | Description |
|-------|------|-------------|
| doc_id | str | 文档 ID |
| title | str | 文档标题 |
| doc_type | str | 文档类型 |
| department | str | 归属部门 |
| version | str | 版本 |
| relevance_score | float | 向量相关度 (0-1, 1 为最相关) |

## Entity: DraftPrefill (新增)

影响报告→草稿台联动参数，通过 URL query params 传递。

| Field | Type | Description |
|-------|------|-------------|
| trigger_doc_id | str | 触发变更的文档 ID |
| impacted_doc_id | str | 受影响的目标文档 ID |
| report_id | str | 来源影响报告 ID |
| subject | str | 自动生成的草稿主题 |
| related_doc_ids | list[str] | 预选的来源文档列表 |

## State Transitions

### Impact Analysis Mode

```
请求到达 → 检查 embedding_store 可用性
  ├─ 可用 → ai_vector 模式（向量粗筛 → LLM 精判）
  └─ 不可用 → heuristic 模式（现有规则引擎）
```

### Draft Prefill Flow

```
影响报告页 → 点击"生成对齐草稿" → URL ?trigger_doc_id=X&impacted_doc_id=Y
  → DraftNew 读取 URL params → 自动生成 subject → 自动预选 related_doc_ids
  → 用户确认 → 触发生成
```
