# Research: LLM Connectivity and Impact Localization Hardening

## Decision 1: 在 `llm.client` 内做 Ollama 模型名归一化

- Decision: 支持把 `gemma4:26b` 这类裸模型名归一化为 `ollama/gemma4:26b`
- Rationale: 用户当前 README 和实际使用方式都偏向裸模型名；把 provider 语义封在适配层，比要求调用方理解 LiteLLM 细节更稳妥
- Alternatives considered:
  - 只改 README，要求用户手工写 `ollama/` 前缀：不能解决已有配置和真实错误路径
  - 在每个路由单独修模型名：会再次制造分散逻辑

## Decision 2: 草稿路由显式使用应用设置构造 `HarneticsLLM`

- Decision: `api/routes/draft.py` 通过 `request.app.state.settings` 组装 `HarneticsLLM`，再注入 `DraftGenerator`
- Rationale: 当前 bug 的根因之一是路由直接 `DraftGenerator()`，把配置解析重新退回到默认构造路径
- Alternatives considered:
  - 在 `DraftGenerator` 内继续读取环境变量：无法保证与应用 settings 一致
  - 复用 legacy `DraftService`：会把 graph 栈和 legacy repository 栈重新耦合起来

## Decision 3: 章节定位需要同时修 indexer 和 analyzer

- Decision: 入库时生成 `source_section_id` 感知的边；分析时优先吃 section-aware 边，缺信息时再回退到文本信号匹配
- Rationale: 只改 analyzer 无法凭空创造章节信息；只改 indexer 又无法兼容已有旧边
- Alternatives considered:
  - 只在 analyzer 里做字符串匹配：对内部 section id 完全无效
  - 强制重建所有历史图谱：对当前 bugfix 太重，也不满足“直接跑完闭环”的交付要求

## Decision 4: target 锚点推断只做可解释的轻量启发式

- Decision: 只识别需求号、ICD 参数号、显式 `§3.2` 段落号和文档编号等稳定锚点
- Rationale: 这些锚点已存在于 fixture 文档，足够覆盖当前影响分析场景；再往上做语义匹配会把 bugfix 变成新项目
- Alternatives considered:
  - 引入 embeddings/LLM 做章节匹配：实现与验证成本过高，且会给影响分析增加不必要的不确定性

## Decision 5: 保持 API 结构不变，只增强返回内容质量

- Decision: 不新增端点，不改 JSON shape，只增强 `llm_available` 和 `affected_sections`
- Rationale: 前端已接入这些端点，保持契约稳定能避免无关回归