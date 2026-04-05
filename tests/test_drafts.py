# [INPUT]: 依赖 fastapi.testclient、DraftService、Repository 与 DraftValidator
# [OUTPUT]: 提供草稿生成、告警、编辑与导出流程测试
# [POS]: tests 目录中的草稿工作流契约测试，锁定 Task 5 的最小闭环
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from fastapi.testclient import TestClient

from harnetics.drafts import DraftService
from harnetics.importer import ImportService
from harnetics.repository import Repository
from harnetics.validation import DraftValidator


class FakeLlmClient:
    def generate_markdown(self, *, prompt: str) -> str:
        return "## 1. 概述\n- 地面推力满足 650 kN。[CITATION:1]\n"


def test_draft_service_generates_citations_and_warnings(
    temp_db_path,
    fixture_root,
) -> None:
    repo = Repository(temp_db_path)
    importer = ImportService(repo)
    importer.import_file(fixture_root / "fixtures" / "requirements" / "DOC-SYS-001.md")
    importer.import_file(fixture_root / "fixtures" / "design" / "DOC-DES-001.md")
    importer.import_file(fixture_root / "fixtures" / "templates" / "DOC-TPL-001.md")
    importer.import_file(fixture_root / "fixtures" / "test_plans" / "DOC-TST-003.md")

    documents = repo.list_documents()
    template = repo.get_default_template()
    service = DraftService(
        repository=repo,
        llm_client=FakeLlmClient(),
        validator=DraftValidator(repo),
    )
    draft = service.generate(
        topic="TQ-12 地面试车测试大纲",
        department="动力系统部",
        target_doc_type="TestPlan",
        target_system_level="Subsystem",
        selected_document_ids=[documents[0].id or 0, documents[1].id or 0, documents[3].id or 0],
        template_id=template.id or 0,
    )

    assert draft.citations
    assert any(issue.severity == "warning" for issue in draft.issues)


def test_draft_workspace_supports_plan_edit_and_export(imported_fixture_app) -> None:
    client = TestClient(imported_fixture_app)
    documents = imported_fixture_app.state.repository.list_documents()
    template = imported_fixture_app.state.repository.get_default_template()

    plan_response = client.post(
        "/drafts/plan",
        data={
            "topic": "TQ-12 地面试车测试大纲",
            "department": "动力系统部",
            "target_doc_type": "TestPlan",
            "target_system_level": "Subsystem",
        },
    )
    assert plan_response.status_code == 200

    response = client.post(
        "/drafts",
        data={
            "topic": "TQ-12 地面试车测试大纲",
            "department": "动力系统部",
            "target_doc_type": "TestPlan",
            "target_system_level": "Subsystem",
            "selected_document_ids": [documents[0].id or 0, documents[1].id or 0],
            "template_id": template.id or 0,
        },
        follow_redirects=False,
    )
    show_response = client.get(response.headers["location"])
    draft_id = int(response.headers["location"].rstrip("/").split("/")[-1])
    edit_response = client.post(
        f"/drafts/{draft_id}/edit",
        data={"content": "## 更新后的草稿"},
        follow_redirects=False,
    )
    export_response = client.get(f"/drafts/{draft_id}/export")

    assert response.status_code == 303
    assert response.headers["location"].startswith("/drafts/")
    assert show_response.status_code == 200
    assert edit_response.status_code == 303
    assert export_response.status_code == 200
    assert export_response.headers["content-type"].startswith("text/markdown")
    assert export_response.text == "## 更新后的草稿"
