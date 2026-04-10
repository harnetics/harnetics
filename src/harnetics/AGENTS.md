# harnetics/
> L2 | 父级: /AGENTS.md

成员清单
__init__.py: 包级入口，导出最小公共 API。
app.py: FastAPI 应用工厂（旧版入口），挂载健康检查、仓储/导入/检索/草稿服务与 web 路由。
config.py: 运行时设置对象——数据库路径、ChromaDB、LLM、嵌入模型与服务端口。
importer.py: 受控 Markdown/YAML 导入服务，负责解析、校验与入库。
retrieval.py: 候选检索规划器，按主题、部门、类型与层级对来源排序。
validation.py: 草稿校验器，产出阻断与警告级问题。
drafts.py: 草稿编排服务，负责 prompt 组装、生成落库、引注附着与状态更新。
repository.py: SQLite schema 初始化与唯一持久化边界（旧版 catalog 数据）。
models/: 领域 dataclass 包——document/icd/draft/impact + 旧版 records 兼容层。
graph/: 图谱 SQLite 连接管理器 + schema.sql（7 表 + 7 索引）。
llm/: LLM 客户端包，承载 OpenAI-compatible HTTP 调用。
api/: 新版 FastAPI 应用工厂 + 依赖注入 + API 路由骨架。
parsers/: 预留——Markdown/YAML 解析器。
engine/: 预留——对齐引擎核心逻辑。
evaluators/: 预留——草稿评估器。
cli/: 预留——typer CLI 命令。
web/: 文档目录 HTTP 路由与页面渲染子模块。

法则: 业务逻辑留在服务层，包根只做装配与边界定义。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
