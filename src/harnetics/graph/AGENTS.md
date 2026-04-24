# harnetics/graph/
> L2 | 父级: src/harnetics/AGENTS.md

成员清单
__init__.py: 包入口，导出 init_db / get_connection。
schema.sql: 7 表 + 7 索引的图谱 DDL（documents/sections/edges/icd_parameters/versions/drafts/impact_reports）。
store.py: SQLite 连接管理器——init_db() 建表并拒绝 legacy schema 冲突，get_connection() 上下文管理器，启用外键 + WAL。
indexer.py: 文档入库引擎，负责格式识别、解析、建节点/章节/边与 ICD 参数抽取；对 Markdown/YAML 生成 section-aware 引用边并尝试推断 target section。
embeddings.py: ChromaDB 持久化向量索引，支持本地 sentence-transformers 与云端 OpenAI-compatible embeddings，并提供章节级/文档级语义检索；`delete_by_doc(doc_id)` 支持按文档删除向量条目。
query.py: 图谱高阶查询层，提供全图、上下游、陈旧引用与 related 文档查询。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
