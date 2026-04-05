# [INPUT]: 依赖本包内部的 create_app、Settings 与 get_settings
# [OUTPUT]: 提供包级公共入口 create_app、Settings、get_settings
# [POS]: harnetics 包的轻量门面，供外部直接导入最小 API
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

import os

from .app import create_app
from .config import Settings, get_settings

__all__ = ["Settings", "create_app", "get_settings"]


def pytest_main() -> int:
    os.environ.setdefault("TMPDIR", "/tmp")
    os.environ.setdefault("TEMP", "/tmp")
    os.environ.setdefault("TMP", "/tmp")

    from pytest import console_main

    return console_main()
