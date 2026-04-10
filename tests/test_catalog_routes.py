# [INPUT]: 依赖 fastapi.testclient、catalog 夹具与上传/仓储边界
# [OUTPUT]: 提供上传校验、文档列表过滤和文档详情页面的回归测试
# [POS]: tests 目录中的 catalog 路由契约测试，先锁定最小 HTTP 行为
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from pathlib import Path

from fastapi.testclient import TestClient

from harnetics.app import create_app


def test_default_create_app_can_serve_documents_in_temp_cwd(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    client = TestClient(create_app())

    response = client.get("/documents")

    assert response.status_code == 200
    assert "暂无符合条件的文档" in response.text


def test_upload_route_rejects_missing_metadata(temp_app) -> None:
    client = TestClient(temp_app)

    response = client.post(
        "/documents/import",
        files={"file": ("bad.md", "# no front matter", "text/markdown")},
    )

    assert response.status_code == 400


def test_upload_route_rejects_path_traversal(temp_app, tmp_path: Path) -> None:
    client = TestClient(temp_app)
    uploads_dir = temp_app.state.settings.raw_upload_dir
    escaped_path = tmp_path / "escape.md"

    response = client.post(
        "/documents/import",
        files={
            "file": (
                "../escape.md",
                """---
doc_id: DOC-SYS-001
title: escape attempt
version: v1.0
status: Approved
department: 系统工程部
doc_type: Requirement
system_level: System
engineering_phase: Requirement
---
# body
""",
                "text/markdown",
            )
        },
    )

    assert response.status_code == 400
    assert not escaped_path.exists()
    assert not uploads_dir.exists() or not any(uploads_dir.iterdir())


def test_upload_route_rejects_malformed_yaml(temp_app) -> None:
    client = TestClient(temp_app)
    uploads_dir = temp_app.state.settings.raw_upload_dir

    response = client.post(
        "/documents/import",
        files={
            "file": (
                "bad.yaml",
                "metadata: [unclosed",
                "application/x-yaml",
            )
        },
    )

    assert response.status_code == 400
    assert not uploads_dir.exists() or not any(uploads_dir.iterdir())


def test_upload_route_keeps_existing_raw_file_intact(temp_app) -> None:
    client = TestClient(temp_app)
    uploads_dir = temp_app.state.settings.raw_upload_dir
    upload_name = "same-name.md"
    original_content = """---
doc_id: DOC-SYS-001
title: original
version: v1.0
status: Approved
department: 系统工程部
doc_type: Requirement
system_level: System
engineering_phase: Requirement
---
# original body
"""

    first = client.post(
        "/documents/import",
        files={"file": (upload_name, original_content, "text/markdown")},
    )
    assert first.status_code == 200

    stored_path = uploads_dir / upload_name
    assert stored_path.read_text(encoding="utf-8") == original_content

    second = client.post(
        "/documents/import",
        files={
            "file": (
                upload_name,
                """---
doc_id: DOC-SYS-001
title: updated
version: v1.1
status: Approved
department: 系统工程部
doc_type: Requirement
system_level: System
engineering_phase: Requirement
---
# updated body
""",
                "text/markdown",
            )
        },
    )

    assert second.status_code == 400
    assert stored_path.read_text(encoding="utf-8") == original_content
    assert uploads_dir.exists()


def test_documents_page_lists_and_filters_imported_docs(imported_fixture_app) -> None:
    client = TestClient(imported_fixture_app)

    response = client.get("/documents?department=系统工程部")

    assert response.status_code == 200
    assert "DOC-SYS-001" in response.text
    assert "DOC-DES-001" not in response.text


def test_documents_page_treats_empty_department_as_unfiltered(imported_fixture_app) -> None:
    client = TestClient(imported_fixture_app)

    response = client.get("/documents?department=")

    assert response.status_code == 200
    assert "DOC-SYS-001" in response.text
    assert "DOC-DES-001" in response.text


def test_document_detail_shows_sections(imported_fixture_app) -> None:
    client = TestClient(imported_fixture_app)
    document_id = imported_fixture_app.state.repository.list_documents()[0].id or 0

    response = client.get(f"/documents/{document_id}")

    assert response.status_code == 200
    assert "文档说明" in response.text
    assert "本文档定义天行一号" in response.text


def test_document_detail_returns_404_for_missing_document(imported_fixture_app) -> None:
    client = TestClient(imported_fixture_app)

    response = client.get("/documents/999")

    assert response.status_code == 404
