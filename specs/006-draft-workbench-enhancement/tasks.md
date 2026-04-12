# Tasks: 草稿工作台增强

**Input**: Design documents from `specs/006-draft-workbench-enhancement/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup

**Purpose**: 安装新前端依赖

- [x] T001 安装 react-markdown + remark-gfm 到 frontend/package.json

---

## Phase 2: Foundational (后端评估映射 + 引用回填)

**Purpose**: 后端核心逻辑变更，阻塞所有前端用户故事

- [x] T002 [P] 在 src/harnetics/api/routes/draft.py 的 generate_draft 端点中，生成完成后内联调用 EvaluatorBus.run_all()，将评估结果与草稿一起持久化，并基于评估结果设定 status
- [x] T003 [P] 在 src/harnetics/api/routes/draft.py 的 generate_draft 响应中添加 eval_results 数组和 created_at 字段，eval_results 中 level 值映射为 "Pass"/"Warning"/"Blocker"
- [x] T004 [P] 在 src/harnetics/engine/draft_generator.py 的 _parse_citations 后，查询 graph store 回填每条 Citation 的 quote 字段为章节 heading + 内容前 200 字符
- [x] T005 在 src/harnetics/api/routes/draft.py 的 list_drafts 端点中，扩展返回 subject（从 request_json 提取）和 eval_summary（从 eval_results_json 统计 pass/warn/block 计数）

**Checkpoint**: 后端 API 契约就绪，前端故事可并行开始

---

## Phase 3: User Story 2 - Markdown 渲染预览 (Priority: P1) 🎯 MVP

**Goal**: 草稿内容以 Markdown 格式渲染而非纯文本

**Independent Test**: 打开草稿详情页，确认标题/列表/代码块正确渲染

- [x] T006 [P] [US2] 创建 frontend/src/components/MarkdownRenderer.tsx，封装 react-markdown + remark-gfm，配置 Tailwind prose 样式
- [x] T007 [US2] 修改 frontend/src/pages/DraftShow.tsx，将 `<pre>` 内容区替换为 MarkdownRenderer 组件

**Checkpoint**: 草稿内容 Markdown 渲染可用

---

## Phase 4: User Story 1+3 - 评估结果结构化展示 (Priority: P1)

**Goal**: 评估结果按 Pass/Warning/Blocker 三级分类展示，生成后自动可用

**Independent Test**: 生成草稿后侧栏立即显示评估统计和详情

- [x] T008 [US1] 修改 frontend/src/types/index.ts，确认 EvalResult.level 类型兼容 "Pass"/"Warning"/"Blocker" 新值
- [x] T009 [US1] 修改 frontend/src/pages/DraftShow.tsx 的评估结果卡片，确保读取 generate 响应中的 eval_results 并正确渲染三级分类

**Checkpoint**: 评估结果在草稿详情页结构化展示

---

## Phase 5: User Story 4 - 引用来源章节内容定位 (Priority: P2)

**Goal**: 引用列表显示章节标题和内容摘要

**Independent Test**: 草稿详情页引用列表每条显示非空的章节内容而非空白

- [x] T010 [US4] 修改 frontend/src/pages/DraftShow.tsx 的引用来源卡片，当 quote 为空时显示"原始内容不可用"，有内容时渲染 heading + 摘要

**Checkpoint**: 引用来源有实际内容展示

---

## Phase 6: User Story 5 - 导出草稿为 Markdown 文件 (Priority: P2)

**Goal**: 导出按钮触发浏览器下载 .md 文件

**Independent Test**: 点击导出按钮后浏览器下载文件

- [x] T011 [US5] 修改 frontend/src/pages/DraftShow.tsx 的导出按钮 onClick，使用 fetch + Blob + URL.createObjectURL 调用 /api/draft/{id}/export 触发下载

**Checkpoint**: 导出功能可用

---

## Phase 7: User Story 6 - 历史草稿列表与状态标注 (Priority: P2)

**Goal**: 提供历史草稿列表页，展示所有草稿及状态

**Independent Test**: 访问 /drafts 显示所有历史草稿，每条带状态徽章

- [x] T012 [P] [US6] 扩展 frontend/src/types/index.ts 中 DraftSummary 类型，添加 subject 和 eval_summary 字段
- [x] T013 [P] [US6] 创建 frontend/src/pages/DraftHistory.tsx 历史草稿列表页，调用 fetchDrafts 渲染卡片列表（draft_id、subject、generated_by、created_at、状态徽章）
- [x] T014 [US6] 在 frontend/src/App.tsx 中添加 /drafts 路由指向 DraftHistory 页面，并在导航中添加入口

**Checkpoint**: 历史草稿列表页可访问且显示完整

---

## Phase 8: Polish & Cross-Cutting

**Purpose**: 回归验证与收尾

- [x] T015 运行 uv run pytest tests/ -x -q 验证后端回归 ✅ 69 passed, 0 failed
- [x] T016 运行 quickstart.md 中的验证清单确认全部功能正常 ✅ tsc --noEmit OK, vite build OK

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 无依赖，立即开始
- **Phase 2 (Foundational)**: 依赖 Phase 1（需要 react-markdown 但后端不用）
- **Phase 3-7 (User Stories)**: 全部依赖 Phase 2 后端完成
  - Phase 3 (Markdown 渲染) 可与 Phase 4-7 并行
  - Phase 4 (评估展示) 依赖后端 eval_results 字段
  - Phase 5 (引用定位) 依赖后端 quote 回填
  - Phase 6 (导出) 独立可并行
  - Phase 7 (历史列表) 依赖后端 subject + eval_summary
- **Phase 8 (Polish)**: 所有故事完成后

### Parallel Opportunities

- T002, T003, T004 后端修改可同时进行（不同函数/区域）
- T006, T012, T013 前端新文件可并行创建
- T007, T009, T010, T011 修改 DraftShow.tsx 不同区域可顺序快速完成

---

## Implementation Strategy

**MVP**: Phase 1-3 (Setup + Backend + Markdown 渲染) 即可交付最小可用改进
**Full delivery**: Phase 1-8 全部完成，覆盖 6 个用户故事

## Validation Record

| 日期 | 命令 | 结果 |
|------|------|------|
| _待填_ | `uv run pytest tests/ -x -q` | _待运行_ |
