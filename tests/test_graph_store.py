# [INPUT]: 依赖 pytest、graph.store 与 legacy repository schema
# [OUTPUT]: 提供 graph store 初始化与兼容性保护的回归测试
# [POS]: tests 目录中的图谱存储层测试，锁定新 graph schema 不再误踩旧 repository DB
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from pathlib import Path

import pytest

from harnetics.graph.indexer import DocumentIndexer
from harnetics.graph.store import init_db
from harnetics.graph import store
from harnetics.repository import Repository


def test_init_db_creates_graph_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "graph.db"

    init_db(db_path)

    import sqlite3

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("PRAGMA table_info(documents)").fetchall()

    columns = {row[1] for row in rows}
    assert {"doc_id", "content_hash", "file_path", "created_at", "updated_at"} <= columns


def test_init_db_rejects_legacy_repository_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.db"
    Repository(db_path)

    with pytest.raises(RuntimeError, match="legacy repository database"):
        init_db(db_path)


def test_document_indexer_indexes_sections_when_embedding_store_present(tmp_path: Path) -> None:
    db_path = tmp_path / "graph.db"
    init_db(db_path)

    md_path = tmp_path / "DOC-SYS-001.md"
    md_path.write_text(
        """---
title: 系统级需求
doc_type: Requirement
department: 系统工程部
system_level: System
engineering_phase: Requirement
version: v1.0
status: Approved
---
# 1. 文档说明
本文档定义系统级需求。
""",
        encoding="utf-8",
    )

    class FakeEmbeddingStore:
        def __init__(self) -> None:
            self.calls: list[tuple[str, list[str]]] = []

        def index_sections(self, doc_id: str, sections: list) -> None:
            self.calls.append((doc_id, [section.section_id for section in sections]))

    emb_store = FakeEmbeddingStore()
    indexer = DocumentIndexer(embedding_store=emb_store)

    doc = indexer.ingest_document(str(md_path))

    stored_sections = store.get_sections(doc.doc_id)
    assert len(stored_sections) == 1
    assert emb_store.calls == [(doc.doc_id, [stored_sections[0].section_id])]


def test_ingest_directory_skips_agents_markdown(tmp_path: Path) -> None:
    db_path = tmp_path / "graph.db"
    init_db(db_path)

    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    (fixture_dir / "AGENTS.md").write_text("# internal", encoding="utf-8")
    (fixture_dir / "DOC-SYS-001.md").write_text(
        """---
title: 系统级需求
doc_type: Requirement
department: 系统工程部
system_level: System
engineering_phase: Requirement
version: v1.0
status: Approved
---
# 1. 文档说明
本文档定义系统级需求。
""",
        encoding="utf-8",
    )

    docs = DocumentIndexer().ingest_directory(str(fixture_dir))

    assert [doc.doc_id for doc in docs] == ["DOC-SYS-001"]


def test_ingest_markdown_preserves_frontmatter_after_leading_comment(tmp_path: Path) -> None:
    db_path = tmp_path / "graph.db"
    init_db(db_path)

    md_path = tmp_path / "DOC-SYS-001.md"
    md_path.write_text(
        """<!-- contract comment -->
---
doc_id: DOC-SYS-001
title: 天行一号运载火箭系统级需求文档
doc_type: Requirement
department: 系统工程部
system_level: System
engineering_phase: Requirement
version: v3.1
status: Approved
---
# 1. 文档说明
本文档定义系统级需求。
""",
        encoding="utf-8",
    )

    doc = DocumentIndexer().ingest_document(str(md_path))

    assert doc.title == "天行一号运载火箭系统级需求文档"
    assert doc.doc_type == "Requirement"
    assert doc.department == "系统工程部"
    assert doc.system_level == "System"