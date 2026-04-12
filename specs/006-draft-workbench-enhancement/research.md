# Research: 草稿工作台增强

**Feature**: 006-draft-workbench-enhancement
**Date**: 2026-04-12

## Decision 1: Markdown 渲染方案

**Decision**: 使用 react-markdown + remark-gfm
**Rationale**: react-markdown 是 React 生态中最成熟的 Markdown 渲染库，remark-gfm 扩展支持 GFM 表格和任务列表。比 marked + dangerouslySetInnerHTML 更安全（默认不执行 HTML），在现有 shadcn/ui + Tailwind 体系中集成方便。
**Alternatives considered**:
- marked + rehype-sanitize: 需要额外 sanitize 步骤，react-markdown 内建安全
- @mdx-js/react: 过重，需要编译步骤，本场景不需要 JSX-in-Markdown
- 手写正则解析: 不现实，边界情况太多

## Decision 2: 评估结果 level 映射策略

**Decision**: 后端在 evaluate 路由中将 EvalResult 的 (status, level) 二元组映射为前端展示标签
- status=pass → "Pass"（不论 level）
- status=fail + level=block → "Blocker"
- status=fail + level=warn → "Warning"
- status=warn + level=warn → "Warning"
- status=skip → "Pass"（跳过视为通过）

**Rationale**: 前端目前按字符串 "Pass"/"Warning"/"Blocker" 渲染图标和颜色。后端统一映射消除了前端的条件判断复杂度，只需一个字段即可驱动全部展示。
**Alternatives considered**:
- 前端自行映射: 增加前端逻辑复杂度，且后端已有 EvalLevel/EvalStatus 语义
- 新增额外字段: 增加数据冗余，不如直接修改 level 输出

## Decision 3: 自动触发评估时机

**Decision**: 在 DraftGenerator.generate() 完成后、持久化之前，内联调用 EvaluatorBus.run_all()，将 eval_results 一起持久化
**Rationale**: 消除手动 POST /api/evaluate/{draft_id} 的额外步骤。生成和评估是单一原子操作，用户期望一次调用获得完整结果。评估器全部基于规则（无 LLM 调用），延迟可忽略（<100ms）。
**Alternatives considered**:
- 保持手动触发: 用户体验差，需要额外点击
- 异步后台任务: 过重，评估器本身极快无需异步

## Decision 4: 引用 quote 回填策略

**Decision**: 在 DraftGenerator._parse_citations() 解析出引用后，立即从 graph store 查询对应 section 的 heading + content 前 200 字符回填到 quote 字段
**Rationale**: 引用数据伴随草稿生成一次性确定。回填发生在持久化前，不增加额外 API 调用。200 字符截断平衡了摘要可读性和数据量。
**Alternatives considered**:
- 前端按需加载: 每条引用一个请求，N+1 问题
- 全量内容: 过大，引用可能有几十条，每条完整章节内容会使响应臃肿

## Decision 5: 历史草稿列表数据扩展

**Decision**: 扩展 GET /api/draft 列表接口，新增返回 subject 字段（从 request_json 中提取）和 eval_summary（pass/warn/block 计数对象）
**Rationale**: 列表页需要显示主题和状态摘要。subject 已存储在 request_json 中可直接提取，eval_summary 从 eval_results_json 按 level 统计。
**Alternatives considered**:
- 前端逐条 fetchDraft: 性能灾难
- 新增独立字段到 drafts 表: 需要 schema migration，不值得

## Decision 6: 导出实现方案

**Decision**: 前端导出按钮使用 fetch + Blob + URL.createObjectURL 触发下载，调用已有 GET /api/draft/{id}/export 端点
**Rationale**: 后端端点已存在且返回正确的 text/plain 响应。前端只需补充下载触发逻辑。不需要新增后端代码。
**Alternatives considered**:
- window.open(url): 简单但无法控制文件名
- 添加 Content-Disposition header: 需要修改后端，fetch+blob 方案纯前端解决
