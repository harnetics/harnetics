# [INPUT]: 依赖 pathlib，用于定义固定运行时路径
# [OUTPUT]: 提供 Settings 数据对象与 get_settings() 工厂
# [POS]: harnetics 的运行时配置中心，统一定义数据库、上传与 LLM 参数
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    database_path: Path = Path("var/harnetics.db")
    raw_upload_dir: Path = Path("var/uploads")
    export_dir: Path = Path("var/exports")
    llm_base_url: str = "http://127.0.0.1:11434/v1"
    llm_model: str = "gemma-3-27b-it"


def get_settings() -> Settings:
    return Settings()
