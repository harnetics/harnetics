# [INPUT]: 依赖 sqlite3、pathlib 与同目录 schema.sql
# [OUTPUT]: 对外提供 init_db() 和 get_connection() 上下文管理器
# [POS]: graph 包的 SQLite 连接管理器，负责图谱库初始化与连接生命周期
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

_SCHEMA_PATH = Path(__file__).with_name("schema.sql")

# ---- 模块级默认路径，由 init_db() 设置 ----
_db_path: Path = Path("var/harnetics.db")


def init_db(db_path: Path | str | None = None) -> None:
    """建表 + 启用外键约束。启动时调用一次即可。"""
    global _db_path
    if db_path is not None:
        _db_path = Path(db_path)
    _db_path.parent.mkdir(parents=True, exist_ok=True)
    schema_sql = _SCHEMA_PATH.read_text(encoding="utf-8")
    with _connect(_db_path) as conn:
        conn.executescript(schema_sql)


@contextmanager
def get_connection(db_path: Path | str | None = None) -> Generator[sqlite3.Connection, None, None]:
    """获取一个启用外键约束的 SQLite 连接，自动提交/回滚。"""
    path = Path(db_path) if db_path is not None else _db_path
    conn = _connect(path)
    try:
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn
