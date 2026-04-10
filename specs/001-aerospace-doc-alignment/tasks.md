# Tasks: Aerospace Document Alignment Product

**Input**: Design documents from `/specs/001-aerospace-doc-alignment/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Organization**: Tasks grouped by user story (P1 → P2 → P3) to enable independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description with file path`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[USn]**: Which user story this task belongs to

---

## Phase 1: Setup (Project Skeleton)

**Purpose**: Project directories, dependencies, configuration — zero business logic

- [ ] T001 Create project directory structure per plan.md layout in `src/harnetics/` (models/, parsers/, graph/, engine/, evaluators/, llm/, api/routes/, web/templates/, cli/)
- [ ] T002 Configure `pyproject.toml` with all dependencies: fastapi, jinja2, uvicorn, python-multipart, litellm, chromadb, sentence-transformers, pyyaml, typer, rich, httpx, ruff, pytest, pytest-asyncio
- [ ] T003 [P] Create `src/harnetics/config.py` with global settings (DB path `var/harnetics.db`, chromadb path `var/chroma/`, Ollama URL, embedding model name, LLM model name, server port)
- [ ] T004 [P] Create `src/harnetics/web/static/css/app.css` with Tailwind CDN + DaisyUI CDN link scaffold
- [ ] T005 [P] Create `src/harnetics/web/static/js/htmx.min.js` placeholder (CDN fallback in base template)
- [ ] T006 [P] Create `src/harnetics/web/templates/base.html` with Tailwind/DaisyUI CDN, HTMX CDN, nav bar (首页/文档库/草稿台/变更影响/图谱), Chinese UI shell

**Checkpoint**: `pip install -e .` succeeds, `python -c "import harnetics"` works

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: DB schema, base models, shared infrastructure — MUST complete before any user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Create SQLite DDL script in `src/harnetics/graph/schema.sql` with all 7 tables (documents, sections, edges, icd_parameters, versions, drafts, impact_reports) and 7 indexes per data-model.md
- [ ] T008 Implement `src/harnetics/graph/store.py` — SQLite connection manager with `init_db()` (run schema.sql), `get_connection()` context manager, foreign keys enabled
- [ ] T009 [P] Implement `src/harnetics/models/document.py` — dataclasses: `DocumentNode`, `Section`, `DocumentEdge` matching documents/sections/edges table schemas
- [ ] T010 [P] Implement `src/harnetics/models/icd.py` — dataclass: `ICDParameter` matching icd_parameters table schema
- [ ] T011 [P] Implement `src/harnetics/models/draft.py` — dataclasses: `DraftRequest`, `AlignedDraft`, `Citation`, `Conflict` matching drafts table + JSON sub-schemas
- [ ] T012 [P] Implement `src/harnetics/models/impact.py` — dataclasses: `ImpactReport`, `ImpactedDoc`, `SectionDiff` matching impact_reports table + JSON sub-schemas
- [ ] T013 Implement `src/harnetics/api/app.py` — FastAPI app factory, mount static files, include API routers + web router, Jinja2 template config, lifespan (init_db on startup)
- [ ] T014 Implement `src/harnetics/api/deps.py` — dependency injection: `get_db()`, `get_graph_store()`, `get_llm_client()`, `get_chroma_client()`
- [ ] T015 Create empty `__init__.py` files for all packages: models, parsers, graph, engine, evaluators, llm, api, api/routes, web, cli
- [ ] T016 Create test scaffold: `tests/conftest.py` with tmp_path fixtures, in-memory SQLite, fixture doc paths

**Checkpoint**: `pytest tests/conftest.py` passes, DB initializes with all 7 tables, FastAPI app starts on empty state

---

## Phase 3: US1 — 文档库导入与浏览 (P1) 🎯 MVP

**Goal**: Import Markdown/YAML fixture docs, auto-parse sections, extract ICD params, build relation edges, browse/filter/search via Web UI

**Independent Test**: Upload 10 fixture docs → all indexed with correct sections, ICD params extracted, ≥15 edges created, filterable by department/type/level

### Parsers

