# [INPUT]: 依赖 FastAPI Request、config、graph.store、repository
# [OUTPUT]: 对外提供依赖注入 provider 函数
# [POS]: api 包的 DI 层，将配置与存储注入路由
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

import sqlite3
from typing import Generator

from fastapi import Request

from harnetics.config import Settings, get_settings
from harnetics.graph.store import get_connection


def dep_settings(request: Request) -> Settings:
    return request.app.state.settings


def dep_graph_connection(request: Request) -> Generator[sqlite3.Connection, None, None]:
    with get_connection(request.app.state.settings.graph_db_path) as conn:
        yield conn
