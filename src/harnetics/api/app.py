# [INPUT]: 依赖 FastAPI、Jinja2、pathlib、graph.store 与 config
# [OUTPUT]: 对外提供 create_api_app() 工厂函数
# [POS]: api 包的应用装配层，独立于旧 app.py，支持 lifespan 启动 init_db
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from harnetics.config import get_settings
from harnetics.graph.store import init_db
from harnetics.web.routes import router as web_router


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """应用启动时初始化图谱数据库。"""
    settings = get_settings()
    init_db(settings.graph_db_path)
    yield


def create_api_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Harnetics", lifespan=_lifespan)

    # ---- 静态文件 ----
    static_dir = Path(__file__).resolve().parent.parent / "web" / "static"
    if static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # ---- 模板 ----
    templates_dir = Path(__file__).resolve().parent.parent / "web" / "templates"
    app.state.templates = Jinja2Templates(directory=str(templates_dir))
    app.state.settings = settings

    # ---- 路由（复用现有 web router） ----
    app.include_router(web_router)

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    return app
