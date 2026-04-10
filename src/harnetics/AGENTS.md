# harnetics/
> L2 | 父级: /AGENTS.md

成员清单
__init__.py: 包级入口，导出最小公共 API。
app.py: FastAPI 应用工厂（旧版入口），挂载健康检查、仓储/导入/检索/草稿服务与 web 路由。
config.py: 运行时设置对象——隔离 legacy repository DB 与 graph DB，并统一上传、LLM、ChromaDB 与端口参数。
importer.py: 受控 Markdown/YAML 导入服务，负责解析、校验与入库。
retrieval.py: 候选检索规划器，按主题、部门、类型与层级对来源排序。
validation.py: 草稿校验器，产出阻断与警告级问题。
drafts.py: 草稿编排服务，负责 prompt 组装、生成落库、引注附着与状态更新。
repository.py: SQLite schema 初始化与唯一持久化边界（旧版 catalog 数据）。
models/: 领域 dataclass 包——document/icd/draft/impact + 旧版 records 兼容层。
graph/: 新版图谱 SQLite 连接管理器、DDL、索引、查询、向量检索与导入引擎。
llm/: LLM 客户端包，承载 litellm/Ollama 适配与旧版 OpenAI-compatible 兼容层。
api/: 新版 FastAPI 应用工厂 + 依赖注入 + documents/draft/evaluate/impact/graph/status 路由。
parsers/: Markdown/YAML/ICD 解析器。
engine/: 对齐草稿、冲突检测、影响分析等核心引擎。
evaluators/: 草稿质量门评估器集合（EA/EB/ED）。
cli/: typer CLI 命令，面向 graph DB 的 init/ingest/serve。
web/: 文档目录 HTTP 路由与页面渲染子模块，兼容旧工作流并承载新仪表盘/图谱页面。

法则: 业务逻辑留在服务层，包根只做装配与边界定义。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
