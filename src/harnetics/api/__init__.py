# [INPUT]: 聚合 api 子模块的公共接口
# [OUTPUT]: 对外提供 create_api_app
# [POS]: api 包入口
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from .app import create_api_app

__all__ = ["create_api_app"]
