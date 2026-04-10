# [INPUT]: 依赖 pathlib，用于定义固定运行时路径
# [OUTPUT]: 提供 Settings 数据对象与 get_settings() 工厂
# [POS]: harnetics 的运行时配置中心，统一定义数据库、上传与 LLM 参数
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    # ---- 旧版 Repository 路径（保留兼容） ----
    database_path: Path = Path("var/harnetics.db")
    raw_upload_dir: Path = Path("var/uploads")
    export_dir: Path = Path("var/exports")

    # ---- 图谱 SQLite ----
    graph_db_path: Path = Path("var/harnetics.db")

    # ---- ChromaDB 向量库 ----
    chromadb_path: Path = Path("var/chroma/")

    # ---- LLM ----
    llm_base_url: str = "http://localhost:11434"
    llm_model: str = "ollama/gemma4:26b-it-a4b-q4_K_M"

    # ---- Embedding ----
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"

    # ---- Server ----
    server_port: int = 8080


def get_settings() -> Settings:
    return Settings()
