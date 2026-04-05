# [INPUT]: 依赖 FastAPI 与本地配置工厂 get_settings
# [OUTPUT]: 提供 create_app()，并暴露 /health 健康检查路由
# [POS]: harnetics 的应用装配层，负责把配置挂到 app.state 上
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from fastapi import FastAPI

from .config import get_settings


def create_app() -> FastAPI:
    app = FastAPI(title="Harnetics")
    app.state.settings = get_settings()

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    return app
