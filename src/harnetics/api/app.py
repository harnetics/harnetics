# [INPUT]: 依赖 FastAPI、pathlib、graph.store、config 与所有 api.routes.*
# [OUTPUT]: 对外提供 create_api_app() 工厂函数
# [POS]: api 包的应用装配层，注册全量 API 路由 + SPA 前端托管，挂载 RuntimeSettingsManager
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from harnetics.config import get_settings, RuntimeSettingsManager
from harnetics.graph.store import init_db
from harnetics.api.routes.documents import router as documents_api_router
from harnetics.api.routes.evaluate import router as evaluate_router
from harnetics.api.routes.draft import router as draft_router
from harnetics.api.routes.impact import router as impact_router
from harnetics.api.routes.graph import router as graph_router
from harnetics.api.routes.status import router as status_router
from harnetics.api.routes.settings import router as settings_router
from harnetics.api.routes.evolution import router as evolution_router
from harnetics.api.routes.fixture import router as fixture_router


def _configure_harnetics_logging() -> None:
    app_logger = logging.getLogger("harnetics")
    uvicorn_logger = logging.getLogger("uvicorn.error")
    if uvicorn_logger.handlers:
        app_logger.handlers = uvicorn_logger.handlers
        app_logger.propagate = False
    app_logger.setLevel(logging.INFO)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """应用启动时初始化图谱数据库与向量索引。"""
    settings = get_settings()
    init_db(settings.graph_db_path)

    # ---- 初始化 EmbeddingStore（可能失败，降级为 None） ----
    emb_store = None
    embedding_error = ""
    try:
        from harnetics.graph.embeddings import EmbeddingStore
        emb_store = EmbeddingStore(
            persist_path=str(settings.chromadb_path),
            model_name=settings.embedding_model,
            api_key=settings.embedding_api_key,
            base_url=settings.embedding_base_url,
        )
    except Exception as exc:
        embedding_error = f"{type(exc).__name__}: {exc}"
    app.state.embedding_store = emb_store
    app.state.embedding_error = embedding_error
    app.state.embedding_collection_reset = bool(emb_store and emb_store.collection_was_reset)

    yield


def create_api_app() -> FastAPI:
    settings = get_settings()
    _configure_harnetics_logging()

    # ---- 工厂阶段先初始化图谱库，确保无 lifespan 的测试客户端也能安全访问状态端点 ----
    init_db(settings.graph_db_path)

    app = FastAPI(title="Harnetics", lifespan=_lifespan)

    app.state.settings = settings
    app.state.runtime_settings = RuntimeSettingsManager(settings)

    # ---- API 路由 ----
    app.include_router(documents_api_router)
    app.include_router(evaluate_router)
    app.include_router(draft_router)
    app.include_router(impact_router)
    app.include_router(graph_router)
    app.include_router(status_router)
    app.include_router(settings_router)
    app.include_router(evolution_router)
    app.include_router(fixture_router)

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    # ---- SPA 前端托管 (production build) ----
    dist_dir = Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist"
    if dist_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(dist_dir / "assets")), name="spa-assets")

        @app.get("/{full_path:path}")
        async def spa_fallback(request: Request, full_path: str):
            """SPA fallback: 非 API 路由一律返回 index.html。"""
            file_path = dist_dir / full_path
            if file_path.is_file():
                return FileResponse(str(file_path))
            return FileResponse(str(dist_dir / "index.html"))

    return app
