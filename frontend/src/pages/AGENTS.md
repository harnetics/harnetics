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
DesignSystem.tsx: 设计系统展示页。

法则: 每个页面只负责一个用户故事主视图；跨页复用能力下沉到 components/ 或 lib/。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
