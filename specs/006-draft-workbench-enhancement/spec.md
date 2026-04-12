# Feature Specification: 草稿工作台增强

**Feature Branch**: `006-draft-workbench-enhancement`
**Created**: 2026-04-12
**Status**: Draft
**Input**: 优化草稿工作台的 Markdown 渲染、评估结果适配、引用来源定位、导出功能修复与历史草稿列表

## User Scenarios & Testing

### User Story 1 - AI 输出结构化评估（告警/阻断标记） (Priority: P1)

用户生成草稿后，AI 返回的评估结果以结构化方式呈现——通过、告警、阻断三级分类独立展示，而非以纯文本嵌入草稿正文中。评估结果在侧栏卡片中按三类分组统计和列出。

**Why this priority**: 评估结果是草稿生产质量的核心判断依据。结构化呈现直接决定用户能否快速定位问题并采取行动。

**Independent Test**: 触发评估后，侧栏卡片中应显示通过/告警/阻断三类计数，每条评估规则应归入其中一类，且用户可展开查看每条的详细信息。

**Acceptance Scenarios**:

1. **Given** 草稿已成功生成, **When** 评估器运行完毕, **Then** 每条评估规则按 PASS/WARN/BLOCK 归类统计，侧栏概览卡片显示三类计数
2. **Given** 评估器返回 BLOCK 级别结果, **When** 用户查看详情标签页, **Then** 阻断条目以红色标识并附带具体位置描述
3. **Given** 评估器返回 WARN 级别结果, **When** 用户查看详情标签页, **Then** 告警条目以黄色标识并附带描述

---

### User Story 2 - 草稿内容 Markdown 渲染预览 (Priority: P1)

草稿内容预览区域从 `<pre>` 等宽字体改为 Markdown 格式渲染，支持标题、列表、加粗、引用块等常见标记，保留代码块和表格的正确排版。

**Why this priority**: 草稿本身就是 Markdown 格式输出，以 Markdown 渲染展示是基本的可读性需求，直接影响用户审查效率。

**Independent Test**: 在草稿预览区域输出包含标题、列表、加粗、代码块的 Markdown 内容，渲染后应正确显示为格式化文档而非纯文本。

**Acceptance Scenarios**:

1. **Given** 草稿内容包含 Markdown 标题和列表, **When** 在草稿详情页打开, **Then** 内容渲染为格式化 Markdown（标题有层级、列表有缩进）
2. **Given** 草稿内容包含代码块, **When** 在草稿详情页打开, **Then** 代码块以等宽字体和背景色正确显示
3. **Given** 草稿内容包含 `[📎 DOC-XXX-YYY §X.X]` 引注标记, **When** 渲染后, **Then** 引注标记作为行内元素可识别

---

### User Story 3 - 评估结果后端适配与统计 (Priority: P1)

评估路由在后端自动将 8 个 evaluator 的结果按 level (block/warn) 和 status (pass/fail/warn/skip) 映射为前端可消费的 "Pass" / "Warning" / "Blocker" 三类。草稿生成后自动触发评估（不再依赖手动 POST），评估结果随草稿一起返回。

**Why this priority**: 目前评估需要额外手动触发，且后端 level 字段 (block/warn) 与前端展示标签 (Pass/Warning/Blocker) 存在映射不一致。统一后端输出是消除前后端歧义的前提。

**Independent Test**: 调用草稿生成接口后，响应中应包含 eval_results 数组，每条结果带有 level 字段映射为 "Pass" / "Warning" / "Blocker" 之一。

**Acceptance Scenarios**:

1. **Given** POST /api/draft/generate 成功, **When** 响应返回, **Then** 响应体包含 eval_results 数组，每条具备 evaluator_id/name/status/level/detail
2. **Given** evaluator 返回 status=pass + level=block, **When** 前端收到, **Then** 该条显示为 "Pass"
3. **Given** evaluator 返回 status=fail + level=block, **When** 前端收到, **Then** 该条显示为 "Blocker"
4. **Given** evaluator 返回 status=fail + level=warn, **When** 前端收到, **Then** 该条显示为 "Warning"

---

### User Story 4 - 引用来源章节内容定位 (Priority: P2)

引用来源列表中，每条引用除了显示 source_doc_id 和 source_section_id 外，还应展示对应章节的实际标题和内容摘要，而非空白。用户点击引用可跳转到文档详情对应章节。

**Why this priority**: 引用来源的价值在于上下文溯源。当前空白 quote 字段使引用列表形同虚设，无法帮助用户理解来源。

**Independent Test**: 在草稿详情页的引用来源列表中，每条引用应显示章节标题和内容片段（前 200 字符），置信度百分比正确显示。

**Acceptance Scenarios**:

1. **Given** 草稿包含引用 DOC-FMA-001 §1, **When** 查看引用来源列表, **Then** 该条显示章节标题和前 200 字符的内容摘要
2. **Given** 引用的 section_id 在数据库中存在, **When** 后端返回引用数据, **Then** quote 字段包含实际章节内容片段
3. **Given** 引用的 section_id 不存在或已删除, **When** 后端返回引用数据, **Then** quote 字段显示"原始内容不可用"

