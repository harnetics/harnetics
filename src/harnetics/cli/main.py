"""
# [INPUT]: 依赖 typer、rich、graph.store、graph.indexer、api.app、uvicorn
# [OUTPUT]: 对外提供 CLI 命令: init、ingest、serve
# [POS]: cli 包的命令入口，默认操作独立 graph DB，并提供 reset/reload 等开发启动能力
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from harnetics.config import DEFAULT_CHROMADB_PATH, DEFAULT_GRAPH_DB_PATH

app = typer.Typer(name="harnetics", help="Harnetics — 航天文档对齐工具")
console = Console()


# ================================================================
# init — 初始化数据库
# ================================================================

@app.command()
def init(
    db: str = typer.Option(str(DEFAULT_GRAPH_DB_PATH), help="Graph SQLite 数据库路径"),
    reset: bool = typer.Option(False, "--reset", help="删除现有图谱数据库后重建"),
) -> None:
    """初始化图谱数据库（建表 + WAL 模式）。"""
    from harnetics.graph.store import init_db
    db_path = Path(db)
    if reset and db_path.exists():
        db_path.unlink()
    init_db(db_path)
    console.print(f"[green]✓[/green] 数据库已初始化：{db_path}")


# ================================================================
# ingest — 批量导入文档
# ================================================================

@app.command()
def ingest(
    path: str = typer.Argument(..., help="文件或目录路径（支持 .md / .yaml）"),
    db: str = typer.Option(str(DEFAULT_GRAPH_DB_PATH), help="Graph SQLite 数据库路径"),
    chroma: str = typer.Option(str(DEFAULT_CHROMADB_PATH), help="ChromaDB 持久化目录"),
    with_embeddings: bool = typer.Option(False, "--with-embeddings", help="同步构建 Chroma 向量索引（首次运行可能较慢）"),
) -> None:
    """将文档批量导入图谱数据库与向量索引。"""
    from harnetics.graph.store import init_db
    from harnetics.graph.indexer import DocumentIndexer
    from harnetics.graph.embeddings import EmbeddingStore
    from harnetics.config import get_settings

    db_path = Path(db)
    init_db(db_path)

    target = Path(path)
    if not target.exists():
        console.print(f"[red]错误：路径不存在：{target}[/red]")
        raise typer.Exit(1)

    emb_store = None
    if with_embeddings:
        console.print("[cyan]►[/cyan] 初始化向量索引（首次运行可能下载/加载嵌入模型）")
        emb_store = EmbeddingStore(
            persist_path=chroma,
            model_name=get_settings().embedding_model,
        )
    else:
        console.print("[yellow]![/yellow] 已跳过向量索引，仅导入图谱 SQLite；如需语义索引请追加 --with-embeddings")

    indexer = DocumentIndexer(embedding_store=emb_store)

    if target.is_file():
        doc = indexer.ingest_document(target)
        console.print(f"[green]✓[/green] 已导入：{doc.doc_id} — {doc.title}")
    else:
        docs = indexer.ingest_directory(target)
        table = Table("文档 ID", "标题", "类型", "状态")
        for doc in docs:
            table.add_row(doc.doc_id, doc.title, doc.doc_type, doc.status)
        console.print(table)
        console.print(f"[green]✓[/green] 共导入 {len(docs)} 个文档")


# ================================================================
# serve — 启动 Web 服务
# ================================================================

@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="监听地址"),
    port: int = typer.Option(8000, help="监听端口"),
    reload: bool = typer.Option(False, help="开发模式热重载"),
    db: str = typer.Option(str(DEFAULT_GRAPH_DB_PATH), help="Graph SQLite 数据库路径"),
) -> None:
    """启动 Harnetics Web 服务（FastAPI + uvicorn）。"""
    import os
    import uvicorn

    os.environ.setdefault("HARNETICS_GRAPH_DB_PATH", str(Path(db)))
    console.print(f"[cyan]►[/cyan] 启动服务 http://{host}:{port}")
    uvicorn.run(
        "harnetics.api.app:create_api_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
    )


# ================================================================
# 入口
# ================================================================

if __name__ == "__main__":
    app()
