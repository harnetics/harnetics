# [INPUT]: 依赖 pytest、Path、Repository 与 ImportService
# [OUTPUT]: 提供 controlled Markdown/YAML 导入与缺失元数据拦截的回归测试
# [POS]: tests 目录中的导入服务契约测试，锁定最小导入行为
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from pathlib import Path

import pytest

from harnetics.importer import ImportService
from harnetics.repository import Repository


def test_import_service_ingests_controlled_markdown(temp_db_path: Path, fixture_root: Path) -> None:
    repo = Repository(temp_db_path)
    service = ImportService(repo)

    result = service.import_file(fixture_root / "fixtures" / "requirements" / "DOC-SYS-001.md")
    stored = repo.list_documents()
    detail = repo.get_document_detail(stored[0].id or 0)

    assert result.document.doc_id == "DOC-SYS-001"
    assert result.section_count == 1
    assert len(stored) == 1
    assert detail.document.doc_id == "DOC-SYS-001"
    assert detail.sections[0].heading == "body"
    assert detail.sections[0].level == 1
    assert detail.sections[0].sequence == 1
    assert detail.sections[0].trace_refs == ""
    assert "# 天行一号运载火箭系统级需求文档" in detail.sections[0].content


def test_import_service_ingests_controlled_yaml(temp_db_path: Path, fixture_root: Path) -> None:
    repo = Repository(temp_db_path)
    service = ImportService(repo)

    result = service.import_file(fixture_root / "fixtures" / "icd" / "DOC-ICD-001.yaml")
    stored = repo.list_documents()
    detail = repo.get_document_detail(stored[0].id or 0)

    assert result.document.doc_type == "ICD"
    assert result.section_count == len(detail.sections)
    assert len(stored) == 1
    assert detail.document.doc_id == "DOC-ICD-001"
    assert detail.sections[0].heading == "一级发动机地面推力"
    assert detail.sections[0].level == 2
    assert detail.sections[0].sequence == 1
    assert detail.sections[0].trace_refs == ""
    assert "param_id: ICD-PRP-001" in detail.sections[0].content


def test_import_service_rejects_missing_metadata(temp_db_path: Path, tmp_path: Path) -> None:
    repo = Repository(temp_db_path)
    service = ImportService(repo)
    bad_file = tmp_path / "bad.md"
    bad_file.write_text(
        """<!--
[INPUT]: test
[OUTPUT]: test
[POS]: test
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->

---
title: missing doc_id
version: v1.0
status: Approved
department: 系统工程部
doc_type: Requirement
system_level: System
engineering_phase: Requirement
---

# body
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing required metadata"):
        service.import_file(bad_file)
