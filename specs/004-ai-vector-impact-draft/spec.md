# Feature Specification: AI 向量驱动的影响分析与草稿联动

**Feature Branch**: `004-ai-vector-impact-draft`  
**Created**: 2026-04-11  
**Status**: Draft  
**Input**: 变更影响分析接入 AI 向量分析，实现环境变量配置（本地/云端 LLM、向量模型），影响分析精准定位受影响章节，影响报告→草稿台自动填写联动，草稿台候选文档向量筛选

## User Scenarios & Testing

### User Story 1 - AI 向量驱动的精准影响分析 (Priority: P1)

用户点击"分析影响"后，系统通过 AI 大模型（而非纯规则/BFS 遍历）对受影响章节做语义级精准定位。当前实现中 `_find_affected_sections` 在 heuristic fallback 时会把下游文档几乎所有章节都列为受影响（如截图所示，DOC-TPL-001 所有 19 个 section 均被标记），等同于没有分析。新方案：将变更章节内容与下游文档各章节做向量相似度比对 + LLM 语义判定，仅保留真正相关的章节。

**Why this priority**: 这是核心痛点——影响分析是产品的核心价值主张，当前输出过于宽泛等同无效。不解决这个问题，后续所有功能（草稿联动、质量评分）都建立在噪声数据之上。

**Independent Test**: 上传含明确追溯关系的上下游文档（如 DOC-SYS-001 → DOC-TST-003），触发影响分析后，受影响章节数量应显著少于文档总章节数，且均与变更内容语义相关。

**Acceptance Scenarios**:

1. **Given** 文档 DOC-FMA-001 升级到 v3.1 且仅修改了第 4 章"动力系统故障模式", **When** 用户触发影响分析, **Then** 下游文档 DOC-TST-001 的受影响章节仅包含与动力系统测试直接相关的 3-5 个章节，而非全部 20+ 章节
2. **Given** 影响分析完成, **When** 用户查看报告详情, **Then** 每个受影响章节附带 1 句话的影响理由说明（AI 生成）
3. **Given** 向量索引尚未构建或模型不可用, **When** 用户触发影响分析, **Then** 系统优雅降级到当前 heuristic 模式并提示"AI 分析不可用，已使用规则引擎"

---

### User Story 2 - 影响报告→草稿台自动联动 (Priority: P2)

在影响分析报告页面，用户点击某个受影响文档卡片上的"生成对齐草稿"按钮后，系统自动跳转到草稿台并预填写：草稿主题（基于影响报告上下文自动生成）、来源文档（自动勾选触发文档 + 受影响文档关联的上游文档）。用户确认后直接点击"生成"即可开始写草稿，无需手动重复输入。

**Why this priority**: 当前从影响报告到草稿台的流程是断裂的——点击"生成对齐草稿"后跳到空白草稿台，用户需要重新输入主题和手动选择文档。这个体验断层让整个工作流失去连贯性。

**Independent Test**: 在影响报告页面点击某个受影响文档的"生成对齐草稿"，验证草稿台已预填主题和来源文档列表。

**Acceptance Scenarios**:

1. **Given** 影响报告显示 DOC-TST-001 受 DOC-FMA-001 变更影响, **When** 用户点击 DOC-TST-001 卡片上的"生成对齐草稿", **Then** 跳转到草稿台，主题已填写"DOC-TST-001 对齐更新：响应 DOC-FMA-001 v3.1 变更"，来源文档已自动勾选 DOC-FMA-001 和 DOC-TST-001
2. **Given** 草稿台预填信息已就绪, **When** 用户直接点击"开始生成", **Then** 草稿生成流程启动，无需用户做任何额外操作

---

### User Story 3 - 草稿台候选文档向量检索 (Priority: P2)

草稿台"步骤二：候选来源文档"当前直接返回全部文档（如截图所示 10 篇全部列出），用户需要人工逐个扫描选择。新方案：基于草稿主题描述做向量语义检索，仅返回与主题最相关的候选文档（top-K），并按相关度排序展示。

**Why this priority**: 当候选文档从 10 篇扩展到 50、100 篇时，无筛选的列表将完全不可用。向量检索是让草稿台在规模化场景中保持可用性的基础能力。

**Independent Test**: 在草稿台输入一个具体主题（如"涡轮泵性能试验"），验证返回的候选文档列表是语义相关的子集（而非全部文档），且排在前面的文档与主题相关度最高。

**Acceptance Scenarios**:

1. **Given** 数据库中有 10 篇文档, **When** 用户在草稿台输入主题"涡轮泵性能试验大纲", **Then** 候选文档列表按相关度排序，最相关的 DOC-TST-002（涡轮泵试验相关）排在最前，与主题无关的文档（如 DOC-ICD-001 接口文档）排在末尾或不显示
2. **Given** 向量检索已返回候选列表, **When** 用户查看结果, **Then** 每个文档附带一个相关度分数标签（如 0.92），帮助用户判断选择

---

### User Story 4 - 环境变量配置：本地/云端 LLM 与向量模型 (Priority: P1)

用户通过项目根目录的 `.env` 文件统一配置 LLM 提供商（本地 Ollama / 云端 OpenAI/Anthropic/DeepSeek 等）和 embedding 向量模型（本地 sentence-transformers / 云端 OpenAI embeddings）。系统在启动时读取配置，运行时按配置路由到对应模型提供商。

**Why this priority**: 这是 US1 和 US3 的基础设施前提——没有可配置的模型路由，AI 分析就无法接入云端大模型（本地小模型能力不足以做精准语义判定）。