- [ ] T017 [P] [US1] Implement `src/harnetics/parsers/markdown_parser.py` — `parse_markdown(content: str, doc_id: str) -> list[Section]`: split by heading regex (`^#{1,6}\s`), extract heading/content/level/order_index
- [ ] T018 [P] [US1] Implement `src/harnetics/parsers/yaml_parser.py` — `parse_yaml(content: str) -> dict`: safe_load wrapper with error handling for malformed YAML
- [ ] T019 [P] [US1] Implement `src/harnetics/parsers/icd_parser.py` — `parse_icd_yaml(content: str, doc_id: str) -> list[ICDParameter]`: validate ICD schema (parameters list), extract param_id/name/interface_type/subsystem_a/b/value/unit/range/owner_department

### Graph Store Operations

- [ ] T020 [US1] Implement CRUD in `src/harnetics/graph/store.py` — `insert_document()`, `insert_sections()`, `insert_edges()`, `insert_icd_parameters()`, `get_document()`, `get_documents(filters)`, `get_sections(doc_id)`, `delete_document(doc_id)` with CASCADE, `search_documents(q)`
- [ ] T021 [US1] Implement `src/harnetics/graph/indexer.py` — `ingest_document(file_path, metadata) -> DocumentNode`: orchestrator that reads file, detects format (md/yaml), calls parser, inserts document + sections, runs relation extraction, inserts edges; for ICD files also calls icd_parser and inserts params
- [ ] T022 [US1] Implement relation extraction in `src/harnetics/graph/indexer.py` — `extract_relations(doc_id, content) -> list[DocumentEdge]`: regex scan for `DOC-[A-Z]{3}-\d{3}` references, infer relation type by doc_type pairs (design→requirement = traces_to, any→ICD = constrained_by, etc.), confidence=1.0 for exact match

### Embeddings

- [ ] T023 [US1] Implement `src/harnetics/graph/embeddings.py` — `EmbeddingStore`: init chromadb persistent client, `index_sections(doc_id, sections)` with metadata {doc_id, section_id, heading, doc_type, department}, `search_similar(query, filters, top_k) -> list[Section]`

### API Routes

- [ ] T024 [US1] Implement `src/harnetics/api/routes/documents.py` — `POST /api/documents/upload` (multipart: file + metadata fields per documents-api contract), `GET /api/documents` (query params: department, doc_type, system_level, status, q, page, per_page), `GET /api/documents/{doc_id}` (detail with sections + upstream/downstream), `DELETE /api/documents/{doc_id}`, `GET /api/documents/{doc_id}/sections`
- [ ] T025 [P] [US1] Implement ICD param routes in `src/harnetics/api/routes/documents.py` — `GET /api/icd/parameters`, `GET /api/icd/parameters/{param_id}`

### Web Templates

- [ ] T026 [US1] Implement `src/harnetics/web/templates/documents/list.html` — document table with filter dropdowns (department, doc_type, system_level), search input, HTMX-powered filtering (`hx-get`), upload button link
- [ ] T027 [P] [US1] Implement `src/harnetics/web/templates/documents/upload.html` — drag-drop zone, metadata form fields (doc_id, title, doc_type, department, system_level, engineering_phase, version, is_icd checkbox), HTMX form submit to `/api/documents/upload`
- [ ] T028 [P] [US1] Implement `src/harnetics/web/templates/documents/detail.html` — metadata card, sections accordion, upstream/downstream doc lists with relation type and confidence badges
- [ ] T029 [US1] Add document routes to `src/harnetics/web/routes.py` — `GET /documents` (list page), `GET /documents/{doc_id}` (detail page), `GET /documents/upload` (upload page)

**Checkpoint**: `harnetics ingest ./fixtures/ --recursive` imports 10 docs, `/documents` shows filterable list, `/documents/DOC-ICD-001` shows 12 ICD params, ≥15 relation edges visible in detail pages

---

## Phase 4: US6 — Evaluator 质量门 (P1)

**Goal**: 8 quality evaluators (EA.1-5, EB.1, ED.1, ED.3) with BaseEvaluator + EvaluatorBus pattern, block/warn levels, export gate

**Independent Test**: Feed a mock draft with pre-planted issues → verify EA.1-5, EB.1, ED.1, ED.3 each produce correct pass/fail/warn results

### Evaluator Framework

