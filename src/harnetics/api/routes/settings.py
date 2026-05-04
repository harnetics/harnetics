# [INPUT]: 依赖 FastAPI、pathlib、os、collections.deque、config.RuntimeSettingsManager、config.write_dotenv_values
# [OUTPUT]: 对外提供 settings_router (GET/PUT /api/settings、GET /api/settings/logs)，支持常用模型配置、thinking 开关与四步比对高级推理边界配置
# [POS]: api/routes 的设置与调试域 REST 端点，被 api/app.py 注册；PUT 写操作经 write_dotenv_values 回写到 .env，日志端点只读后端运行日志
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

import os
from collections import deque
from pathlib import Path

from fastapi import APIRouter, Request
from pydantic import BaseModel

from harnetics.config import write_dotenv_values

router = APIRouter(prefix="/api")


class SettingsPayload(BaseModel):
    llm_model: str | None = None
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_thinking_supported: str | None = None
    llm_enable_thinking: str | None = None
    embedding_model: str | None = None
    embedding_base_url: str | None = None
    embedding_api_key: str | None = None
    llm_max_tokens: str | None = None
    llm_timeout_seconds: str | None = None
    comparison_4step_batch_size: str | None = None
    comparison_step1_max_tokens: str | None = None
    comparison_step3_max_tokens: str | None = None
    comparison_step4_max_tokens: str | None = None


class DeveloperLogsResponse(BaseModel):
    path: str
    lines: list[str]


def _mask_key(key: str) -> str:
    """脱敏 API Key：仅显示前 4 位和后 4 位。"""
    if len(key) <= 8:
        return "*" * len(key) if key else ""
    return f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}"


def _masked_snapshot(raw: dict[str, str]) -> dict[str, str]:
    result = dict(raw)
    for k in ("llm_api_key", "embedding_api_key"):
        if k in result:
            result[k] = _mask_key(result[k])
    return result


def _latest_log_file() -> Path | None:
    explicit = os.environ.get("HARNETICS_LOG_FILE", "").strip()
    if explicit:
        path = Path(explicit).expanduser()
        if path.is_file():
            return path

    log_dir = Path(os.environ.get("HARNETICS_LOG_DIR", "data/logs")).expanduser()
    if not log_dir.is_dir():
        return None

    logs = [path for path in log_dir.glob("*.log") if path.is_file()]
    if not logs:
        return None
    return max(logs, key=lambda path: path.stat().st_mtime)


def _tail_lines(path: Path, limit: int) -> list[str]:
    count = max(1, min(limit, 500))
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        return [line.rstrip("\n") for line in deque(fh, maxlen=count)]


@router.get("/settings")
def get_settings(request: Request):
    mgr = request.app.state.runtime_settings
    return _masked_snapshot(mgr.snapshot())


@router.put("/settings")
def update_settings(request: Request, payload: SettingsPayload):
    mgr = request.app.state.runtime_settings
    changes = {k: v for k, v in payload.model_dump().items() if v is not None}
    updated = mgr.update(changes)
    write_dotenv_values(changes)
    return _masked_snapshot(updated)


@router.get("/settings/logs")
def get_developer_logs(limit: int = 200) -> DeveloperLogsResponse:
    path = _latest_log_file()
    if path is None:
        return DeveloperLogsResponse(path="", lines=[])
    return DeveloperLogsResponse(path=str(path), lines=_tail_lines(path, limit))
