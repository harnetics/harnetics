# [INPUT]: 依赖 os、pathlib、dotenv、threading
# [OUTPUT]: 提供 Settings 数据对象、RuntimeSettingsManager 运行时覆盖层、write_dotenv_values() 回写函数、默认路径常量、get_settings() 工厂
# [POS]: harnetics 的运行时配置中心，.env 文件是单一真相源，API 层写操作经 write_dotenv_values 回写，进程内经 RuntimeSettingsManager 即时可见
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

import os
import threading
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values


DEFAULT_GRAPH_DB_PATH = Path("var/harnetics-graph.db")
DEFAULT_RAW_UPLOAD_DIR = Path("var/uploads")
DEFAULT_EXPORT_DIR = Path("var/exports")
DEFAULT_CHROMADB_PATH = Path("var/chroma")
DEFAULT_SERVER_PORT = 8000
DEFAULT_LLM_BASE_URL = ""  # 空字符串 → SDK 使用 api.openai.com/v1；本地 Ollama 设为 http://localhost:11434
DEFAULT_LLM_MODEL = "gpt-4o-mini"
DEFAULT_LLM_MAX_TOKENS = 16384
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
    llm_max_tokens: int = DEFAULT_LLM_MAX_TOKENS

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
    """读取 .env 文件 + 环境变量覆盖默认值，不污染进程环境。"""
    dotenv_path = get_dotenv_path()
    dotenv_map = {
        str(key): str(value)
        for key, value in (dotenv_values(dotenv_path) if dotenv_path is not None else {}).items()
        if key is not None and value is not None
    }

    def _get(name: str, default: str | None = None) -> str | None:
        if name in os.environ:
            return os.environ[name]
        return dotenv_map.get(name, default)

    raw_upload_dir = _get("HARNETICS_RAW_UPLOAD_DIR")
    export_dir = _get("HARNETICS_EXPORT_DIR")
    graph_db = _get("HARNETICS_GRAPH_DB_PATH")
    chroma_dir = _get("HARNETICS_CHROMA_DIR")
    llm_model = _get("HARNETICS_LLM_MODEL")
    llm_url = _get("HARNETICS_LLM_BASE_URL")
    llm_api_key = _get("HARNETICS_LLM_API_KEY", "") or ""
    llm_max_tokens_raw = _get("HARNETICS_LLM_MAX_TOKENS")
    embedding_model = _get("HARNETICS_EMBEDDING_MODEL")
    embedding_api_key = _get("HARNETICS_EMBEDDING_API_KEY", "") or ""
    embedding_base_url = _get("HARNETICS_EMBEDDING_BASE_URL", "") or ""
    server_port = _get("HARNETICS_SERVER_PORT")
    return Settings(
        raw_upload_dir=Path(raw_upload_dir) if raw_upload_dir else DEFAULT_RAW_UPLOAD_DIR,
        export_dir=Path(export_dir) if export_dir else DEFAULT_EXPORT_DIR,
        graph_db_path=Path(graph_db) if graph_db else DEFAULT_GRAPH_DB_PATH,
        chromadb_path=Path(chroma_dir) if chroma_dir else DEFAULT_CHROMADB_PATH,
        llm_model=llm_model or DEFAULT_LLM_MODEL,
        llm_base_url=llm_url or DEFAULT_LLM_BASE_URL,
        llm_api_key=llm_api_key,
        llm_max_tokens=int(llm_max_tokens_raw) if llm_max_tokens_raw else DEFAULT_LLM_MAX_TOKENS,
        embedding_model=embedding_model or "paraphrase-multilingual-MiniLM-L12-v2",
        embedding_api_key=embedding_api_key,
        embedding_base_url=embedding_base_url,
        server_port=int(server_port) if server_port else DEFAULT_SERVER_PORT,
    )


# ================================================================
# 运行时可变配置覆盖层
# ================================================================

# 允许通过 API 实时修改的字段白名单
_MUTABLE_KEYS = frozenset({
    "llm_model", "llm_base_url", "llm_api_key",
    "embedding_model", "embedding_base_url", "embedding_api_key",
})

# Settings 字段名 → .env 键名映射（用于回写）
_MUTABLE_KEY_TO_ENV: dict[str, str] = {
    "llm_model":           "HARNETICS_LLM_MODEL",
    "llm_base_url":        "HARNETICS_LLM_BASE_URL",
    "llm_api_key":         "HARNETICS_LLM_API_KEY",
    "embedding_model":     "HARNETICS_EMBEDDING_MODEL",
    "embedding_base_url":  "HARNETICS_EMBEDDING_BASE_URL",
    "embedding_api_key":   "HARNETICS_EMBEDDING_API_KEY",
}


def write_dotenv_values(changes: dict[str, str]) -> None:
    """将可变配置字段回写到 .env 文件，消除 DB vs 文件的双真相源。"""
    from dotenv import set_key
    dotenv_path = get_dotenv_path()
    if dotenv_path is None:
        dotenv_path = _PROJECT_ROOT / ".env"
        dotenv_path.touch()
    for settings_key, value in changes.items():
        env_key = _MUTABLE_KEY_TO_ENV.get(settings_key)
        if env_key:
            set_key(str(dotenv_path), env_key, value)


class RuntimeSettingsManager:
    """在 get_settings() 基线之上叠加内存态覆盖值，线程安全。"""

    def __init__(self, base: Settings) -> None:
        self._base = base
        self._overrides: dict[str, str] = {}
        self._lock = threading.Lock()

    # ---- 读 ----

    def get(self, key: str) -> str:
        with self._lock:
            if key in self._overrides:
                return self._overrides[key]
        return getattr(self._base, key, "")

    def snapshot(self) -> dict[str, str]:
        """返回所有可变字段的当前有效值（覆盖值 > 基线值）。"""
        result: dict[str, str] = {}
        with self._lock:
            for k in _MUTABLE_KEYS:
                result[k] = self._overrides.get(k, getattr(self._base, k, ""))
        return result

    # ---- 写 ----

    def update(self, changes: dict[str, str]) -> dict[str, str]:
        """批量更新覆盖值，忽略不在白名单中的键，返回更新后的快照。"""
        with self._lock:
            for k, v in changes.items():
                if k in _MUTABLE_KEYS:
                    self._overrides[k] = v
        return self.snapshot()