---

### User Story 5 - 导出草稿为 Markdown 文件 (Priority: P2)

点击"导出草稿"按钮后，浏览器下载一个 `.md` 格式文件，文件名基于 draft_id，内容为草稿正文的完整 Markdown 文本。

**Why this priority**: 导出功能按钮已存在但无实际效果，属于已暴露的 UX 缺陷，修复成本低且用户期望明确。

**Independent Test**: 点击"导出草稿"按钮后，浏览器应下载名为 `{draft_id}.md` 的文件，文件内容与草稿正文完全一致。

**Acceptance Scenarios**:

1. **Given** 在草稿详情页, **When** 点击导出按钮, **Then** 浏览器触发 `.md` 文件下载，文件名为 `{draft_id}.md`
2. **Given** 草稿内容含中文, **When** 下载并打开文件, **Then** 编码正确（UTF-8），无乱码

---

### User Story 6 - 历史草稿列表与状态标注 (Priority: P2)

草稿工作台提供"历史草稿"列表页，展示所有已生成的草稿。每条草稿显示 draft_id、主题、生成时间、生成模型和当前状态（通过 / 告警 / 阻断 / 已完成），支持按时间倒序排列。用户可从列表进入任一草稿详情。

**Why this priority**: 无历史列表意味着用户生成草稿后无法回溯，所有过往工作隐形。这直接影响工作连续性和产品可用度。

**Independent Test**: 在草稿工作台导航中进入"历史草稿"，应看到按时间倒序排列的草稿列表，每条标注状态徽章，点击可跳转至详情页。

**Acceptance Scenarios**:

1. **Given** 数据库中有 N 条草稿记录, **When** 打开历史草稿列表, **Then** 显示 N 条记录，按 created_at 倒序排列
2. **Given** 某草稿 status 为 "blocked", **When** 显示在列表中, **Then** 带红色"阻断"徽章
3. **Given** 某草稿 status 为 "eval_pass", **When** 显示在列表中, **Then** 带绿色"通过"徽章
4. **Given** 某草稿 status 为 "completed"（未评估）, **When** 显示在列表中, **Then** 带灰色"已完成"徽章
5. **Given** 用户点击列表中某条草稿, **When** 路由跳转, **Then** 进入 /draft/{draft_id} 详情页

---

### Edge Cases

- 草稿内容为空字符串时，Markdown 渲染器应显示占位提示
- 评估器全部返回 SKIP 时，概览卡片应显示全零统计并附说明
- 引用章节在文档被删除后仍保持降级展示而非崩溃
- 历史列表为空时，显示引导用户创建首份草稿的提示

## Requirements

### Functional Requirements

- **FR-001**: 草稿详情页 MUST 将 content_md 渲染为格式化 Markdown 而非纯文本
- **FR-002**: 评估结果 MUST 将后端 status/level 组合映射为 "Pass" / "Warning" / "Blocker" 三类
- **FR-003**: 草稿生成接口 MUST 在生成完成后自动触发评估并在响应中包含 eval_results
- **FR-004**: 引用来源 MUST 在后端填充 quote 字段为对应章节的实际内容摘要
- **FR-005**: 导出按钮 MUST 触发浏览器下载 draft_id.md 文件
- **FR-006**: 系统 MUST 提供历史草稿列表页，展示所有草稿及其当前状态
- **FR-007**: 历史草稿列表 MUST 包含 draft_id、主题摘要、生成模型、创建时间和状态徽章
- **FR-008**: 后端草稿列表接口 MUST 返回 subject 字段供前端展示主题

### Key Entities

- **Draft**: 生成的对齐草稿，核心属性为 draft_id、content_md、status、citations、eval_results、generated_by、created_at
- **EvalResult**: 单个评估器的执行结果，核心属性为 evaluator_id、name、status、level、detail、locations
- **Citation**: 引用来源条目，核心属性为 source_doc_id、source_section_id、quote、confidence

## Success Criteria

### Measurable Outcomes

- **SC-001**: 草稿内容在详情页中以 Markdown 格式正确渲染，标题、列表、代码块均可识别
- **SC-002**: 评估结果按通过/告警/阻断三类统计正确，概览和详情两个视图数据一致
- **SC-003**: 引用来源列表中 100% 的有效引用显示章节标题和内容摘要
- **SC-004**: 导出按钮点击后浏览器在 2 秒内触发 .md 文件下载
- **SC-005**: 历史草稿列表正确显示所有已生成草稿，每条附带最新状态徽章
- **SC-006**: 草稿生成后无需手动触发评估即可在详情页查看评估结果

## Assumptions

- 前端已使用 React 18 + Vite + shadcn/ui 技术栈，Markdown 渲染引入 react-markdown + remark-gfm 即可
- 后端 evaluator bus 已实现 8 个评估器，评估接口稳定可靠
- 引用章节的 section_id 对应 graph store 中 sections 表的主键，可按 doc_id + section_id 查询
- 草稿列表接口已存在（GET /api/draft），仅需扩展返回字段
- 导出端点已存在（GET /api/draft/{id}/export），仅需前端接线下载逻辑
