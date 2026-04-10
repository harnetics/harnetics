# pages/
> L2 | 父级: /frontend/src/AGENTS.md

成员清单
Dashboard.tsx: 仪表盘概览页，消费 /api/status。
Documents.tsx: 文档列表与筛选页。
DocumentDetail.tsx: 文档详情页，展示元数据/章节/关系。
DraftNew.tsx: 草稿创建工作台。
DraftShow.tsx: 草稿详情与评估页。
Impact.tsx: 影响分析首页与报告列表。
ImpactReport.tsx: 影响分析报告详情页。
Graph.tsx: SVG 图谱可视化页。
DesignSystem.tsx: 设计系统展示页。

法则: 每个页面只负责一个用户故事主视图；跨页复用能力下沉到 components/ 或 lib/。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
