# [INPUT]: 依赖 os、pathlib，用于定义旧仓储栈与新图谱栈的固定运行时路径
# [OUTPUT]: 提供 Settings 数据对象、默认路径常量与 get_settings() 工厂
# [POS]: harnetics 的运行时配置中心，隔离 legacy repository DB 与 graph DB，统一定义上传与 LLM 参数
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_REPOSITORY_DB_PATH = Path("var/harnetics.db")
DEFAULT_GRAPH_DB_PATH = Path("var/harnetics-graph.db")
DEFAULT_RAW_UPLOAD_DIR = Path("var/uploads")
DEFAULT_EXPORT_DIR = Path("var/exports")
DEFAULT_CHROMADB_PATH = Path("var/chroma")
DEFAULT_SERVER_PORT = 8000
DEFAULT_LLM_BASE_URL = "http://localhost:11434"
DEFAULT_LLM_MODEL = "gemma4:26b"


@dataclass(frozen=True, slots=True)
class Settings:
    # ---- 旧版 Repository 路径（保留兼容） ----
    database_path: Path = DEFAULT_REPOSITORY_DB_PATH
    raw_upload_dir: Path = DEFAULT_RAW_UPLOAD_DIR
    export_dir: Path = DEFAULT_EXPORT_DIR

    # ---- 图谱 SQLite ----
    graph_db_path: Path = DEFAULT_GRAPH_DB_PATH

    # ---- ChromaDB 向量库 ----
    chromadb_path: Path = DEFAULT_CHROMADB_PATH

    # ---- LLM ----
    llm_base_url: str = DEFAULT_LLM_BASE_URL
    llm_model: str = DEFAULT_LLM_MODEL

    # ---- Embedding ----
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"

    # ---- Server ----
    server_port: int = DEFAULT_SERVER_PORT


def get_settings() -> Settings:
    """读取环境变量覆盖默认值。"""
    database_path = os.environ.get("HARNETICS_DATABASE_PATH")
    raw_upload_dir = os.environ.get("HARNETICS_RAW_UPLOAD_DIR")
    export_dir = os.environ.get("HARNETICS_EXPORT_DIR")
    graph_db = os.environ.get("HARNETICS_GRAPH_DB_PATH")
    chroma_dir = os.environ.get("HARNETICS_CHROMA_DIR")
    llm_model = os.environ.get("HARNETICS_LLM_MODEL")
    llm_url = os.environ.get("HARNETICS_LLM_BASE_URL")
    server_port = os.environ.get("HARNETICS_SERVER_PORT")
    return Settings(
        database_path=Path(database_path) if database_path else DEFAULT_REPOSITORY_DB_PATH,
        raw_upload_dir=Path(raw_upload_dir) if raw_upload_dir else DEFAULT_RAW_UPLOAD_DIR,
        export_dir=Path(export_dir) if export_dir else DEFAULT_EXPORT_DIR,
        graph_db_path=Path(graph_db) if graph_db else DEFAULT_GRAPH_DB_PATH,
        chromadb_path=Path(chroma_dir) if chroma_dir else DEFAULT_CHROMADB_PATH,
        llm_model=llm_model or DEFAULT_LLM_MODEL,
        llm_base_url=llm_url or DEFAULT_LLM_BASE_URL,
        server_port=int(server_port) if server_port else DEFAULT_SERVER_PORT,
    )
