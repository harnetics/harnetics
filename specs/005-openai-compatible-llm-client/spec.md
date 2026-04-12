# Feature Specification: OpenAI-compatible LLM 调用收敛

**Feature Branch**: `005-openai-compatible-llm-client`  
**Created**: 2026-04-12  
**Status**: Implemented  
**Input**: User description: "先分批commit 现有根仓子仓的变更，然后请你直接跑完 speckit 的闭环（从 specify-implement），记得采用 sub-agent 模式。调用 AI 逻辑直接改成采用 OpenAI-compatible 格式，并支持 aihubmix 这类 `/v1/chat/completions` 网关与原始模型名；后续补充 embedding 调用示例，要求向量路径也对齐该语义。"

## User Scenarios & Testing

### User Story 1 - 云端网关直接生成草稿 (Priority: P1)

产品工程师为草稿生成配置一个 OpenAI-compatible 网关后，系统直接按该网关的通用会话接口发起请求，而不是再依赖特定 provider 前缀或本地模型路由语义。工程师只需填写网关地址、API key 和原始模型名，就能触发草稿生成。

**Why this priority**: 这是当前阻塞问题的根因。只要远端调用语义还依赖 LiteLLM 专属 provider/model 约定，实际运行时就会持续出现误路由、错误模型名或难以诊断的本地回退。

**Independent Test**: 将系统配置为 OpenAI-compatible 网关、原始模型名和有效凭证后，单独调用草稿生成接口，验证响应成功且状态接口显示远端 effective route，而不是本地 Ollama 路由。

**Acceptance Scenarios**:

1. **Given** 工程师配置了 OpenAI-compatible 网关地址、API key 和原始模型名 `claude-sonnet-4-6`, **When** 用户触发草稿生成, **Then** 系统使用该网关完成生成，不要求用户手工补 provider 前缀。
2. **Given** 工程师将模型切换为具有更强推理能力的原始模型名 `claude-sonnet-4-6-think`, **When** 用户再次触发草稿生成, **Then** 系统直接把该模型名传给网关，且无需改代码。

---

### User Story 2 - AI 辅助分析复用同一远端调用语义 (Priority: P1)

变更影响分析中的 AI 判定、向量粗筛与草稿生成复用同一套远端 AI 调用规则。用户不希望草稿生成走远端，而影响分析仍然悄悄退回本地模型、另一套 embedding 协议或另一套不一致的调用语义。

**Why this priority**: 如果同一产品中的两条 AI 工作流使用不同调用语义，故障会变成“部分页面正常、部分页面仍走本地”的隐性分叉，维护成本很高，也很难向用户解释。

**Independent Test**: 在同一组远端配置下，分别触发一次草稿生成和一次影响分析，验证 completion 与 embedding 都成功使用同源 OpenAI-compatible 配置，并且错误信息保持一致的诊断粒度。

**Acceptance Scenarios**:

1. **Given** 系统已配置 OpenAI-compatible 网关和原始模型名, **When** 用户发起影响分析并触发 AI 判定, **Then** 影响分析复用与草稿生成一致的远端调用语义。
2. **Given** 网关拒绝当前模型或凭证无效, **When** 用户触发草稿生成或影响分析, **Then** 系统返回包含 effective model 与 effective base 的可诊断错误，而不会误报为本地模型异常。
3. **Given** 系统为向量检索配置了远端 embedding 模型 `jina-embeddings-v5-text-small`, **When** 用户触发依赖向量检索的影响分析或搜索路径, **Then** 系统直接按 OpenAI-compatible embeddings 接口发送该原始模型名，而不是要求 provider 前缀或继续走 LiteLLM 特有语义。

---

### User Story 3 - 运行时路由可观测 (Priority: P2)

工程师在排查 AI 路由问题时，需要从系统状态页面直接看到服务进程实际使用的模型名、基地址和配置来源，而不是只能依赖 shell 中的局部探针结果。

**Why this priority**: 当前问题之所以难排查，是因为“shell 里看到的配置”和“服务进程实际生效的配置”可能不是同一个视图。没有运行时可观测性，修复成本会持续偏高。

**Independent Test**: 启动服务后单独调用状态接口，验证返回的模型名、基地址和配置来源与当前服务进程实际生效的配置一致。

**Acceptance Scenarios**:

