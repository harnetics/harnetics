# harnetics/api/routes/
> L2 | 父级: src/harnetics/api/AGENTS.md

成员清单
__init__.py: 包入口（空）。
documents.py: 文档 CRUD + 上传 + 搜索路由，挂载于 /api/documents。
draft.py: 草稿生成、查询与历史列表路由，挂载于 /api/draft。
evaluate.py: 草稿评估触发路由，挂载于 /api/evaluate。
evolution.py: 进化信号统计路由，挂载于 /api/evolution，服务 Evolution 页面。
fixture.py: 夹具导入、场景列举与运行路由，挂载于 /api/fixture，驱动 TestLab 演示。
graph.py: 文档图谱节点/边查询路由，挂载于 /api/graph。
impact.py: 影响分析触发与报告查询路由，挂载于 /api/impact。
settings.py: LLM/Embedding 运行时配置读写路由，挂载于 /api/settings。
status.py: 健康检查与 LLM/Embedding 状态探测路由，挂载于 /api/status。

法则: routes/ 只做 HTTP 协议适配与请求验证，业务逻辑全部委托 engine/ 与 store/ 层。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
