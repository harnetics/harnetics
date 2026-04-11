# harnetics/
> L2 | 父级: /AGENTS.md

成员清单
__init__.py: 包级入口，导出最小公共 API。
app.py: 旧版 FastAPI/Jinja2 入口，保留 legacy repository 工作流与兼容性冒烟测试。
config.py: 运行时设置对象——隔离 legacy repository DB 与 graph DB，并统一上传、LLM、ChromaDB 与端口参数。
importer.py: 受控 Markdown/YAML 导入服务，负责解析、校验与入库。
retrieval.py: 候选检索规划器，按主题、部门、类型与层级对来源排序。
validation.py: 草稿校验器，产出阻断与警告级问题。
drafts.py: 草稿编排服务，负责 prompt 组装、生成落库、引注附着与状态更新。
repository.py: SQLite schema 初始化与唯一持久化边界（旧版 catalog 数据）。
models/: 领域 dataclass 包——document/icd/draft/impact + 旧版 records 兼容层。
graph/: 新版图谱 SQLite 连接管理器、DDL、索引、查询、向量检索与导入引擎；当前已支持 section-aware 引用边。
llm/: LLM 客户端包，承载 LiteLLM、本地 Ollama 与 OpenAI-compatible 接入；负责裸 Ollama 与 bare remote 模型名的 provider 归一化，并提供可控 LiteLLM debug 开关。
api/: React SPA 主工作流入口，负责图谱栈 API、仪表盘统计与前端 dist 托管；草稿与状态端点复用统一 LLM 配置语义。
parsers/: Markdown/YAML/ICD 解析器。
engine/: 对齐草稿、冲突检测、影响分析等图谱工作流核心引擎。
evaluators/: 草稿质量门评估器集合（EA/EB/ED）。
cli/: typer CLI 命令，面向 graph DB 的 init/ingest/serve。
web/: 旧版服务端渲染页面与路由，作为兼容层/参考保留，不再是主前端。

法则: 业务逻辑留在服务层，包根只做装配与边界定义。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
