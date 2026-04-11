# Research: AI 向量驱动的影响分析与草稿联动

## Decision 1: Embedding 提供商路由方案

**Decision**: 使用 litellm.embedding() 作为统一入口，支持本地 sentence-transformers 和云端 OpenAI/其他提供商
**Rationale**: litellm 已是项目依赖，其 embedding() 函数支持 `openai/text-embedding-3-small`、`ollama/nomic-embed-text` 等多提供商路由，无需额外封装
**Alternatives considered**:
- 直接使用 OpenAI client：需要额外依赖，且不支持 Ollama embedding
- chromadb 内置 embedding function：不支持云端 API key 路由

**实现要点**: 
- 本地模型（sentence-transformers）保持 ChromaDB 原生 `SentenceTransformerEmbeddingFunction`
- 云端模型通过自定义 `ChromaDB EmbeddingFunction` 包装 `litellm.embedding()`
- 检测方式：model_name 包含 `/` 时为云端路由（如 `openai/text-embedding-3-small`），否则为本地

## Decision 2: 影响分析 AI 路径架构

**Decision**: 向量粗筛 + LLM 精判两阶段流水线
**Rationale**: 纯向量相似度无法理解"影响"的因果语义（相似≠受影响），纯 LLM 处理全文太慢。两阶段结合：向量快速缩小候选集（50→10），LLM 精判因果关系（10→3-5）
**Alternatives considered**:
- 纯向量方案：快但精度不够，"动力系统"和"推进系统"可能向量很近但一个不受另一个影响
- 纯 LLM 方案：精确但慢，将 20 个章节全文送 LLM 做判定要 30s+
- GraphRAG：过度工程，当前规模（10-100 文档）不需要

## Decision 3: .env 配置加载方案

**Decision**: python-dotenv 在 `get_settings()` 入口 `load_dotenv()`，环境变量优先级高于 .env 文件
**Rationale**: python-dotenv 是 Python Web 项目标准配置方式，FastAPI 官方推荐
**Alternatives considered**:
- pydantic-settings：过度封装，当前 dataclass 够用
- 纯环境变量：不方便本地开发，需要每次 export

## Decision 4: affected_sections 结构变更

**Decision**: 从 `list[str]` 扩展为 `list[AffectedSection]`，其中 `AffectedSection = {section_id, heading, reason}`
**Rationale**: 后端已有 section heading 信息，reason 由 LLM 生成。前端需要展示影响理由，仅 section_id 不够
**Alternatives considered**:
- 保持 `list[str]` + 新增 `reasons` 并行字段：易错，不利维护
- 嵌套到 ImpactedDoc.details 中：过度嵌套

## Decision 5: 草稿台联动传参方式

**Decision**: URL query params `?trigger_doc_id=X&impacted_doc_id=Y&report_id=Z`，前端 DraftNew 从 URL 读取后自动预填
**Rationale**: 无状态、可直接分享链接、不依赖 React state/context 跨页传递
**Alternatives considered**:
- React context/zustand store：增加状态管理复杂度
- sessionStorage：刷新后丢失
- POST 中间 API 生成 prefill token：过度设计
