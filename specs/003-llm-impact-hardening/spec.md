# Feature Specification: LLM Connectivity and Impact Localization Hardening

**Feature Branch**: `003-llm-impact-hardening`
**Created**: 2026-04-11
**Status**: Draft
**Input**: User description: "请你直接跑完 speckit 的闭环（从 specify-implement），记得采用 sub-agent 模式。1. LLM 无法正常连接；2. 影响分析无法正常定位章节。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — 本地 Ollama 草稿生成可直接工作 (Priority: P1)

工程师已经启动本地 Ollama，并把 `HARNETICS_LLM_MODEL` 设为 `gemma4:26b`、`HARNETICS_LLM_BASE_URL` 设为 `http://localhost:11434`。进入草稿台后，点击生成草稿，请求能够使用当前应用配置成功调用 LLM；若模型未安装或端点异常，错误信息要明确指出模型和 base URL，而不是只返回模糊的 500。

**Why this priority**: 草稿生成是系统核心主路径；本地 Ollama 是当前默认开发方式，不能要求用户理解 LiteLLM provider 细节才能工作。

**Independent Test**: 用 `gemma4:26b` 这样的裸模型名启动 API，并通过路由触发草稿生成；验证应用将模型归一化到 Ollama provider、使用 app.state 的配置实例化 LLM 客户端，并在失败时返回可诊断错误上下文。

**Acceptance Scenarios**:

1. **Given** `HARNETICS_LLM_MODEL=gemma4:26b` 且 `HARNETICS_LLM_BASE_URL=http://localhost:11434`, **When** 用户调用 `POST /api/draft/generate`, **Then** 路由使用应用设置构造 LLM 客户端，并将模型按 Ollama 语义归一化后发起调用
2. **Given** Ollama 正在运行但请求的模型未安装, **When** 仪表盘调用 `GET /api/status`, **Then** `llm_available` 为 `false`，且判断基于目标模型是否存在而非仅仅 `/api/tags` 返回 200
3. **Given** LLM 请求失败, **When** 草稿生成返回错误, **Then** 响应包含可操作的诊断上下文（模型、base URL、原始异常类型）

---

### User Story 2 — 影响分析能定位具体受影响章节 (Priority: P1)

工程师上传需求文档、设计文档和测试大纲后，对上游文档发起影响分析。系统不仅要列出受影响文档，还要指出下游文档里哪些章节被波及，即使现有图谱里仍混有只到文档级的旧边，也要尽可能给出章节定位结果。

**Why this priority**: 仅知道“哪份文档受影响”还不够，真正的审查动作发生在章节级；没有章节定位，影响分析对工程决策帮助很有限。

**Independent Test**: 导入 fixture 文档后对 `DOC-SYS-001` 发起影响分析；验证 `DOC-DES-001` 或 `DOC-TST-003` 至少有一个非空 `affected_sections` 列表，并且章节来源于 section-aware 边或兼容旧图的内容信号匹配。

**Acceptance Scenarios**:

1. **Given** 下游文档的某个章节显式引用上游文档与其需求/参数锚点, **When** 系统建立图谱边, **Then** 存储的 edge 必须携带 `source_section_id`，且在可推断时携带 `target_section_id`
2. **Given** 上游文档发生变更, **When** 用户调用 `POST /api/impact/analyze`, **Then** 报告中的 `impacted_docs[].affected_sections` 优先基于 section-aware 边返回具体章节
3. **Given** 历史图谱边缺少 `target_section_id`, **When** 影响分析运行, **Then** 系统仍可基于章节文本中的引用信号和锚点做兼容性定位，而不是总是返回空数组

---

### User Story 3 — Spec Kit 闭环产物可审计 (Priority: P2)

维护者查看当前特性目录时，能够看到完整的 spec/plan/tasks/checklists/contracts/quickstart，并且 `tasks.md` 中的实现任务状态与实际代码一致。

**Why this priority**: 用户明确要求跑完 Speckit 闭环，这意味着文档工件本身也是交付物的一部分。

**Independent Test**: 检查 `specs/003-llm-impact-hardening/` 是否包含必需文档，并确认 `tasks.md` 的勾选状态与最终实现一致。

**Acceptance Scenarios**:

