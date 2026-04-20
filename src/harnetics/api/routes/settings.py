# [INPUT]: 依赖 FastAPI、config.RuntimeSettingsManager、config.write_dotenv_values
# [OUTPUT]: 对外提供 settings_router (GET/PUT /api/settings)
# [POS]: api/routes 的设置域 REST 端点，被 api/app.py 注册；PUT 写操作经 write_dotenv_values 回写到 .env，.env 是单一真相源
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from harnetics.config import write_dotenv_values

router = APIRouter(prefix="/api")


class SettingsPayload(BaseModel):
    llm_model: str | None = None
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    embedding_model: str | None = None
    embedding_base_url: str | None = None
    embedding_api_key: str | None = None


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
