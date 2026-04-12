# harnetics/api/
> L2 | 父级: src/harnetics/AGENTS.md

成员清单
__init__.py: 包入口，导出 create_api_app。
app.py: 新版 FastAPI 应用工厂，lifespan 初始化 graph DB，挂载全量 API router 与 SPA fallback/dist 静态资源。
deps.py: 依赖注入 provider — settings 与 graph connection。
routes/: 按领域拆分的 API 路由模块（documents/draft/evaluate/impact/graph/status）。documents 提供向量搜索并在向量不可用时降级到关键词匹配；draft/impact 复用同一套 OpenAI-compatible LLM 语义；status 同时暴露 `/api/status` 与 `/api/dashboard/stats`，并通过短 TTL 缓存保持 LLM 诊断字段稳定一致。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
