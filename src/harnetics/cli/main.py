"""
# [INPUT]: 依赖 typer、rich、graph.store、graph.indexer、api.app、uvicorn、webbrowser、threading
# [OUTPUT]: 对外提供 CLI 命令: init、ingest、serve；serve 支持启动配置检测、浏览器自动打开
# [POS]: cli 包的命令入口，默认操作独立 graph DB，并提供 reset/reload 等开发启动能力
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""
from __future__ import annotations

import threading
import webbrowser
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from harnetics.config import DEFAULT_CHROMADB_PATH, DEFAULT_GRAPH_DB_PATH

app = typer.Typer(name="harnetics", help="Harnetics — 航天文档对齐工具")
console = Console()


# ================================================================
# 配置检测辅助
# ================================================================

def _check_config_warnings() -> None:
    """检查 LLM / Embedding 关键参数，未配置时打印友好引导。"""
    from harnetics.config import get_settings, get_dotenv_path

    settings = get_settings()
    dotenv_path = get_dotenv_path()
    env_hint = str(dotenv_path) if dotenv_path else ".env（将在项目根目录自动创建）"

    rows: list[tuple[str, str, str]] = []

    # --- LLM ---
    if not settings.llm_api_key:
        rows.append(("HARNETICS_LLM_API_KEY", settings.llm_model or "gpt-4o-mini", "云端 LLM API Key（OpenAI-compatible）"))
    if not settings.llm_base_url:
        rows.append(("HARNETICS_LLM_BASE_URL", "https://api.openai.com/v1", "LLM 端点 URL（留空则用 OpenAI 官方）"))

    # --- Embedding ---
    if not settings.embedding_api_key and settings.embedding_base_url:
        rows.append(("HARNETICS_EMBEDDING_API_KEY", "", "远端 Embedding API Key"))
    if not settings.embedding_base_url:
        rows.append(("HARNETICS_EMBEDDING_MODEL", settings.embedding_model, "Embedding 模型名（本地默认已内置，云端需指定）"))

    if not rows:
        return  # 已正确配置，静默退出

    tbl = Table("环境变量", "示例值/当前默认", "说明", show_lines=False, style="yellow")
    for var, example, desc in rows:
        tbl.add_row(f"[bold]{var}[/bold]", example, desc)

    console.print(
        Panel(
            tbl,
            title="[yellow bold]⚠  检测到未配置的 LLM/Embedding 参数[/yellow bold]",
            subtitle=f"[dim]请在 {env_hint} 中填写以上变量后重启服务[/dim]",
            border_style="yellow",
            padding=(1, 2),
        )
    )


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

    settings = get_settings()
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
            model_name=settings.embedding_model,
            api_key=settings.embedding_api_key,
            base_url=settings.embedding_base_url,
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
    no_browser: bool = typer.Option(False, "--no-browser", help="禁止自动打开浏览器"),
) -> None:
    """启动 Harnetics Web 服务（FastAPI + uvicorn）。"""
    import os
    import uvicorn

    os.environ.setdefault("HARNETICS_GRAPH_DB_PATH", str(Path(db)))

    # ---- 配置检测 ----
    _check_config_warnings()

    # ---- 打印可点击地址 ----
    url = f"http://localhost:{port}"
    console.print(f"[cyan]►[/cyan] 启动服务 {url}")

    # ---- 自动打开浏览器（uvicorn.run 是阻塞调用，用后台线程延迟打开） ----
    if not no_browser and not reload:
        def _open() -> None:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        threading.Timer(1.5, _open).start()

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