- [ ] T030 [US6] Implement `src/harnetics/evaluators/base.py` — `EvalLevel` enum (block/warn), `EvalStatus` enum (pass/fail/warn/skip), `EvalResult` dataclass, `BaseEvaluator` ABC with `evaluate(draft, graph) -> EvalResult`, `EvaluatorBus` class with `register()`, `run_all(draft, graph) -> list[EvalResult]`, `has_blocking_failures(results) -> bool`

### Citation Evaluators (EA.1–EA.5)

- [ ] T031 [P] [US6] Implement `src/harnetics/evaluators/citation.py` — `EA1_CitationCompleteness`: regex match paragraphs with numbers/params, check 📎 marker exists → block
- [ ] T032 [P] [US6] Implement EA.2 in `src/harnetics/evaluators/citation.py` — `EA2_CitationReality`: extract DOC-XXX-XXX from citations, verify each exists in documents table → block
- [ ] T033 [P] [US6] Implement EA.3 in `src/harnetics/evaluators/citation.py` — `EA3_VersionFreshness`: compare cited version vs documents table latest non-Superseded version → warn
- [ ] T034 [P] [US6] Implement EA.4 in `src/harnetics/evaluators/citation.py` — `EA4_NoCyclicReferences`: DFS cycle detection on edges table → block
- [ ] T035 [P] [US6] Implement EA.5 in `src/harnetics/evaluators/citation.py` — `EA5_CoverageRate`: count technical paragraphs (containing numbers) / paragraphs with citations, threshold ≥80% → warn

### ICD Evaluator (EB.1)

- [ ] T036 [P] [US6] Implement `src/harnetics/evaluators/icd.py` — `EB1_ICDConsistency`: extract param name+value from draft text, cross-check against icd_parameters table values → block

### AI Quality Evaluators (ED.1, ED.3)

- [ ] T037 [P] [US6] Implement `src/harnetics/evaluators/ai_quality.py` — `ED1_NoFabrication`: every number in draft must trace back to a source document section → block
- [ ] T038 [P] [US6] Implement ED.3 in `src/harnetics/evaluators/ai_quality.py` — `ED3_ConflictMarked`: each entry in conflicts list must have corresponding ⚠️ marker in draft body → block

### Evaluate API

- [ ] T039 [US6] Implement `src/harnetics/api/routes/evaluate.py` — `POST /api/evaluate/{draft_id}` (optional `evaluators` query param for selective run), `GET /api/evaluate/results/{eval_id}` per evaluate-api contract

**Checkpoint**: Unit test with mock draft → all 8 evaluators return expected results, `POST /api/evaluate/{draft_id}` returns full result set, `has_blocking_failures` correctly gates export

---

## Phase 5: US2 — 对齐草稿生成 (P1)

**Goal**: LLM-powered draft generation with retrieval → context assembly → generation → citation parsing → conflict detection → evaluator gate, Web UI 3-step workspace

**Independent Test**: Generate draft for "TQ-12 热试车测试大纲" with 10 fixture docs → draft covers 8 template chapters, 100% citations point to real docs, ≥1 conflict detected, evaluator results displayed

### LLM Client

- [ ] T040 [P] [US2] Implement `src/harnetics/llm/client.py` — `HarneticsLLM` class: litellm.completion wrapper for `ollama/gemma4:26b-it-a4b-q4_K_M`, temperature=0.3, max_tokens=8192, `generate_draft(system_prompt, context, user_request) -> str`, `check_availability() -> bool`
- [ ] T041 [P] [US2] Implement `src/harnetics/llm/prompts.py` — `DRAFT_SYSTEM_PROMPT` (strict rules: 📎 citation format, no fabrication, ⚠️ conflict marking, template adherence, Chinese output), `build_context(sections, icd_params, template) -> str`

### Draft Engine

- [ ] T042 [US2] Implement `src/harnetics/engine/draft_generator.py` — `DraftGenerator.generate(request: DraftRequest) -> AlignedDraft`: orchestrate retrieval (chromadb similarity + metadata filter) → extract ICD constraints → assemble LLM context → call LLM → parse citations from output (`[📎 DOC-XXX-XXX §X.X]` regex) → return AlignedDraft
- [ ] T043 [US2] Implement `src/harnetics/engine/conflict_detector.py` — `ConflictDetector.detect(related_docs, icd_params) -> list[Conflict]`: cross-compare parameter values across doc pairs, flag version mismatches, return Conflict objects with doc_a/doc_b/value_a/value_b/resolution

