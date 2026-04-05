# harnetics/
> L2 | 父级: /AGENTS.md

成员清单
__init__.py: 包级入口，导出最小公共 API。
app.py: FastAPI 应用工厂与健康检查路由。
config.py: 运行时设置对象与默认路径来源。

法则: 只保留最小可运行骨架，避免把业务逻辑塞进包根。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
