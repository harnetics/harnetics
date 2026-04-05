# [INPUT]: 依赖 pytest、harnetics.models 与 harnetics.repository
# [OUTPUT]: 提供 SQLite 仓储与领域记录的回归测试
# [POS]: tests 目录中的数据库层契约测试，先锁定最小持久化行为
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

import pytest
from types import SimpleNamespace

from harnetics.models import DocumentRecord, DraftRecord, SectionRecord
from harnetics.repository import Repository


def test_repository_stores_document_tree(temp_db_path) -> None:
    repo = Repository(temp_db_path)
    document_id = repo.insert_document(
        DocumentRecord(
            id=None,
            doc_id="DOC-SYS-001",
            title="系统级需求",
            department="系统工程部",
            doc_type="Requirement",
            system_level="System",
            engineering_phase="Requirement",
            version="v3.1",
            status="Approved",
            source_path="fixtures/requirements/DOC-SYS-001.md",
            imported_at="2026-04-06T00:00:00+00:00",
        )
    )
    repo.replace_sections(
        document_id,
        [
            SectionRecord(
                id=None,
                document_id=document_id,
                heading="1. 文档说明",
                level=2,
                sequence=1,
                content="本文档定义系统级需求。",
                trace_refs="",
            )
        ],
    )

    stored = repo.list_documents()
    detail = repo.get_document_detail(document_id)

    assert len(stored) == 1
    assert stored[0].doc_id == "DOC-SYS-001"
    assert detail.sections[0].heading == "1. 文档说明"


def test_repository_rejects_duplicate_doc_version(temp_db_path) -> None:
    repo = Repository(temp_db_path)
    record = DocumentRecord(
        id=None,
        doc_id="DOC-SYS-001",
        title="系统级需求",
        department="系统工程部",
        doc_type="Requirement",
        system_level="System",
        engineering_phase="Requirement",
        version="v3.1",
        status="Approved",
        source_path="fixtures/requirements/DOC-SYS-001.md",
        imported_at="2026-04-06T00:00:00+00:00",
    )
    repo.insert_document(record)

    with pytest.raises(ValueError, match="duplicate document version"):
        repo.insert_document(record)


def test_repository_defaults_missing_issue_source_refs(temp_db_path) -> None:
    repo = Repository(temp_db_path)
    draft_id = repo.insert_draft(
        DraftRecord(
            id=None,
            topic="审阅",
            department="系统工程部",
            target_doc_type="Requirement",
            target_system_level="System",
            status="generated",
            content_markdown="正文",
            exported_at=None,
        )
    )

    repo.insert_validation_issues(
        draft_id,
        [SimpleNamespace(severity="warning", message="missing reference")],
    )

    detail = repo.get_draft_detail(draft_id)

    assert len(detail.issues) == 1
    assert detail.issues[0].severity == "warning"
    assert detail.issues[0].message == "missing reference"
    assert detail.issues[0].source_refs == ""
