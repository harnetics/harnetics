# [INPUT]: 依赖 fastapi.testclient、DraftService、Repository 与 DraftValidator
# [OUTPUT]: 提供草稿生成、告警、编辑与导出流程测试
# [POS]: tests 目录中的草稿工作流契约测试，锁定 Task 5 的最小闭环
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from fastapi.testclient import TestClient

from harnetics.drafts import DraftService
from harnetics.importer import ImportService
from harnetics.models import DocumentRecord
from harnetics.models import TemplateRecord
from harnetics.repository import Repository
from harnetics.validation import DraftValidator


class FakeLlmClient:
    def generate_markdown(self, *, prompt: str) -> str:
        return "## 1. 概述\n- 地面推力满足 650 kN。[CITATION:1]\n"


class StaticLlmClient:
    def __init__(self, content: str) -> None:
        self.content = content

    def generate_markdown(self, *, prompt: str) -> str:
        return self.content


class PromptCapturingLlmClient:
    def __init__(self, content: str) -> None:
        self.content = content
        self.prompts: list[str] = []

    def generate_markdown(self, *, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.content


def _load_draft_repo(temp_db_path, fixture_root):
    repo = Repository(temp_db_path)
    importer = ImportService(repo)
    importer.import_file(fixture_root / "fixtures" / "requirements" / "DOC-SYS-001.md")
    importer.import_file(fixture_root / "fixtures" / "design" / "DOC-DES-001.md")
    importer.import_file(fixture_root / "fixtures" / "templates" / "DOC-TPL-001.md")
    importer.import_file(fixture_root / "fixtures" / "test_plans" / "DOC-TST-003.md")
    return repo


def _insert_secondary_template(repo: Repository) -> int:
    document_id = repo.insert_document(
        DocumentRecord(
            id=None,
            doc_id="DOC-TPL-999",
            title="备选试验模板",
            department="试验与验证部",
            doc_type="Template",
            system_level="System",
            engineering_phase="Test",
            version="v1.0",
            status="Approved",
            source_path="fixtures/templates/DOC-TPL-999.md",
            imported_at="2026-04-06T00:00:00+00:00",
        )
    )
    return repo.upsert_template(
        TemplateRecord(
            id=None,
            document_id=document_id,
            name="备选试验模板",
            required_sections="A. 自定义章节",
            structure="## A. 自定义章节 【必填】\n> 仅用于模板选择测试",
        )
    )


def test_draft_service_generates_citations_and_warnings(
    temp_db_path,
    fixture_root,
) -> None:
    repo = _load_draft_repo(temp_db_path, fixture_root)
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


def test_draft_service_preserves_multiple_valid_citation_markers(
    temp_db_path,
    fixture_root,
) -> None:
    repo = _load_draft_repo(temp_db_path, fixture_root)
    documents = repo.list_documents()
    template = repo.get_default_template()
    first_section_id = repo.get_document_detail(documents[0].id or 0).sections[0].id or 0
    second_section_id = repo.get_document_detail(documents[1].id or 0).sections[0].id or 0
    service = DraftService(
        repository=repo,
        llm_client=StaticLlmClient(
            "## 1. 概述\n"
            f"- 第一条。[CITATION:{first_section_id}]\n"
            f"- 第二条。[CITATION:{second_section_id}]\n"
        ),
        validator=DraftValidator(repo),
    )

    draft = service.generate(
        topic="TQ-12 地面试车测试大纲",
        department="动力系统部",
        target_doc_type="TestPlan",
        target_system_level="Subsystem",
        selected_document_ids=[documents[0].id or 0, documents[1].id or 0],
        template_id=template.id or 0,
    )

    assert [citation.section_id for citation in draft.citations] == [first_section_id, second_section_id]
    assert draft.status == "ready"


def test_draft_service_skips_invalid_citation_ids_without_crashing(
    temp_db_path,
    fixture_root,
) -> None:
    repo = _load_draft_repo(temp_db_path, fixture_root)
    documents = repo.list_documents()
    template = repo.get_default_template()
    service = DraftService(
        repository=repo,
        llm_client=StaticLlmClient("## 1. 概述\n- 无效引用。[CITATION:999999]\n"),
        validator=DraftValidator(repo),
    )

    draft = service.generate(
        topic="TQ-12 地面试车测试大纲",
        department="动力系统部",
        target_doc_type="TestPlan",
        target_system_level="Subsystem",
        selected_document_ids=[documents[0].id or 0, documents[1].id or 0],
        template_id=template.id or 0,
    )

    assert draft.citations == []
    assert draft.status == "blocked"
    assert any(issue.message == "草稿缺少引用" for issue in draft.issues)


def test_draft_service_rejects_citations_from_unselected_documents(
    temp_db_path,
    fixture_root,
) -> None:
    repo = _load_draft_repo(temp_db_path, fixture_root)
    documents = repo.list_documents()
    template = repo.get_default_template()
    unselected_section_id = repo.get_document_detail(documents[1].id or 0).sections[0].id or 0
    service = DraftService(
        repository=repo,
        llm_client=StaticLlmClient(f"## 1. 概述\n- 越界引用。[CITATION:{unselected_section_id}]\n"),
        validator=DraftValidator(repo),
    )

    draft = service.generate(
        topic="TQ-12 地面试车测试大纲",
        department="动力系统部",
        target_doc_type="TestPlan",
        target_system_level="Subsystem",
        selected_document_ids=[documents[0].id or 0],
        template_id=template.id or 0,
    )

    assert draft.citations == []
    assert draft.status == "blocked"
    assert any(issue.message == "草稿缺少引用" for issue in draft.issues)


def test_draft_service_uses_requested_template_in_prompt(
    temp_db_path,
    fixture_root,
) -> None:
    repo = _load_draft_repo(temp_db_path, fixture_root)
    documents = repo.list_documents()
    alternate_template_id = _insert_secondary_template(repo)
    llm_client = PromptCapturingLlmClient("## 1. 概述\n- 内容。[CITATION:1]\n")
    service = DraftService(
        repository=repo,
        llm_client=llm_client,
        validator=DraftValidator(repo),
    )

    service.generate(
        topic="TQ-12 地面试车测试大纲",
        department="动力系统部",
        target_doc_type="TestPlan",
        target_system_level="Subsystem",
        selected_document_ids=[documents[0].id or 0, documents[1].id or 0],
        template_id=alternate_template_id,
    )

    assert "## A. 自定义章节 【必填】" in llm_client.prompts[0]
    assert "## 1. 概述 【必填】" not in llm_client.prompts[0]


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


def test_plan_route_returns_400_when_no_template_exists(temp_app) -> None:
    client = TestClient(temp_app)

    response = client.post(
        "/drafts/plan",
        data={
            "topic": "TQ-12 地面试车测试大纲",
            "department": "动力系统部",
            "target_doc_type": "TestPlan",
            "target_system_level": "Subsystem",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "no template available for draft planning"


def test_edit_recomputes_draft_citations_issues_and_status(imported_fixture_app) -> None:
    client = TestClient(imported_fixture_app)
    documents = imported_fixture_app.state.repository.list_documents()
    template = imported_fixture_app.state.repository.get_default_template()

    create_response = client.post(
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
    draft_id = int(create_response.headers["location"].rstrip("/").split("/")[-1])

    initial_draft = imported_fixture_app.state.repository.get_draft_detail(draft_id)
    assert initial_draft.status == "ready"
    assert initial_draft.citations

    edit_response = client.post(
        f"/drafts/{draft_id}/edit",
        data={"content": "不合格正文"},
        follow_redirects=False,
    )
    workspace_response = client.get(edit_response.headers["location"])
    updated_draft = imported_fixture_app.state.repository.get_draft_detail(draft_id)

    assert edit_response.status_code == 303
    assert updated_draft.status == "blocked"
    assert updated_draft.citations == []
    assert any(issue.message == "草稿缺少引用" for issue in updated_draft.issues)
    assert any(issue.message == "模板必填章节缺失：1. 概述" for issue in updated_draft.issues)
    assert "状态：blocked" in workspace_response.text
    assert "无引注。" in workspace_response.text
    assert "状态：ready" not in workspace_response.text


def test_export_updates_draft_exported_at(imported_fixture_app) -> None:
    client = TestClient(imported_fixture_app)
    documents = imported_fixture_app.state.repository.list_documents()
    template = imported_fixture_app.state.repository.get_default_template()

    create_response = client.post(
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
    draft_id = int(create_response.headers["location"].rstrip("/").split("/")[-1])

    before_export = imported_fixture_app.state.repository.get_draft_detail(draft_id)
    export_response = client.get(f"/drafts/{draft_id}/export")
    after_export = imported_fixture_app.state.repository.get_draft_detail(draft_id)

    assert before_export.exported_at is None
    assert export_response.status_code == 200
    assert after_export.exported_at is not None
