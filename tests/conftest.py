# [INPUT]: 依赖 pytest 的 tmp_path fixture、FastAPI app 工厂与导入/仓储/草稿服务
# [OUTPUT]: 提供 temp_db_path、fixture_root、temp_app 与 imported_fixture_app 夹具
# [POS]: tests 目录的共享测试支架，供 catalog、retrieval 与 draft workflow 复用
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from pathlib import Path
from types import SimpleNamespace

import pytest

from harnetics.app import create_app
from harnetics.drafts import DraftService
from harnetics.importer import ImportService
from harnetics.repository import Repository
from harnetics.retrieval import RetrievalPlanner
from harnetics.validation import DraftValidator


class FakeLlmClient:
    def generate_markdown(self, *, prompt: str) -> str:
        if "SECTION:1" in prompt:
            citation = 1
        else:
            citation = 2
        return f"## 1. 概述\n- 地面推力满足 650 kN。[CITATION:{citation}]\n"


@pytest.fixture()
def temp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


@pytest.fixture()
def fixture_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture()
def temp_app(temp_db_path: Path, tmp_path: Path):
    app = create_app()
    repository = Repository(temp_db_path)
    app.state.repository = repository
    app.state.import_service = ImportService(repository)
    app.state.settings = SimpleNamespace(raw_upload_dir=tmp_path / "uploads")
    app.state.retrieval_planner = RetrievalPlanner(repository)
    app.state.draft_service = DraftService(
        repository=repository,
        llm_client=FakeLlmClient(),
        validator=DraftValidator(repository),
    )
    return app


@pytest.fixture()
def imported_fixture_app(temp_app, fixture_root: Path):
    importer = temp_app.state.import_service
    importer.import_file(fixture_root / "fixtures" / "requirements" / "DOC-SYS-001.md")
    importer.import_file(fixture_root / "fixtures" / "design" / "DOC-DES-001.md")
    importer.import_file(fixture_root / "fixtures" / "templates" / "DOC-TPL-001.md")
    importer.import_file(fixture_root / "fixtures" / "test_plans" / "DOC-TST-003.md")
    return temp_app
