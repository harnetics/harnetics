# [INPUT]: 依赖 pytest 的 tmp_path fixture 与当前测试文件位置
# [OUTPUT]: 提供 temp_db_path 与 fixture_root fixture，返回临时数据库路径和仓库根路径
# [POS]: tests 目录的共享测试支架，供数据库与 fixture 路径相关测试复用
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from pathlib import Path

import pytest


@pytest.fixture()
def temp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


@pytest.fixture()
def fixture_root() -> Path:
    return Path(__file__).resolve().parents[1]
