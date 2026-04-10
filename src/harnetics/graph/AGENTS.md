# harnetics/graph/
> L2 | 父级: src/harnetics/AGENTS.md

成员清单
__init__.py: 包入口，导出 init_db / get_connection。
schema.sql: 7 表 + 7 索引的图谱 DDL（documents/sections/edges/icd_parameters/versions/drafts/impact_reports）。
store.py: SQLite 连接管理器——init_db() 建表，get_connection() 上下文管理器，启用外键 + WAL。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