### Draft API

- [ ] T044 [US2] Implement `src/harnetics/api/routes/draft.py` — `POST /api/draft/generate` (accept DraftRequest JSON, return full draft with citations + conflicts + eval_results per draft-api contract), `GET /api/draft/{draft_id}`, `GET /api/drafts` (list), `GET /api/draft/{draft_id}/export` (markdown download, 403 if blocking evaluators fail)

### Web Templates

- [ ] T045 [US2] Implement `src/harnetics/web/templates/draft/workspace.html` — Step 1: config form (department/doc_type/system_level dropdowns, subject textarea, parent_doc/template selects, auto-retrieved related docs checklist), HTMX submit
- [ ] T046 [US2] Implement `src/harnetics/web/templates/draft/progress.html` — Step 2: progress tracker with HTMX polling (`hx-get` every 3s), status stages (检索→提取ICD→生成中→校验中)
- [ ] T047 [US2] Implement `src/harnetics/web/templates/draft/result.html` — Step 3: two-column layout (left: draft content with 📎 and ⚠️ markers, right: citation panel with source snippets), evaluator result bar at bottom, export button (disabled if blocked)
- [ ] T048 [US2] Add draft routes to `src/harnetics/web/routes.py` — `GET /draft` (workspace), `GET /draft/{draft_id}` (result page)

**Checkpoint**: Full draft generation flow works end-to-end via Web UI, citations link to real docs, conflicts detected, evaluator panel shows 8 results

---

## Phase 6: US3 — 变更影响分析 (P2)

**Goal**: Analyze document version changes, identify affected downstream docs with Critical/Major/Minor severity, generate impact report

**Independent Test**: Simulate modifying DOC-ICD-001 thrust param → system identifies 4 affected docs with correct severity levels

### Impact Engine

- [ ] T049 [US3] Implement `src/harnetics/engine/impact_analyzer.py` — `ImpactAnalyzer.analyze(doc_id, old_version, new_version) -> ImpactReport`: diff changed sections between versions, query downstream docs via edges (BFS with depth tracking), compute severity (depth=1 + constrained_by/traces_to = Critical, depth=2 or references = Major, depth≥3 = Minor), generate summary

### Impact API

- [ ] T050 [US3] Implement `src/harnetics/api/routes/impact.py` — `POST /api/impact/analyze` (accept doc_id + optional old/new version per impact-api contract), `GET /api/impact/{report_id}`, `GET /api/impact/{report_id}/export` (markdown report download)

### Web Templates

- [ ] T051 [P] [US3] Implement `src/harnetics/web/templates/impact/analyze.html` — doc selector dropdown, version selectors (old/new), "分析影响" button, HTMX submit
- [ ] T052 [P] [US3] Implement `src/harnetics/web/templates/impact/report.html` — changed params diff table (old→new with color coding), affected docs table (doc_id, department, severity badge 🔴🟡🟢, affected sections, recommendation), export button
- [ ] T053 [US3] Add impact routes to `src/harnetics/web/routes.py` — `GET /impact` (analyze page), `GET /impact/{report_id}` (report page)

**Checkpoint**: Impact analysis for DOC-ICD-001 returns 4 affected docs (3 Critical, 1 Major), report page renders correctly, export produces valid markdown

---

## Phase 7: US4 — 文档图谱可视化 (P2)

**Goal**: Interactive vis-network.js graph showing all document nodes and relation edges, filterable by department/level, clickable nodes

**Independent Test**: Load 10 fixture docs → graph renders 10 nodes + ≥15 edges, ICD node centered, department colors correct, node click shows detail popup

### Graph Query

- [ ] T054 [US4] Implement `src/harnetics/graph/query.py` — `DocumentGraph` class: `get_full_graph(department?, system_level?) -> dict` (vis-network format: nodes with id/label/title/group/shape/size, edges with from/to/label/dashes/arrows, groups with department colors), `get_upstream(doc_id, depth) -> list`, `get_downstream(doc_id, depth) -> list`, `get_stale_references() -> list`, `get_related(doc_id) -> list`

