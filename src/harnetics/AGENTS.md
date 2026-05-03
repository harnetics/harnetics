# harnetics/
> L2 | 父级: /AGENTS.md

成员清单
__init__.py: 包级入口，导出 create_app（映射 api.app.create_api_app）、Settings 与 get_settings。
config.py: 运行时设置对象——统一 graph DB、上传、云端优先 LLM/Embedding 默认值、LLM 超时、比对四步 token/batch 边界、ChromaDB、端口参数与 `.env` 解析路径（显式文件 > cwd > 仓库根）；含 RuntimeSettingsManager 内存态覆盖层。
models/: 领域 dataclass 包——document/icd/draft/impact 四个子模块。
graph/: 图谱 SQLite 连接管理器、DDL、索引、查询、向量检索与导入引擎；支持 section-aware 引用边与 edge collapse。
llm/: LLM 客户端包，承载 OpenAI-compatible 会话调用与显式本地 Ollama 兼容路径；负责原始模型名/诊断模型名分离、路由归一化、模型探测与错误脱敏。
api/: React SPA 主工作流入口，负责图谱栈 API、仪表盘统计与前端 dist 托管；草稿与状态端点复用统一 LLM 配置语义；settings 端点提供运行时配置读写与开发者日志读取。
desktop/: 桌面 sidecar 运行时路径契约，统一用户 app data 下的 graph DB、Chroma、上传、导出、日志与 `.env`。
parsers/: Markdown/YAML/ICD 解析器。
engine/: 对齐草稿、冲突检测、影响分析等图谱工作流核心引擎。
evaluators/: 草稿质量门评估器集合（EA/EB/ED）。
cli/: typer CLI 命令，面向 graph DB 的 init/ingest/serve；serve 同时作为桌面 sidecar 后端入口。

法则: 业务逻辑留在服务层，包根只做装配与边界定义。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
