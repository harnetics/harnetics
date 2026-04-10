# [INPUT]: 依赖 pytest 的 tmp_path fixture、FastAPI app 工厂与导入/仓储/草稿服务
# [OUTPUT]: 提供 temp_db_path、fixture_root、temp_app 与 imported_fixture_app 夹具
# [POS]: tests 目录的共享测试支架，供 catalog、retrieval 与 draft workflow 复用
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from pathlib import Path
from types import SimpleNamespace

import pytest

from harnetics.app import create_app
from harnetics.drafts import DraftService
from harnetics.graph.store import init_db, get_connection
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


@pytest.fixture()
def graph_db_path(tmp_path: Path) -> Path:
    """初始化图谱 SQLite 数据库并返回路径。"""
    db_path = tmp_path / "graph_test.db"
    init_db(db_path)
    return db_path


@pytest.fixture()
def graph_conn(graph_db_path: Path):
    """获取图谱数据库连接，测试结束后关闭。"""
    with get_connection(graph_db_path) as conn:
        yield conn


@pytest.fixture()
def fixture_doc_paths(fixture_root: Path) -> dict[str, Path]:
    """常用 fixture 文档路径映射。"""
    base = fixture_root / "fixtures"
    return {
        "sys_req": base / "requirements" / "DOC-SYS-001.md",
        "design": base / "design" / "DOC-DES-001.md",
        "template": base / "templates" / "DOC-TPL-001.md",
        "test_plan": base / "test_plans" / "DOC-TST-003.md",
        "icd": base / "icd" / "DOC-ICD-001.yaml",
    }