### Graph API

- [ ] T055 [US4] Implement `src/harnetics/api/routes/graph.py` — `GET /api/graph` (full graph with optional department/system_level filters per graph-api contract), `GET /api/graph/upstream/{doc_id}`, `GET /api/graph/downstream/{doc_id}`, `GET /api/graph/stale`, `GET /api/graph/related/{doc_id}`

### Web Template

- [ ] T056 [US4] Implement `src/harnetics/web/templates/graph/view.html` — vis-network.js CDN include, canvas container, department/level filter dropdowns (HTMX-triggered reload), JS: fetch `/api/graph` → render network, node click handler → detail popup card, ICD node physics config (central gravity), department color legend
- [ ] T057 [US4] Create `src/harnetics/web/static/js/graph.js` — vis-network initialization, node/edge rendering options, click event handlers, filter update logic
- [ ] T058 [US4] Add graph route to `src/harnetics/web/routes.py` — `GET /graph` (graph view page)

**Checkpoint**: `/graph` renders interactive network with 10 nodes, ICD centered, department colors, node click shows popup, department filter works

---

## Phase 8: US5 — 系统仪表盘 (P3)

**Goal**: Dashboard homepage with aggregate stats (doc count, edge count, stale refs), recent activity timeline, evaluator pass rate, document health indicators

**Independent Test**: With 10 docs + 1 draft → dashboard shows accurate counts, timeline shows recent ops, health bars render

### Status Aggregation

- [ ] T059 [US5] Implement `src/harnetics/api/routes/status.py` — `GET /api/status` per status-api contract: query document/section/edge/icd_param/draft counts, stale reference count (via query.get_stale_references), Ollama health check (litellm ping), chromadb indexed count, DB file size, recent activity log (last 10 operations from a simple activity_log table or derived from timestamps), eval pass rate from latest draft

### Web Template

- [ ] T060 [US5] Implement `src/harnetics/web/templates/index.html` — stat cards (文档/关系/过期引用), quick action buttons (生成新草稿/变更影响分析), recent activity timeline (HTMX auto-refresh), document health progress bars (citation freshness / ICD consistency / citation coverage), Evaluator pass rate summary
- [ ] T061 [US5] Add index route to `src/harnetics/web/routes.py` — `GET /` (dashboard/index page, fetches status data and renders template)

**Checkpoint**: Homepage shows accurate stats matching actual DB state, timeline updates after operations

---

## Phase 9: Polish & Integration

**Purpose**: CLI, Docker, end-to-end validation, README

- [ ] T062 Implement `src/harnetics/cli/main.py` — typer CLI: `init` (create var/ dir, run schema.sql), `init --reset` (drop + recreate), `ingest <path>` (single file or recursive directory import via indexer), `serve` (uvicorn with configurable host/port)
- [ ] T063 [P] Create `docker-compose.yml` at project root — services: `harnetics` (build from Dockerfile, mount var/, expose 8080), `ollama` (ollama/ollama image, GPU passthrough, model auto-pull)
- [ ] T064 [P] Create `Dockerfile` at project root — Python 3.12-slim base, install project via pip, copy src/ and fixtures/, entrypoint harnetics serve
- [ ] T065 End-to-end smoke test in `tests/test_e2e/test_mvp_scenario.py` — programmatic: init DB → ingest 10 fixtures → verify 10 docs + ≥15 edges + 12 ICD params → generate draft (mock LLM if no GPU) → run evaluators → verify results → run impact analysis → verify 4 affected docs
- [ ] T066 Update `README.md` at project root — installation (pip + Ollama), quickstart (init → ingest → serve), smoke test commands, CLI reference, Docker Compose usage, link to fixtures/ and specs/

**Checkpoint**: Full MVP scenario passes end-to-end, Docker build succeeds, README covers all entry points

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup ──────────→ Phase 2: Foundational ─────→ Phase 3: US1 (P1)
                                                   │
                                                   ├──→ Phase 4: US6 (P1) ──→ Phase 5: US2 (P1)
                                                   │                                    │
                                                   ├──→ Phase 6: US3 (P2) ◄─────────────┘ (US2 optional but US1 required)
                                                   │
                                                   ├──→ Phase 7: US4 (P2) (only needs US1 data)
                                                   │
                                                   └──→ Phase 8: US5 (P3) (needs US1 + any downstream data)
                                                                    │
                                                   Phase 9: Polish ◄┘ (after all desired stories)
