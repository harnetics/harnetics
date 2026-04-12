# Tasks: OpenAI-compatible LLM 调用收敛

**Input**: Design documents from `/specs/005-openai-compatible-llm-client/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: 不单独采用 TDD 阶段拆分，但每个用户故事都必须补齐对应回归验证。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 为 OpenAI-compatible 客户端切换准备依赖与操作说明。

- [X] T001 Add OpenAI SDK dependency and refresh lockfile in pyproject.toml and uv.lock
- [X] T002 Update OpenAI-compatible operator examples in .env.example and README.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 收敛配置解析与统一 LLM 路由决策，阻断隐式回退分叉。

- [X] T003 Refine .env source resolution and shared AI route selection helpers in src/harnetics/config.py, src/harnetics/llm/client.py, and src/harnetics/graph/embeddings.py
- [X] T004 Align legacy compatibility path with the shared LLM route semantics in src/harnetics/llm/client.py and src/harnetics/app.py

**Checkpoint**: 所有 LLM 入口在进入用户故事前共用同一套配置解析与路由判定。

---

## Phase 3: User Story 1 - 云端网关直接生成草稿 (Priority: P1) 🎯 MVP

**Goal**: 草稿生成通过 OpenAI-compatible 网关直接使用原始模型名完成远端调用。

**Independent Test**: 仅配置网关地址、API key 和原始模型名后，`POST /api/draft/generate` 可以成功完成，并在状态端点体现远端 effective route。

- [X] T005 [US1] Implement OpenAI-compatible remote chat completion path in src/harnetics/llm/client.py
- [X] T006 [US1] Persist requested/effective model metadata for generated drafts in src/harnetics/engine/draft_generator.py and src/harnetics/api/routes/draft.py
- [X] T007 [US1] Add regression coverage for remote draft generation and raw-model pass-through in tests/test_llm_client.py and tests/test_env_routing.py

**Checkpoint**: 仅完成本阶段后，远端草稿生成已可单独演示。

---

## Phase 4: User Story 2 - AI 辅助分析复用同一路由 (Priority: P1)

**Goal**: 影响分析中的 AI 判定与草稿生成复用一致的远端语义，并输出同等级诊断错误。

**Independent Test**: 在同一组网关配置下分别触发草稿生成和影响分析，两者都使用相同 effective model/base；远端失败时都返回不含密钥的诊断错误。

- [X] T008 [US2] Reuse the OpenAI-compatible client in impact-analysis AI judging and align remote embedding routing in src/harnetics/engine/impact_analyzer.py, src/harnetics/api/routes/impact.py, and src/harnetics/graph/embeddings.py
- [X] T009 [US2] Normalize draft and impact API error surfaces around effective route diagnostics in src/harnetics/api/routes/draft.py and src/harnetics/llm/client.py
- [X] T010 [US2] Extend workflow regressions for shared route behavior in tests/test_e2e_mvp_scenario.py and tests/test_app.py

**Checkpoint**: 仅完成本阶段后，草稿生成与影响分析对同一远端配置表现一致。

---

## Phase 5: User Story 3 - 运行时路由可观测 (Priority: P2)

**Goal**: 工程师能直接通过状态接口确认服务进程实际使用的模型、基地址与配置来源。

**Independent Test**: 服务启动后访问 `/api/status`，可直接读到配置模型名、effective route 和配置文件来源，且从仓库子目录启动时仍正确。

- [X] T011 [US3] Expose and normalize runtime AI route diagnostics in src/harnetics/api/routes/status.py and src/harnetics/config.py
- [X] T012 [US3] Update runtime-diagnostics regression coverage in tests/test_app.py and tests/test_e2e_mvp_scenario.py

**Checkpoint**: 仅完成本阶段后，工程师不依赖 shell 探针也能定位服务进程实际路由。

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 文档、特性闭环状态与验证收尾。

- [X] T013 Update feature docs and maps in AGENTS, README, `.env.example`, and docs/daily/2026-04-12.md to match the final OpenAI-compatible completion/embedding implementation
- [X] T014 Run targeted validation from specs/005-openai-compatible-llm-client/quickstart.md and record completion in specs/005-openai-compatible-llm-client/tasks.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: No dependencies - can start immediately
- **Phase 2**: Depends on Phase 1 - blocks all user stories
- **Phase 3**: Depends on Phase 2 - MVP
- **Phase 4**: Depends on Phase 3 because it reuses the new client behavior
- **Phase 5**: Depends on Phase 2 and can land after Phase 3/4 diagnostics stabilize
- **Phase 6**: Depends on all prior phases

### User Story Dependencies

- **US1**: Starts after Foundational phase completion
- **US2**: Depends on US1 because impact analysis must reuse the new client contract
- **US3**: Depends on Foundational phase completion and should be finalized after US1/US2 expose stable diagnostics

### Parallel Opportunities

- T001 and T002 can proceed in parallel
- T011 and T012 can proceed after T003 once the shared route helpers stabilize

## Implementation Strategy

### MVP First (US1)

1. Complete Setup
2. Complete Foundational
3. Complete US1
4. Validate remote draft generation

### Incremental Delivery

1. Add OpenAI-compatible draft generation
2. Reuse the same route in impact analysis
3. Finalize runtime observability and docs

### Notes

- Every completed task must be marked `[X]` in this file.
- Do not silently reintroduce local fallback for remote configuration errors.
- Error text may include effective model/base but must not expose API keys.

## Validation Record

- 2026-04-12: Ran `.venv/bin/python -m pytest tests/test_llm_client.py tests/test_graph_store.py tests/test_env_routing.py tests/test_app.py tests/test_e2e_mvp_scenario.py -q` → `42 passed, 16 warnings in 17.91s`