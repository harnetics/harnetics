# [INPUT]: 依赖 pytest 的 tmp_path fixture
# [OUTPUT]: 提供 temp_db_path fixture，返回临时测试数据库路径
# [POS]: tests 目录的共享测试支架，供后续数据库相关测试复用
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from pathlib import Path

import pytest


@pytest.fixture()
def temp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"