```

### Critical Path

```
Setup → Foundational → US1 (parsers + store + indexer + embeddings + API + web)
                            → US6 (evaluator framework + 8 evaluators)
                                 → US2 (LLM + draft generator + conflict detector + web)
```

### User Story Dependencies

| Story | Depends On | Why |
|-------|-----------|-----|
| US1 (文档库) | Phase 2 only | Data foundation — no story dependency |
| US6 (Evaluator) | US1 (documents + edges + icd_parameters in DB) | Evaluators query document graph |
| US2 (草稿生成) | US1 (retrieval source) + US6 (quality gate) | Draft needs docs; must run evaluators |
| US3 (影响分析) | US1 (edges for downstream traversal) | BFS over document graph |
| US4 (图谱可视化) | US1 (nodes + edges data) | Renders document graph |
| US5 (仪表盘) | US1 (counts) | Aggregates from all tables |

### Parallel Opportunities Per Phase

**Phase 1**: T003, T004, T005, T006 all parallel (different files)
**Phase 2**: T009, T010, T011, T012 all parallel (model files); T015 parallel with all
**Phase 3**: T017, T018, T019 parallel (parser files); T025, T027, T028 parallel; T023 parallel with API work
**Phase 4**: T031–T038 all parallel (independent evaluator implementations)
**Phase 5**: T040, T041 parallel (LLM files); T045, T046, T047 parallel (template files)
**Phase 6**: T051, T052 parallel (template files)
**Phase 7**: T056, T057 parallel (template + JS)
**Phase 9**: T063, T064 parallel (Docker files)

---

## Parallel Example: Phase 4 (Evaluators)

```bash
# All 8 evaluator implementations are independent — maximum parallelism:
T031: EA1_CitationCompleteness   in evaluators/citation.py
T032: EA2_CitationReality        in evaluators/citation.py
T033: EA3_VersionFreshness       in evaluators/citation.py
T034: EA4_NoCyclicReferences     in evaluators/citation.py
T035: EA5_CoverageRate           in evaluators/citation.py
T036: EB1_ICDConsistency         in evaluators/icd.py
T037: ED1_NoFabrication          in evaluators/ai_quality.py
T038: ED3_ConflictMarked         in evaluators/ai_quality.py
# Note: T031-T035 share citation.py but implement distinct classes — no conflict
```

---

## Implementation Strategy

### MVP First (US1 + US6 + US2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: US1 — 文档库导入与浏览
4. Complete Phase 4: US6 — Evaluator 质量门
5. Complete Phase 5: US2 — 对齐草稿生成
6. **STOP and VALIDATE**: Full MVP scenario — import → draft → evaluate → export

### Incremental Delivery (P2/P3)

7. Phase 6: US3 — 变更影响分析 (P2)
8. Phase 7: US4 — 文档图谱可视化 (P2)
9. Phase 8: US5 — 系统仪表盘 (P3)
10. Phase 9: Polish — CLI + Docker + E2E + README

### Suggested Parallel Lanes (2 developers)

| Developer A | Developer B |
|-------------|-------------|
| Phase 1 + Phase 2 (together) | Phase 1 + Phase 2 (together) |
| Phase 3: US1 (parsers, store, indexer) | Phase 3: US1 (API routes, web templates) |
| Phase 4: US6 (EA.1-EA.5, EB.1) | Phase 4: US6 (ED.1, ED.3, bus, API) |
| Phase 5: US2 (LLM, draft engine) | Phase 5: US2 (web templates, draft API) |
| Phase 6: US3 | Phase 7: US4 |
| Phase 8: US5 | Phase 9: Polish |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [USn] label maps task to specific user story for traceability
- Each user story is independently testable at its checkpoint
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- ICD routes (T025) bundled in documents router to avoid single-endpoint files
- Evaluator implementations (T031-T038) share files by domain but implement independent classes
- Draft export gate (403) enforced in T044 using `EvaluatorBus.has_blocking_failures()`
