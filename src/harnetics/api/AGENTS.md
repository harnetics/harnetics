# harnetics/api/
> L2 | 父级: src/harnetics/AGENTS.md

成员清单
__init__.py: 包入口，导出 create_api_app。
app.py: 新版 FastAPI 应用工厂，lifespan 初始化图谱 DB，挂载静态文件与模板。
deps.py: 依赖注入 provider — settings 与 graph connection。
routes/: 预留——按领域拆分的 API 路由模块。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
