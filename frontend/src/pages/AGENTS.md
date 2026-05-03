# pages/
> L2 | 父级: /frontend/src/AGENTS.md

成员清单
Dashboard.tsx: 仪表盘概览页，消费 /api/dashboard/stats。
Documents.tsx: 文档列表与筛选页。
DocumentDetail.tsx: 文档详情页，展示元数据/章节/关系。
DraftNew.tsx: 草稿创建工作台，支持向量搜索候选文档、关键词降级、相关度标签展示，以及由影响报告自动生成主题/预选来源文档。
DraftShow.tsx: 草稿详情与评估页，支持 Markdown 渲染、三级评估结果展示（Pass/Warning/Blocker）、引用内容回显、导出下载。
DraftHistory.tsx: 历史草稿列表页，展示所有草稿及状态徽章、评估摘要统计。
Impact.tsx: 影响分析首页与报告列表。
ImpactReport.tsx: 影响分析报告详情页，展示 AffectedSection（heading + reason tooltip），并将 report/trigger/impacted/new_version 预填参数导航到草稿工作台。
Graph.tsx: SVG 图谱可视化页。
Settings.tsx: 运行时配置页——查看和修改 LLM/Embedding 的 model、base_url、api_key，保存后即时生效；开发者模式下右侧轮询展示后端日志。
Evolution.tsx: GEP 自进化视图——展示本机演化信号历史、当前策略（innovate/balanced/harden/repair-only）、基因标签分布、高频失败检查器，消费 /api/evolution/stats；浅色空状态保持高对比。
Comparison.tsx: 文档比对工作台——双文件上传、四步向量流 / 传统流式切换、消费 `/api/comparison/analyze-4step` 与 `/api/comparison/analyze-stream` SSE，展示步骤状态、匹配进度、符合率与历史会话列表。
ComparisonSession.tsx: 比对结果详情页——审查意见列表（FindingCard/四象限状态/溯源跳转）、完整 Markdown 报告、两份文件章节预览，支持 Tabs 切换与高亮定位。
DesignSystem.tsx: 设计系统展示页。

法则: 每个页面只负责一个用户故事主视图；跨页复用能力下沉到 components/ 或 lib/。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
