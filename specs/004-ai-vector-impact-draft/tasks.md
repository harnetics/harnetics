# Tasks: AI 向量驱动的影响分析与草稿联动

**Input**: Design documents from `/specs/004-ai-vector-impact-draft/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api-contracts.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US4)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 环境配置基础设施，US1/US3/US4 的共同前提

- [ ] T001 添加 python-dotenv 依赖到 pyproject.toml 并在 `get_settings()` 入口调用 `load_dotenv()` — `pyproject.toml`, `src/harnetics/config.py`
- [ ] T002 扩展 Settings dataclass 新增 `embedding_api_key`、`embedding_base_url`、`llm_api_key` 字段，`get_settings()` 读取对应环境变量 — `src/harnetics/config.py`
- [ ] T003 [P] 创建 `.env.example` 模板文件，列出所有可配置环境变量及说明 — `.env.example`
- [ ] T004 [P] 更新 `.gitignore` 确保 `.env` 文件不被提交 — `.gitignore`

**Checkpoint**: 配置基础设施就绪

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: EmbeddingStore 云端支持，所有向量相关 US 的基础

- [ ] T005 [US4] 重构 `EmbeddingStore._build_ef()` 支持云端 embedding：检测 model_name 含 `/` 则使用 litellm.embedding() 包装，否则保持本地 SentenceTransformer — `src/harnetics/graph/embeddings.py`
- [ ] T006 [US4] `EmbeddingStore.__init__()` 接受 `api_key` 和 `base_url` 可选参数，传递给云端 embedding function — `src/harnetics/graph/embeddings.py`
- [ ] T007 [US4] 更新 `api/app.py` lifespan 中 EmbeddingStore 初始化，从 settings 传入 embedding 配置 — `src/harnetics/api/app.py`
- [ ] T008 [US4] 扩展 `/api/status` 返回 `embedding_available`、`embedding_model`、`sections_indexed` — `src/harnetics/api/routes/status.py`

**Checkpoint**: 云端 embedding 路由可用 + 状态可查

---

## Phase 3: User Story 1 — AI 向量影响分析 (Priority: P1) 🎯 MVP

**Goal**: 影响分析使用向量粗筛 + LLM 精判，精准定位受影响章节

**Independent Test**: 触发影响分析后 affected_sections 数量 < 文档总章节数 30%

- [ ] T009 [US1] 扩展 `ImpactedDoc` 模型：`affected_sections` 从 `list[str]` 改为 `list[AffectedSection]`（含 section_id, heading, reason），新增 `analysis_mode` 字段 — `src/harnetics/models/impact.py`
- [ ] T010 [US1] 在 `ImpactAnalyzer` 中新增 `_ai_vector_find_affected_sections()` 方法：(1) 取变更章节 embedding 与下游文档各章节 embedding 做余弦相似度，阈值 0.65 过滤；(2) 候选章节送 LLM 做语义精判，输出 bool + reason — `src/harnetics/engine/impact_analyzer.py`
- [ ] T011 [US1] 修改 `_find_affected_sections()` 入口：有 embedding_store 时走 AI 路径，无则保持 heuristic 降级 — `src/harnetics/engine/impact_analyzer.py`
- [ ] T012 [US1] `ImpactAnalyzer.__init__()` 接受 `embedding_store` 和 `llm` 可选参数 — `src/harnetics/engine/impact_analyzer.py`
- [ ] T013 [US1] 更新 `api/routes/impact.py`：构造 ImpactAnalyzer 时注入 embedding_store 和 llm，响应体包含 `analysis_mode` — `src/harnetics/api/routes/impact.py`
- [ ] T014 [US1] 更新前端 `ImpactReport.tsx`：`affected_sections` 渲染支持 object 格式（显示 heading + reason），兼容旧 string 格式 — `frontend/src/pages/ImpactReport.tsx`
- [ ] T015 [US1] 更新前端 TypeScript 类型定义 `ImpactedDoc.affected_sections` — `frontend/src/types/index.ts`

---

## Phase 4: User Story 3 — 草稿台向量检索 (Priority: P2)

**Goal**: 草稿台候选文档从"全部返回"变为向量语义检索 top-K

**Independent Test**: 输入特定主题后返回的候选文档数量 < 全部文档数且按相关度排序

- [ ] T016 [US3] 新增 `GET /api/documents/search` 路由：接收 `q` 和 `top_k` 参数，调用 EmbeddingStore 做文档级向量检索，返回 `DocumentSearchResult[]` — `src/harnetics/api/routes/documents.py`
- [ ] T017 [US3] `EmbeddingStore` 新增 `search_documents()` 方法：对查询做 section 级向量检索后按 doc_id 聚合取最高分，返回文档级结果 — `src/harnetics/graph/embeddings.py`
- [ ] T018 [US3] 更新前端 `DraftNew.tsx` 步骤二：将 `fetchDocuments()` 替换为 `searchDocuments(topic)` 调用，按 relevance_score 排序展示 — `frontend/src/pages/DraftNew.tsx`
- [ ] T019 [US3] 前端 `api.ts` 新增 `searchDocuments(q, topK)` 函数 — `frontend/src/lib/api.ts`
- [ ] T020 [US3] 前端候选文档卡片展示 `relevance_score` 标签 — `frontend/src/pages/DraftNew.tsx`

---

## Phase 5: User Story 2 — 影响报告→草稿台联动 (Priority: P2)

**Goal**: 从影响报告一键跳转到草稿台，自动预填主题和来源文档

**Independent Test**: 点击"生成对齐草稿"后草稿台已预填，无需手动输入

- [ ] T021 [US2] 更新前端 `ImpactReport.tsx`"生成对齐草稿"按钮：导航到 `/draft?trigger_doc_id=X&impacted_doc_id=Y&report_id=Z` — `frontend/src/pages/ImpactReport.tsx`
- [ ] T022 [US2] 更新前端 `DraftNew.tsx`：从 URL searchParams 读取预填参数，自动生成 subject、预选 related_doc_ids、跳过步骤一直接到步骤二 — `frontend/src/pages/DraftNew.tsx`
- [ ] T023 [US2] 后端 `POST /api/draft/generate` request body 新增可选 `source_report_id` 字段 — `src/harnetics/api/routes/draft.py`

---

## Phase 6: Polish & Cross-Cutting

**Purpose**: 测试、文档、降级保护

- [ ] T024 添加 `test_ai_vector_impact_analysis` 测试：mock LLM 和 embedding，验证 AI 路径返回精简的 affected_sections 含 reason — `tests/test_impact_analyzer.py`
- [ ] T025 [P] 添加 `test_document_search` 测试：验证向量检索端点返回排序结果 — `tests/test_document_search.py`
- [ ] T026 [P] 添加 `test_draft_prefill` 测试：验证预填参数正确传递 — `tests/test_e2e_mvp_scenario.py`
- [ ] T027 [P] 添加 `test_settings_dotenv` 测试：验证 .env 加载和 embedding 配置 — `tests/test_config.py`
- [ ] T028 运行全量 `pytest tests/ -q` 确保所有测试通过
- [ ] T029 [P] 更新 AGENTS.md 文档（根目录 + 受影响模块）

---

## Dependencies

```
Phase 1 (T001-T004) → Phase 2 (T005-T008) → Phase 3 (T009-T015)
                                            → Phase 4 (T016-T020)
                                            → Phase 5 (T021-T023)
All phases → Phase 6 (T024-T029)
```

## Parallel Execution

- T003 ∥ T004（不同文件）
- T005 ∥ T008（不同文件，但 T008 需 T007）
- T009 可独立开始（模型定义）
- T016 ∥ T021（不同 US，不同文件）
- T024 ∥ T025 ∥ T026 ∥ T027（独立测试文件）
