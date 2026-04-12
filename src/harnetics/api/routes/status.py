"""
# [INPUT]: 依赖 app.state.settings、config.get_dotenv_path、graph.store (counts)、graph.query (stale_references)、llm.client (availability_status)
# [OUTPUT]: 对外提供 router: GET /api/status、GET /api/dashboard/stats
# [POS]: api/routes 的健康看板端点，US5 仪表盘数据源，含 LLM/Embedding 可用性、effective route 与配置来源
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""
from __future__ import annotations

from time import monotonic

from fastapi import APIRouter, Request

from harnetics.config import get_dotenv_path
from harnetics.graph import store
from harnetics.graph.query import get_graph

router = APIRouter(prefix="/api", tags=["status"])

_LLM_STATUS_CACHE_TTL_SECONDS = 5.0


@router.get("/status")
@router.get("/dashboard/stats")
def system_status(request: Request) -> dict:
    """返回仪表盘统计：文档数、草稿数、陈旧引用数、LLM/Embedding 可用性。"""
    with store.get_connection() as conn:
        doc_count: int = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        draft_count: int = conn.execute("SELECT COUNT(*) FROM drafts").fetchone()[0]
        eval_pass: int = conn.execute(
            "SELECT COUNT(*) FROM drafts WHERE status = 'eval_pass'"
        ).fetchone()[0]
        eval_blocked: int = conn.execute(
            "SELECT COUNT(*) FROM drafts WHERE status = 'blocked'"
        ).fetchone()[0]
        icd_count: int = conn.execute("SELECT COUNT(*) FROM icd_parameters").fetchone()[0]
        impact_count: int = conn.execute("SELECT COUNT(*) FROM impact_reports").fetchone()[0]

    stale = get_graph().get_stale_references()

    settings = request.app.state.settings
    dotenv_path = get_dotenv_path()

    llm_status = _get_llm_status(request)

    # ---- Embedding 可用性 ----
    emb_store = getattr(request.app.state, "embedding_store", None)
    embedding_available = emb_store is not None
    sections_indexed = emb_store.section_count() if emb_store else 0
    embedding_error = getattr(request.app.state, "embedding_error", "")

    eval_total = eval_pass + eval_blocked
    eval_pass_rate = round(eval_pass / eval_total, 2) if eval_total > 0 else None

    return {
        "documents": doc_count,
        "drafts": draft_count,
        "icd_parameters": icd_count,
        "impact_reports": impact_count,
        "stale_references": len(stale),
        "llm_available": llm_status["available"],
        "llm_model": settings.llm_model,
        "llm_base_url": settings.llm_base_url,
        "llm_effective_model": llm_status["effective_model"],
        "llm_effective_base_url": llm_status["effective_base_url"],
        "llm_error": llm_status["error"],
        "embedding_available": embedding_available,
        "embedding_model": settings.embedding_model,
        "embedding_base_url": settings.embedding_base_url,
        "embedding_error": embedding_error,
        "sections_indexed": sections_indexed,
        "eval_pass_rate": eval_pass_rate,
        "eval_pass": eval_pass,
        "eval_blocked": eval_blocked,
        "config_env_file": str(dotenv_path) if dotenv_path is not None else "",
    }


def _get_llm_status(request: Request) -> dict[str, str | bool]:
    settings = request.app.state.settings
    cache_key = (
        settings.llm_model,
        settings.llm_base_url,
        bool(settings.llm_api_key),
    )
    now = monotonic()
    cached = getattr(request.app.state, "_llm_status_cache", None)
    if cached and cached.get("key") == cache_key and cached.get("expires_at", 0.0) > now:
        return cached["value"]

    value = {
        "available": False,
        "error": "",
        "effective_model": "",
        "effective_base_url": "",
    }
    try:
        from harnetics.llm.client import HarneticsLLM

        llm_client = HarneticsLLM(
            model=settings.llm_model,
            api_base=settings.llm_base_url,
            api_key=settings.llm_api_key or None,
        )
        available, error = llm_client.availability_status()
        value = {
            "available": available,
            "error": error,
            "effective_model": llm_client.model,
            "effective_base_url": llm_client.api_base or "",
        }
    except Exception as exc:
        value["error"] = f"{type(exc).__name__}: {exc}"

    request.app.state._llm_status_cache = {
        "key": cache_key,
        "expires_at": now + _LLM_STATUS_CACHE_TTL_SECONDS,
        "value": value,
    }
    return value