1. **Given** 服务已启动, **When** 工程师请求系统状态, **Then** 响应中包含配置模型名、effective model、effective base 和配置文件来源路径。
2. **Given** 服务从仓库子目录或热重载子进程启动, **When** 工程师请求系统状态, **Then** 仍能确认当前进程命中的配置来源，而不会因为启动目录变化失去可诊断性。

### Edge Cases

- 配置了远端网关但模型名不存在时，系统应快速返回可诊断错误，而不是静默改走本地模型。
- 配置了远端网关但缺少或失效的 API key 时，系统应阻止调用并给出清晰原因。
- 未配置远端网关时，系统仍应允许显式本地模型路径继续工作，避免破坏现有离线联调场景。
- 服务从仓库子目录、热重载子进程或测试临时目录启动时，配置解析仍应稳定命中预期 `.env`。

## Requirements

### Functional Requirements

- **FR-001**: 系统 MUST 支持以 OpenAI-compatible 语义直接调用远端 LLM 网关，并使用原始模型名而非 provider 前缀字符串。
- **FR-002**: 草稿生成 MUST 复用同一套 OpenAI-compatible 远端调用语义，并允许仅通过配置切换标准模型与推理增强模型。
- **FR-003**: 影响分析中的 AI 判定 MUST 与草稿生成复用相同的远端调用规则，不得出现一条工作流走远端、另一条工作流悄悄回退到本地默认模型的分叉。
- **FR-003**: 影响分析中的 AI 判定与其依赖的远端 embedding 调用 MUST 与草稿生成复用同源 OpenAI-compatible 配置，不得出现一条工作流走远端、另一条工作流悄悄回退到本地默认模型或旧协议的分叉。
- **FR-004**: 系统 MUST 继续支持显式本地模型配置，以保持离线或本地联调场景的可用性。
- **FR-005**: 状态接口 MUST 返回运行时实际生效的模型名、基地址和配置来源，以支持排查误路由问题。
- **FR-006**: 远端调用失败时，系统 MUST 返回可诊断错误，至少包含 effective model 与 effective base，但不得泄漏 API key。
- **FR-007**: 系统 MUST 支持通过环境配置切换不同的 OpenAI-compatible 模型名，包括普通模型与推理增强模型，而无需改代码。
- **FR-008**: 示例配置与运行文档 MUST 明确说明如何配置 OpenAI-compatible 网关、原始模型名和本地 fallback。
- **FR-009**: 当系统配置远端 embedding 模型时，MUST 通过 OpenAI-compatible `embeddings` 接口发送原始 embedding 模型名，并保留 embedding base 的可观测性。

### Key Entities

- **AI Route Config**: 描述服务进程当前使用的模型名、基地址、认证信息来源与本地/远端模式。
- **Effective AI Route Snapshot**: 状态接口暴露的运行时路由快照，用于诊断服务进程实际采用的模型与配置来源。
- **LLM Invocation Result**: 统一描述草稿生成与影响分析 AI 判定的成功结果或可诊断错误。
- **Embedding Route Snapshot**: 描述向量检索路径当前使用的 embedding 模型名、base_url 与本地/远端模式。

## Success Criteria

### Measurable Outcomes

- **SC-001**: 在配置 OpenAI-compatible 网关后，草稿生成与影响分析两条 AI 工作流都能在单次演示中成功完成，且 completion/embedding 使用一致的远端配置语义，状态接口显示相同的 effective route 视图。
- **SC-002**: 工程师将模型从标准模型切换到推理增强模型时，仅修改配置即可生效，切换过程不需要代码变更。
- **SC-003**: 当远端模型名或凭证错误时，工程师可在 5 分钟内仅通过状态接口和错误响应定位实际生效的模型与基地址。
- **SC-004**: 未启用远端网关的本地联调场景继续可用，不因新远端调用语义而被破坏。

## Assumptions

- 当前特性收敛远端 AI 主路径：completion 直接走 OpenAI-compatible 会话接口，embedding 在配置远端模型时同步走 OpenAI-compatible embeddings 接口；本地 sentence-transformers 与显式 Ollama 路径继续保留。
- 目标网关遵循标准 OpenAI-compatible 会话接口，并接受原始模型名作为 `model` 字段。
- 现有草稿生成、影响分析和状态接口仍然是本特性的主要验收入口。
- 远端网关的认证方式继续采用单个 API key，不额外引入多步鉴权流程。