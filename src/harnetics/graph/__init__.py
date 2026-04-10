# [INPUT]: 聚合 graph 子模块的公共接口
# [OUTPUT]: 对外提供 init_db, get_connection
# [POS]: graph 包入口
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from .store import get_connection, init_db

__all__ = ["get_connection", "init_db"]
