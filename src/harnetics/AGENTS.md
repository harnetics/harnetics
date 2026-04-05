# harnetics/
> L2 | 父级: /AGENTS.md

成员清单
__init__.py: 包级入口，导出最小公共 API。
app.py: FastAPI 应用工厂，挂载健康检查、仓储/导入/检索/草稿服务与 web 路由。
config.py: 运行时设置对象与默认路径来源。
models.py: 领域记录 dataclass，供仓储与服务层共享。
importer.py: 受控 Markdown/YAML 导入服务，负责解析、校验与入库。
retrieval.py: 候选检索规划器，按主题、部门、类型与层级对来源排序。
llm.py: 本地 OpenAI-compatible LLM 客户端，负责最小 chat completions 调用。
validation.py: 草稿校验器，产出阻断与警告级问题。
drafts.py: 草稿编排服务，负责 prompt 组装、生成落库、引注附着与状态更新。
repository.py: SQLite schema 初始化与唯一持久化边界。
web/: 文档目录 HTTP 路由与页面渲染子模块。

法则: 业务逻辑留在服务层，包根只做装配与边界定义。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
