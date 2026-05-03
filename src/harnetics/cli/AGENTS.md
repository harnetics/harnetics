# harnetics/cli/
> L2 | 父级: src/harnetics/AGENTS.md

成员清单
__init__.py: 包入口。
main.py: typer CLI 命令入口，提供 graph DB 的 init、ingest、serve，并支持 `--reset` 重建图谱库；`ingest --with-embeddings` 会透传 .env 中的云端 embedding 配置；`serve` 可通过 `HARNETICS_LOG_DIR` 将桌面 sidecar 日志写入用户数据目录。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
