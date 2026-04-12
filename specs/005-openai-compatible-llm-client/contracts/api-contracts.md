# API Contracts: OpenAI-compatible LLM 调用收敛

## GET /api/status

**Purpose**: 暴露服务进程当前生效的 AI 路由视图。

**Response requirements**:

```json
{
  "llm_available": true,
  "llm_model": "claude-sonnet-4-6",
  "llm_base_url": "https://aihubmix.com/v1",
  "llm_effective_model": "openai/claude-sonnet-4-6",
  "llm_effective_base_url": "https://aihubmix.com/v1",
  "embedding_base_url": "https://aihubmix.com/v1",
  "config_env_file": "/abs/path/to/.env",
  "llm_error": ""
}
```

**Contract**:
- `llm_model` 返回配置中的原始模型名。
- `llm_effective_model` 返回服务内部判定的 effective route 标识。
- `embedding_base_url` 返回当前远端 embedding 所使用的基地址；未配置时可为空字符串。
- `config_env_file` 返回当前命中的环境文件路径；若无文件，则返回空字符串。
- 任何错误消息不得包含 API key。
- 在配置未变化的前提下，立即连续调用 `/api/status` 与 `/api/dashboard/stats` 应返回一致的 LLM 探测视图。

---

## POST /api/draft/generate

**Purpose**: 在 OpenAI-compatible 网关配置下完成草稿生成。

**Success contract**:
- 当配置远端 OpenAI-compatible 网关与有效原始模型名时，请求成功完成，不要求调用方传 provider 前缀。
- 切换为 `claude-sonnet-4-6-think` 这类推理增强模型名时，请求体中的 `model` 必须直接使用该原始值。

**Failure contract**:

```json
{
  "detail": "LLM generation failed for model=openai/claude-sonnet-4-6 api_base=https://aihubmix.com/v1: AuthenticationError: ..."
}
```

**Contract**:
- 错误必须包含 effective model 与 effective base。
- 错误不得包含 API key。
- 远端失败时不得静默回退到本地默认模型。

---

## POST /api/impact/analyze

**Purpose**: 影响分析中的 AI 判定复用与草稿生成相同的 LLM 路由语义。

**Contract**:
- 在相同远端配置下，其 effective model/base 与草稿生成保持一致。
- 若启用远端 ai_vector 路径，其 embedding 请求必须使用同源 OpenAI-compatible base，并直接发送原始 embedding 模型名。
- 当远端模型不可用时，错误上下文与草稿生成保持相同诊断粒度。
- 若未启用 AI 路径，系统可以继续使用现有非 AI 降级流程，但不得伪装为远端成功调用。