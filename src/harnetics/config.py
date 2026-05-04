# [INPUT]: 依赖 os、pathlib、dotenv、threading
# [OUTPUT]: 提供 Settings 数据对象、RuntimeSettingsManager 运行时覆盖层、write_dotenv_values() 回写函数、默认路径/模型/thinking/四步比对推理边界常量、get_settings() 工厂
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
DEFAULT_LLM_TIMEOUT_SECONDS = 180.0
DEFAULT_LLM_THINKING_SUPPORTED = False
DEFAULT_LLM_ENABLE_THINKING = False
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_EMBEDDING_BASE_URL = ""
DEFAULT_COMPARISON_4STEP_BATCH_SIZE = 10
DEFAULT_COMPARISON_STEP1_MAX_TOKENS = 500000
DEFAULT_COMPARISON_STEP3_MAX_TOKENS = 16384
DEFAULT_COMPARISON_STEP4_MAX_TOKENS = 500000
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
    llm_timeout_seconds: float = DEFAULT_LLM_TIMEOUT_SECONDS
    llm_thinking_supported: bool = DEFAULT_LLM_THINKING_SUPPORTED
    llm_enable_thinking: bool = DEFAULT_LLM_ENABLE_THINKING

    # ---- Embedding ----
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    embedding_api_key: str = ""
    embedding_base_url: str = DEFAULT_EMBEDDING_BASE_URL

    # ---- LLM API Key ----
    llm_api_key: str = ""

    # ---- Server ----
    server_port: int = DEFAULT_SERVER_PORT

    # ---- Comparison ----
    comparison_4step_batch_size: int = DEFAULT_COMPARISON_4STEP_BATCH_SIZE
    comparison_step1_max_tokens: int = DEFAULT_COMPARISON_STEP1_MAX_TOKENS
    comparison_step3_max_tokens: int = DEFAULT_COMPARISON_STEP3_MAX_TOKENS
    comparison_step4_max_tokens: int = DEFAULT_COMPARISON_STEP4_MAX_TOKENS


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
    llm_timeout_raw = _get("HARNETICS_LLM_TIMEOUT_SECONDS")
    llm_thinking_supported_raw = _get("HARNETICS_LLM_THINKING_SUPPORTED")
    llm_enable_thinking_raw = _get("HARNETICS_LLM_ENABLE_THINKING")
    embedding_model = _get("HARNETICS_EMBEDDING_MODEL")
    embedding_api_key = _get("HARNETICS_EMBEDDING_API_KEY", "") or ""
    embedding_base_url = _get("HARNETICS_EMBEDDING_BASE_URL", "") or ""
    server_port = _get("HARNETICS_SERVER_PORT")
    comparison_batch_raw = _get("HARNETICS_COMPARISON_4STEP_BATCH_SIZE")
    comparison_step1_tokens_raw = _get("HARNETICS_COMPARISON_STEP1_MAX_TOKENS")
    comparison_step3_tokens_raw = _get("HARNETICS_COMPARISON_STEP3_MAX_TOKENS")
    comparison_step4_tokens_raw = _get("HARNETICS_COMPARISON_STEP4_MAX_TOKENS")
    return Settings(
        raw_upload_dir=Path(raw_upload_dir) if raw_upload_dir else DEFAULT_RAW_UPLOAD_DIR,
        export_dir=Path(export_dir) if export_dir else DEFAULT_EXPORT_DIR,
        graph_db_path=Path(graph_db) if graph_db else DEFAULT_GRAPH_DB_PATH,
        chromadb_path=Path(chroma_dir) if chroma_dir else DEFAULT_CHROMADB_PATH,
        llm_model=llm_model or DEFAULT_LLM_MODEL,
        llm_base_url=llm_url or DEFAULT_LLM_BASE_URL,
        llm_api_key=llm_api_key,
        llm_max_tokens=_int_setting(llm_max_tokens_raw, DEFAULT_LLM_MAX_TOKENS),
        llm_timeout_seconds=_float_setting(llm_timeout_raw, DEFAULT_LLM_TIMEOUT_SECONDS),
        llm_thinking_supported=_bool_setting(
            llm_thinking_supported_raw, DEFAULT_LLM_THINKING_SUPPORTED
        ),
        llm_enable_thinking=_bool_setting(llm_enable_thinking_raw, DEFAULT_LLM_ENABLE_THINKING),
        embedding_model=embedding_model or DEFAULT_EMBEDDING_MODEL,
        embedding_api_key=embedding_api_key,
        embedding_base_url=embedding_base_url or DEFAULT_EMBEDDING_BASE_URL,
        server_port=int(server_port) if server_port else DEFAULT_SERVER_PORT,
        comparison_4step_batch_size=_int_setting(
            comparison_batch_raw, DEFAULT_COMPARISON_4STEP_BATCH_SIZE
        ),
        comparison_step1_max_tokens=_int_setting(
            comparison_step1_tokens_raw, DEFAULT_COMPARISON_STEP1_MAX_TOKENS
        ),
        comparison_step3_max_tokens=_int_setting(
            comparison_step3_tokens_raw, DEFAULT_COMPARISON_STEP3_MAX_TOKENS
        ),
        comparison_step4_max_tokens=_int_setting(
            comparison_step4_tokens_raw, DEFAULT_COMPARISON_STEP4_MAX_TOKENS
        ),
    )


def _int_setting(raw: str | None, default: int) -> int:
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def _float_setting(raw: str | None, default: float) -> float:
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def _bool_setting(raw: str | None, default: bool) -> bool:
    if raw is None or raw == "":
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


# ================================================================
# 运行时可变配置覆盖层
# ================================================================

# 允许通过 API 实时修改的字段白名单
_MUTABLE_KEYS = frozenset({
    "llm_model", "llm_base_url", "llm_api_key",
    "embedding_model", "embedding_base_url", "embedding_api_key",
    "llm_thinking_supported", "llm_enable_thinking",
    "llm_max_tokens", "llm_timeout_seconds",
    "comparison_4step_batch_size", "comparison_step1_max_tokens",
    "comparison_step3_max_tokens", "comparison_step4_max_tokens",
})

# Settings 字段名 → .env 键名映射（用于回写）
_MUTABLE_KEY_TO_ENV: dict[str, str] = {
    "llm_model":           "HARNETICS_LLM_MODEL",
    "llm_base_url":        "HARNETICS_LLM_BASE_URL",
    "llm_api_key":         "HARNETICS_LLM_API_KEY",
    "embedding_model":     "HARNETICS_EMBEDDING_MODEL",
    "embedding_base_url":  "HARNETICS_EMBEDDING_BASE_URL",
    "embedding_api_key":   "HARNETICS_EMBEDDING_API_KEY",
    "llm_thinking_supported": "HARNETICS_LLM_THINKING_SUPPORTED",
    "llm_enable_thinking":    "HARNETICS_LLM_ENABLE_THINKING",
    "llm_max_tokens":      "HARNETICS_LLM_MAX_TOKENS",
    "llm_timeout_seconds": "HARNETICS_LLM_TIMEOUT_SECONDS",
    "comparison_4step_batch_size":  "HARNETICS_COMPARISON_4STEP_BATCH_SIZE",
    "comparison_step1_max_tokens":  "HARNETICS_COMPARISON_STEP1_MAX_TOKENS",
    "comparison_step3_max_tokens":  "HARNETICS_COMPARISON_STEP3_MAX_TOKENS",
    "comparison_step4_max_tokens":  "HARNETICS_COMPARISON_STEP4_MAX_TOKENS",
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
