# Tasks: LLM Connectivity and Impact Localization Hardening

**Input**: Design documents from `specs/003-llm-impact-hardening/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-contracts.md, quickstart.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US3)

## Phase 1: Setup

**Purpose**: 对齐 Speckit 状态并补齐目录文档

- [x] T001 [US3] 将 `.specify/feature.json` 指向 `specs/003-llm-impact-hardening`
- [x] T002 [US3] 补齐 `specs/AGENTS.md` 与 `specs/003-llm-impact-hardening/AGENTS.md`
- [x] T003 [US3] 生成 `spec.md`、`plan.md`、`research.md`、`data-model.md`、`contracts/api-contracts.md`、`quickstart.md`、`checklists/review.md`

**Checkpoint**: 新特性目录完整，可被 Speckit 脚本解析

---

## Phase 2: User Story 1 — 本地 Ollama 草稿生成可直接工作 (Priority: P1) 🎯 MVP

**Goal**: 收敛 LLM 配置解析与路由使用路径，修复草稿生成连接失败

**Independent Test**: 裸 Ollama 模型名 + app settings 驱动的草稿生成与状态检查回归测试通过

### Implementation

- [x] T004 [US1] 修改 `src/harnetics/llm/client.py`，支持 Ollama 模型名归一化、统一 api_base 解析、模型存在性检查与可诊断错误包装
- [x] T005 [US1] 修改 `src/harnetics/api/routes/draft.py`，通过 `request.app.state.settings` 注入 `HarneticsLLM` 到 `DraftGenerator`
- [x] T006 [US1] 修改 `src/harnetics/api/routes/status.py`，让 `llm_available` 使用相同的 model/api_base 解析语义
- [x] T007 [US1] 新增 `tests/test_llm_client.py`，锁定模型归一化与 availability 逻辑

**Checkpoint**: `/api/draft/generate` 与 `/api/status` 对裸 Ollama 模型配置行为一致

---

## Phase 3: User Story 2 — 影响分析能定位具体受影响章节 (Priority: P1)

**Goal**: 入库生成 section-aware 边，分析时优先走边定位并兼容旧图

**Independent Test**: fixture 驱动的影响分析返回非空 `affected_sections`

### Implementation

- [x] T008 [US2] 修改 `src/harnetics/graph/indexer.py`，在章节级抽取引用、生成 `source_section_id`，并在可推断时填充 `target_section_id`
- [x] T009 [US2] 修改 `src/harnetics/engine/impact_analyzer.py`，使用 section-aware 边优先定位章节，并对旧边启用内容锚点 fallback
- [x] T010 [US2] 扩展 `tests/test_e2e_mvp_scenario.py`，锁定章节级影响定位与草稿路由配置传递场景

**Checkpoint**: 影响分析报告对至少一个下游文档返回非空 `affected_sections`

---

## Phase 4: Polish & Validation

**Purpose**: 文档/地图同步与验证收尾

- [x] T011 [US3] 更新受影响目录 `AGENTS.md`（根目录、`src/harnetics/llm`、`src/harnetics/api`、`src/harnetics/graph`、`src/harnetics/engine`、`tests`）
- [x] T012 [US3] 运行目标 pytest 回归，并确认 `tasks.md` 状态与实现一致
- [x] T013 [US3] 将本次会话决策沉淀到 `docs/daily/2026-04-11.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: 无依赖，立即开始
- **Phase 2**: 依赖 Phase 1
- **Phase 3**: 依赖 Phase 1，可与 Phase 2 并行，但最终需要共同验证
- **Phase 4**: 依赖 Phase 2 与 Phase 3

### User Story Dependencies

- **US1 (P1)**: 无业务前置依赖，是 MVP 主修复路径之一
- **US2 (P1)**: 依赖现有图谱入库与分析链路，但不依赖 US1 完成
- **US3 (P2)**: 在所有实现完成后收尾