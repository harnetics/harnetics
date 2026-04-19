# [INPUT]: 依赖 os、pathlib、dotenv，定义运行时路径与 LLM/Embedding 配置
# [OUTPUT]: 提供 Settings 数据对象、默认路径常量、.env 路径解析与 get_settings() 工厂
# [POS]: harnetics 的运行时配置中心，统一定义 LLM、Embedding、存储路径参数，支持 .env 加载
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


DEFAULT_GRAPH_DB_PATH = Path("var/harnetics-graph.db")
DEFAULT_RAW_UPLOAD_DIR = Path("var/uploads")
DEFAULT_EXPORT_DIR = Path("var/exports")
DEFAULT_CHROMADB_PATH = Path("var/chroma")
DEFAULT_SERVER_PORT = 8000
DEFAULT_LLM_BASE_URL = ""  # 空字符串 → SDK 使用 api.openai.com/v1；本地 Ollama 设为 http://localhost:11434
DEFAULT_LLM_MODEL = "gpt-4o-mini"
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Settings:
    # ---- 图谱 SQLite ----
    graph_db_path: Path = DEFAULT_GRAPH_DB_PATH

    # ---- 上传与导出 ----
    raw_upload_dir: Path = DEFAULT_RAW_UPLOAD_DIR
    export_dir: Path = DEFAULT_EXPORT_DIR

    # ---- ChromaDB 向量库 ----
    chromadb_path: Path = DEFAULT_CHROMADB_PATH

    # ---- LLM ----
    llm_base_url: str = DEFAULT_LLM_BASE_URL
    llm_model: str = DEFAULT_LLM_MODEL

    # ---- Embedding ----
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    embedding_api_key: str = ""
    embedding_base_url: str = ""

    # ---- LLM API Key ----
    llm_api_key: str = ""

    # ---- Server ----
    server_port: int = DEFAULT_SERVER_PORT


def get_dotenv_path() -> Path | None:
    """解析当前应加载的 .env：优先显式指定，其次 cwd，最后仓库根目录。"""
    explicit = os.environ.get("HARNETICS_ENV_FILE", "").strip()
    if explicit:
        return Path(explicit).expanduser()

    cwd_dotenv = Path.cwd() / ".env"
    if cwd_dotenv.exists():
        return cwd_dotenv

    project_dotenv = _PROJECT_ROOT / ".env"
    if project_dotenv.exists():
        return project_dotenv

    return None


def get_settings() -> Settings:
    """读取 .env 文件 + 环境变量覆盖默认值。"""
    dotenv_path = get_dotenv_path()
    if dotenv_path is not None:
        load_dotenv(dotenv_path=dotenv_path, override=False)

    raw_upload_dir = os.environ.get("HARNETICS_RAW_UPLOAD_DIR")
    export_dir = os.environ.get("HARNETICS_EXPORT_DIR")
    graph_db = os.environ.get("HARNETICS_GRAPH_DB_PATH")
    chroma_dir = os.environ.get("HARNETICS_CHROMA_DIR")
    llm_model = os.environ.get("HARNETICS_LLM_MODEL")
    llm_url = os.environ.get("HARNETICS_LLM_BASE_URL")
    llm_api_key = os.environ.get("HARNETICS_LLM_API_KEY", "")
    embedding_model = os.environ.get("HARNETICS_EMBEDDING_MODEL")
    embedding_api_key = os.environ.get("HARNETICS_EMBEDDING_API_KEY", "")
    embedding_base_url = os.environ.get("HARNETICS_EMBEDDING_BASE_URL", "")
    server_port = os.environ.get("HARNETICS_SERVER_PORT")
    return Settings(
        raw_upload_dir=Path(raw_upload_dir) if raw_upload_dir else DEFAULT_RAW_UPLOAD_DIR,
        export_dir=Path(export_dir) if export_dir else DEFAULT_EXPORT_DIR,
        graph_db_path=Path(graph_db) if graph_db else DEFAULT_GRAPH_DB_PATH,
        chromadb_path=Path(chroma_dir) if chroma_dir else DEFAULT_CHROMADB_PATH,
        llm_model=llm_model or DEFAULT_LLM_MODEL,
        llm_base_url=llm_url or DEFAULT_LLM_BASE_URL,
        llm_api_key=llm_api_key,
        embedding_model=embedding_model or "paraphrase-multilingual-MiniLM-L12-v2",
        embedding_api_key=embedding_api_key,
        embedding_base_url=embedding_base_url,
        server_port=int(server_port) if server_port else DEFAULT_SERVER_PORT,
    )