**Independent Test**: 修改 `.env` 中的 `HARNETICS_LLM_PROVIDER` 和 `HARNETICS_EMBEDDING_MODEL`，重启服务后验证 `/api/status` 返回正确的模型配置信息。

**Acceptance Scenarios**:

1. **Given** `.env` 配置 `HARNETICS_LLM_MODEL=deepseek/deepseek-chat` 和 `HARNETICS_LLM_API_KEY=sk-xxx`, **When** 系统启动, **Then** LLM 调用路由到 DeepSeek API 而非本地 Ollama
2. **Given** `.env` 配置 `HARNETICS_EMBEDDING_MODEL=text-embedding-3-small` 和 `HARNETICS_EMBEDDING_API_KEY=sk-xxx`, **When** 文档导入触发向量索引, **Then** 使用 OpenAI embedding API 生成向量而非本地 sentence-transformers
3. **Given** 未配置任何 `.env` 或环境变量, **When** 系统启动, **Then** 默认使用本地 Ollama + 本地 sentence-transformers（向后兼容）
4. **Given** 配置了云端 LLM 但 API key 无效, **When** 系统启动, **Then** `/api/status` 返回 `llm_available: false` 并附带错误信息

---

### Edge Cases

- 向量索引尚未构建时（新安装或空数据库），影响分析和草稿检索优雅降级到非向量模式
- 云端 LLM API 调用超时（>30s），返回清晰错误信息并建议切换到本地模型
- embedding 模型维度不匹配（云端 vs 本地切换时 ChromaDB collection 维度冲突），系统检测并提示用户重建索引
- 影响报告→草稿台联动时，如果影响报告已过期（文档又更新了），提示用户"源报告可能已过时"

## Requirements

### Functional Requirements

- **FR-001**: 影响分析 `_find_affected_sections` 支持向量相似度比对模式：将变更章节 embedding 与下游文档各章节 embedding 做余弦相似度，阈值过滤（默认 0.7）
- **FR-002**: 影响分析在向量粗筛后调用 LLM 做语义精判：给定变更内容和候选章节，LLM 判定是否真正受影响，并输出影响理由
- **FR-003**: 影响分析结果中 `affected_sections` 包含 `reason` 字段（AI 生成的 1 句话影响说明）
- **FR-004**: 草稿台"步骤二"候选文档改为调用向量检索 API `GET /api/documents/search?q={topic}&top_k=10`，按相关度排序返回
- **FR-005**: 草稿台候选文档列表每项附带 `relevance_score`（0-1 浮点数），前端展示为相关度标签
- **FR-006**: 影响报告→草稿台联动：点击"生成对齐草稿"传递参数（trigger_doc_id, impacted_doc_id, report_id），草稿台据此自动填写主题和预选文档
- **FR-007**: `.env` 文件支持配置 `HARNETICS_LLM_MODEL`、`HARNETICS_LLM_API_KEY`、`HARNETICS_LLM_BASE_URL`
- **FR-008**: `.env` 文件支持配置 `HARNETICS_EMBEDDING_MODEL`、`HARNETICS_EMBEDDING_API_KEY`、`HARNETICS_EMBEDDING_BASE_URL`
- **FR-009**: `Settings` dataclass 新增 embedding 配置字段，`get_settings()` 读取环境变量并支持 `.env` 文件加载（python-dotenv）
- **FR-010**: `EmbeddingStore` 支持云端 embedding 提供商（通过 litellm.embedding 或 OpenAI client），根据配置自动选择本地/云端
- **FR-011**: `/api/status` 返回当前 LLM 和 embedding 模型名称及可用性状态
- **FR-012**: 向量分析不可用时自动降级到现有 heuristic 模式，并在 API 响应中标记 `analysis_mode: "heuristic"` 或 `"ai_vector"`

### Non-Functional Requirements

- **NFR-001**: 向量检索响应时间 < 2 秒（10 篇文档、每篇 20 章节规模）
- **NFR-002**: LLM 语义判定单次调用超时 30 秒，总影响分析流程超时 120 秒
- **NFR-003**: 云端 API key 不得出现在日志或错误响应中

## Success Criteria

1. 影响分析受影响章节数量从"≈文档全部章节"降低到"≤30% 文档总章节数"（在标准 fixture 语料上验证）
2. 草稿台候选文档列表从"返回全部"变为"返回 top-K 相关子集"，且排序与主题语义相关
3. 影响报告→草稿台一键预填，用户零输入即可开始生成草稿
4. 系统支持通过 `.env` 在本地 Ollama 和云端 DeepSeek/OpenAI 之间无缝切换，无需改代码

## Assumptions

- litellm 已支持 embedding API 路由（litellm.embedding()），无需额外依赖
- ChromaDB 支持自定义 embedding function，可替换为云端调用
- 现有 fixture 文档（10 篇）足以验证向量检索和影响分析精准度
- python-dotenv 作为新依赖引入，用于 `.env` 文件加载

## Key Entities

| Entity | Description |
|--------|-------------|
| `Settings` | 运行时配置，新增 embedding_api_key、embedding_base_url、embedding_model 字段 |
| `EmbeddingStore` | 向量存储，支持本地/云端 embedding 提供商切换 |
| `ImpactAnalyzer` | 影响分析引擎，新增 AI 向量分析路径 |
| `ImpactedDoc.affected_sections` | 从 `list[str]` 扩展为包含 reason 的结构 |
| `DraftPrefill` | 新增实体，承载影响报告→草稿台的预填参数 |