1. **Given** 进入 `specs/003-llm-impact-hardening/`, **When** 查看目录, **Then** 至少存在 `spec.md`、`plan.md`、`research.md`、`data-model.md`、`contracts/`、`quickstart.md`、`tasks.md` 和 `checklists/`
2. **Given** 实现已完成并验证通过, **When** 查看 `tasks.md`, **Then** 与本次改动对应的任务全部被标记为完成

### Edge Cases

- 模型名缺少 provider 前缀但 base URL 指向 Ollama 根地址或 `/v1` 地址
- API 进程存在全局 `OPENAI_BASE_URL`/`OPENAI_API_KEY`，但当前请求应优先使用 Harnetics 配置
- 图谱中的旧边只有文档级关系，没有任何 section id
- 指定 `changed_section_ids` 时，上游章节 ID 是内部 section id，下游文档不会直接出现该字符串
- YAML/ICD 文档章节粒度较粗，只能提供文档级或弱锚点级定位

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `POST /api/draft/generate` MUST 使用 `app.state.settings` 中的 `llm_model` 与 `llm_base_url` 构造本次请求的 LLM 客户端，而不是依赖隐式默认值
- **FR-002**: 系统 MUST 支持将 `gemma4:26b` 这类裸 Ollama 模型名归一化为 LiteLLM 可识别的 provider/model 形式
- **FR-003**: 当 provider 为 Ollama 时，LLM 可用性检查 MUST 同时验证 endpoint 可达和目标模型存在
- **FR-004**: 草稿生成失败时，错误信息 MUST 包含模型名、base URL 和原始异常类型，便于定位配置问题
- **FR-005**: 文档入库 MUST 在章节级扫描引用关系，并为命中的引用保存 `source_section_id`
- **FR-006**: 如果章节内容中能推断出目标锚点（如 `REQ-SYS-003`、`ICD-PRP-001`、`DOC-XXX §3.2`），系统 MUST 尽力推断并保存 `target_section_id`
- **FR-007**: 影响分析 MUST 优先使用 section-aware 边定位 `affected_sections`，仅在缺少足够边信息时才回退到内容信号匹配
- **FR-008**: 影响分析 MUST 继续沿 BFS 下游传播已有影响，不得因章节定位失败而中断整条依赖链
- **FR-009**: 系统 MUST 为 LLM 配置归一化、草稿路由配置传递、章节级边提取和影响定位添加回归测试
- **FR-010**: Speckit 闭环产物 MUST 与最终实现一致，并同步更新受影响目录的 `AGENTS.md`

### Key Entities

- **ResolvedLlmConfig**: 运行期 LLM 配置解析结果，包含归一化后的 `model`、有效 `api_base`、可选 `api_key` 与 provider 语义
- **SectionAwareEdge**: 文档图谱边，至少包含 `source_doc_id/source_section_id/target_doc_id/target_section_id/relation`，用于章节级影响传播
- **ReferenceSignal**: 从章节文本中抽取的引用锚点集合，例如需求号、ICD 参数号、显式 `§3.2` 段落号
- **LocalizedImpact**: 某份受影响文档上的定位结果，包含 `affected_sections`、命中的 relation、严重度与可追溯摘要

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 在 `HARNETICS_LLM_MODEL=gemma4:26b`、`HARNETICS_LLM_BASE_URL=http://localhost:11434` 的配置下，草稿生成路由的回归测试稳定通过，无需用户手工添加 `ollama/` 前缀
- **SC-002**: `GET /api/status` 在模型未安装时返回 `llm_available=false`，在模型存在时返回 `true`
- **SC-003**: 导入 fixture 文档后，对 `DOC-SYS-001` 发起影响分析时，至少一个下游文档返回非空 `affected_sections`
- **SC-004**: 与本特性相关的新增/修改 pytest 用例全部通过，且不回归现有 E2E 场景

## Assumptions

- 当前主工作流运行在 `src/harnetics/api/app.py`，legacy `src/harnetics/app.py` 继续保留但不作为本次 bug 的主修复入口
- 现有 graph schema 已具备 section-aware edge 所需字段，不需要新增表或做数据库迁移
- 旧图谱数据中可能已存在空 `source_section_id/target_section_id`，因此必须保留兼容性回退策略
- 本次修复以本地 Ollama 与已有 fixture 文档为主要验证路径，云端 provider 仅保证不被新逻辑破坏