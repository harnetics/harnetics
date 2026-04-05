# [INPUT]: 依赖标准库 os 与 pathlib，用于读取环境变量和路径
# [OUTPUT]: 提供 Settings 数据对象与 get_settings() 工厂
# [POS]: harnetics 的运行时配置中心，统一定义数据库、上传与 LLM 参数
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from dataclasses import dataclass
from os import getenv
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    database_path: Path
    raw_upload_dir: Path
    export_dir: Path
    llm_base_url: str
    llm_model: str


def get_settings() -> Settings:
    return Settings(
        database_path=Path(getenv("HARNETICS_DATABASE_PATH", "var/harnetics.db")),
        raw_upload_dir=Path(getenv("HARNETICS_RAW_UPLOAD_DIR", "var/uploads/raw")),
        export_dir=Path(getenv("HARNETICS_EXPORT_DIR", "var/exports")),
        llm_base_url=getenv("HARNETICS_LLM_BASE_URL", "http://localhost:11434"),
        llm_model=getenv("HARNETICS_LLM_MODEL", "llama3.1"),
    )
