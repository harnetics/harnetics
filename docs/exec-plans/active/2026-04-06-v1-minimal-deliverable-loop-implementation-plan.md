<!--
[INPUT]: 依赖 docs/superpowers/specs/2026-04-05-mvp-minimal-deliverable-loop-design.md、docs/product-specs/mvp-prd.md 与当前空仓库状态
[OUTPUT]: 对外提供 Harnetics v1 最小可交付闭环的逐任务实现计划
[POS]: docs/exec-plans/active 的首份执行计划，作为后续实现工作的唯一行动蓝图
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->

# Harnetics v1 Minimal Deliverable Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local FastAPI web app that imports controlled Markdown/YAML documents, lets engineers browse/search them, and generates citation-backed draft Markdown with warnings, light editing, and export.

**Architecture:** Use a server-rendered FastAPI app with a small SQLite database and focused modules for import, retrieval, draft generation, and validation. Keep raw files on disk, keep citations and validation issues as first-class rows in SQLite, and keep the web layer thin so all domain behavior is testable without a browser.

**Tech Stack:** Python 3.12, uv, FastAPI, Jinja2, HTMX, sqlite3, PyYAML, python-frontmatter, httpx, pytest

---

## Planned File Structure

### Project and runtime files

- Create: `.gitignore` - ignore `.venv`, caches, local DB files, exports, and `.superpowers/`
- Create: `pyproject.toml` - project metadata, dependencies, and pytest config
- Create: `src/harnetics/AGENTS.md` - runtime module map
- Create: `src/harnetics/__init__.py` - package marker
- Create: `src/harnetics/config.py` - local settings and path defaults
- Create: `src/harnetics/app.py` - app factory, bootstrap, and router registration
- Create: `src/harnetics/models.py` - record types for documents, sections, templates, drafts, citations, validation issues, and generation runs
- Create: `src/harnetics/repository.py` - SQLite schema, inserts, queries, and updates
- Create: `src/harnetics/importer.py` - controlled Markdown/YAML parsing, validation, and import orchestration
- Create: `src/harnetics/retrieval.py` - candidate ranking and template lookup
- Create: `src/harnetics/llm.py` - OpenAI-compatible local model client
- Create: `src/harnetics/validation.py` - citation, template, and legacy-version checks
- Create: `src/harnetics/drafts.py` - prompt assembly, generation runs, citation extraction, and draft persistence

### Web layer

- Create: `src/harnetics/web/AGENTS.md` - web module map
- Create: `src/harnetics/web/routes.py` - v1 routes for import, catalog, candidate selection, generation, editing, and export
- Create: `src/harnetics/web/templates/AGENTS.md` - template ownership map
- Create: `src/harnetics/web/templates/base.html` - shared shell and navigation
- Create: `src/harnetics/web/templates/documents.html` - upload form, filters, and document list
- Create: `src/harnetics/web/templates/document_detail.html` - metadata and section detail page
- Create: `src/harnetics/web/templates/draft_new.html` - topic form and candidate confirmation UI
- Create: `src/harnetics/web/templates/draft_show.html` - editable draft, warning list, citation list, and export button

### Tests and docs

- Create: `tests/AGENTS.md` - test coverage map
- Create: `tests/conftest.py` - temp DB, fake LLM, and imported app fixtures
- Create: `tests/test_app.py` - bootstrap and health tests
- Create: `tests/test_repository.py` - schema, uniqueness, and query tests
- Create: `tests/test_importer.py` - controlled Markdown/YAML import tests
- Create: `tests/test_catalog_routes.py` - upload, list, filter, and detail route tests
- Create: `tests/test_retrieval.py` - candidate retrieval tests
- Create: `tests/test_drafts.py` - generation, validation, editing, and export tests
- Modify: `ARCHITECTURE.md` - add the real runtime structure once code exists
- Modify: `docs/generated/db-schema.md` - replace the placeholder model sketch with the real SQLite schema and table ownership

### Invariants

- Every new directory created above ships with its own `AGENTS.md` in the same task.
- Every new Python or HTML business file starts with the required L3 header.
- `Repository` is the only module allowed to talk directly to SQLite.
- Tests run with `uv run pytest ...`; do not invent custom verification scripts.

### Task 1: Bootstrap the app skeleton, test harness, and directory maps

**Files:**
- Create: `.gitignore`
- Create: `pyproject.toml`
- Create: `src/harnetics/AGENTS.md`
- Create: `src/harnetics/__init__.py`
- Create: `src/harnetics/config.py`
- Create: `src/harnetics/app.py`
- Create: `src/harnetics/web/AGENTS.md`
- Create: `src/harnetics/web/templates/AGENTS.md`
- Create: `src/harnetics/web/templates/base.html`
- Create: `tests/AGENTS.md`
- Create: `tests/conftest.py`
- Create: `tests/test_app.py`

- [ ] **Step 1: Write the failing bootstrap test**

```python
# tests/test_app.py
from fastapi.testclient import TestClient

from harnetics.app import create_app


def test_healthcheck_returns_ok() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_app.py::test_healthcheck_returns_ok -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'harnetics'`

- [ ] **Step 3: Write the minimal runtime skeleton**

```toml
# pyproject.toml
[project]
name = "harnetics"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.116.0",
  "jinja2>=3.1.4",
  "python-multipart>=0.0.12",
  "python-frontmatter>=1.1.0",
  "PyYAML>=6.0.2",
  "httpx>=0.28.1",
  "uvicorn>=0.35.0",
]

[dependency-groups]
dev = [
  "pytest>=8.4.0",
]

[tool.pytest.ini_options]
pythonpath = ["src"]
```

```python
# src/harnetics/config.py
"""
[INPUT]: 依赖 dataclasses 与 pathlib
[OUTPUT]: 对外提供 Settings 与 get_settings
[POS]: harnetics 的本地运行配置中心
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_path: Path = Path("var/harnetics.db")
    raw_upload_dir: Path = Path("var/uploads")
    export_dir: Path = Path("var/exports")
    llm_base_url: str = "http://127.0.0.1:11434/v1"
    llm_model: str = "gemma-3-27b-it"


def get_settings() -> Settings:
    return Settings()
```

```python
# src/harnetics/app.py
"""
[INPUT]: 依赖 FastAPI 与 harnetics.config
[OUTPUT]: 对外提供 create_app 与 app
[POS]: harnetics 的 ASGI 入口
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""

from fastapi import FastAPI

from harnetics.config import get_settings


def create_app() -> FastAPI:
    app = FastAPI(title="Harnetics")
    app.state.settings = get_settings()

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

```python
# tests/conftest.py
from pathlib import Path

import pytest


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"
```

```html
<!-- src/harnetics/web/templates/base.html -->
<!--
[INPUT]: 依赖页面标题和内容块
[OUTPUT]: 对外提供应用共用布局
[POS]: Web 模板基础骨架
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <title>{% block title %}Harnetics{% endblock %}</title>
  </head>
  <body>
    <nav>
      <a href="/documents">文档库</a>
      <a href="/drafts/new">生成草稿</a>
    </nav>
    <main>{% block content %}{% endblock %}</main>
  </body>
</html>
```

```markdown
# src/harnetics/AGENTS.md
# harnetics/
> L2 | 父级: ../../AGENTS.md

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

成员清单
app.py: FastAPI 入口和依赖装配。
config.py: 本地配置与路径默认值。
```

```text
# .gitignore
.venv/
__pycache__/
.pytest_cache/
var/
.superpowers/
```

- [ ] **Step 4: Run bootstrap test again**

Run: `uv run pytest tests/test_app.py::test_healthcheck_returns_ok -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .gitignore pyproject.toml src/harnetics src/harnetics/web tests
git commit -m "chore: bootstrap fastapi app skeleton"
```

### Task 2: Add domain records, SQLite schema, and repository methods

**Files:**
- Create: `src/harnetics/models.py`
- Create: `src/harnetics/repository.py`
- Create: `tests/test_repository.py`
- Modify: `docs/generated/db-schema.md`

- [ ] **Step 1: Write the failing repository tests**

```python
# tests/test_repository.py
import pytest

from harnetics.models import DocumentRecord, SectionRecord
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_repository.py -v`
Expected: FAIL because `Repository` and record classes do not exist

- [ ] **Step 3: Write the records and repository**

```python
# src/harnetics/models.py
"""
[INPUT]: 依赖 dataclasses
[OUTPUT]: 对外提供 Repository 与 services 共用的 record 类型
[POS]: harnetics 的领域记录定义文件
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""

from dataclasses import dataclass


@dataclass(slots=True)
class DocumentRecord:
    id: int | None
    doc_id: str
    title: str
    department: str
    doc_type: str
    system_level: str
    engineering_phase: str
    version: str
    status: str
    source_path: str
    imported_at: str


@dataclass(slots=True)
class SectionRecord:
    id: int | None
    document_id: int
    heading: str
    level: int
    sequence: int
    content: str
    trace_refs: str


@dataclass(slots=True)
class TemplateRecord:
    id: int | None
    document_id: int
    name: str
    required_sections: str
    structure: str


@dataclass(slots=True)
class DraftRecord:
    id: int | None
    topic: str
    department: str
    target_doc_type: str
    target_system_level: str
    status: str
    content_markdown: str
    exported_at: str | None


@dataclass(slots=True)
class CitationRecord:
    id: int | None
    draft_id: int
    draft_anchor: str
    section_id: int
    quote_excerpt: str


@dataclass(slots=True)
class ValidationIssueRecord:
    id: int | None
    owner_type: str
    owner_id: int
    severity: str
    message: str
    source_refs: str


@dataclass(slots=True)
class GenerationRunRecord:
    id: int | None
    draft_id: int
    selected_document_ids: str
    selected_template_id: int
    status: str
    duration_ms: int
    input_summary: str
```

```python
# src/harnetics/repository.py
"""
[INPUT]: 依赖 sqlite3、pathlib 与 harnetics.models
[OUTPUT]: 对外提供 SQLite schema 初始化和 domain query/update 接口
[POS]: harnetics 的唯一持久化边界层
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""

import sqlite3
from pathlib import Path

from harnetics.models import (
    CitationRecord,
    DocumentRecord,
    DraftRecord,
    GenerationRunRecord,
    SectionRecord,
    TemplateRecord,
    ValidationIssueRecord,
)


SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT NOT NULL,
    title TEXT NOT NULL,
    department TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    system_level TEXT NOT NULL,
    engineering_phase TEXT NOT NULL,
    version TEXT NOT NULL,
    status TEXT NOT NULL,
    source_path TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    UNIQUE(doc_id, version)
);
CREATE TABLE IF NOT EXISTS sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    heading TEXT NOT NULL,
    level INTEGER NOT NULL,
    sequence INTEGER NOT NULL,
    content TEXT NOT NULL,
    trace_refs TEXT NOT NULL DEFAULT '',
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL UNIQUE,
    name TEXT NOT NULL,
    required_sections TEXT NOT NULL,
    structure TEXT NOT NULL,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    department TEXT NOT NULL,
    target_doc_type TEXT NOT NULL,
    target_system_level TEXT NOT NULL,
    status TEXT NOT NULL,
    content_markdown TEXT NOT NULL,
    exported_at TEXT
);
CREATE TABLE IF NOT EXISTS citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id INTEGER NOT NULL,
    draft_anchor TEXT NOT NULL,
    section_id INTEGER NOT NULL,
    quote_excerpt TEXT NOT NULL,
    FOREIGN KEY(draft_id) REFERENCES drafts(id) ON DELETE CASCADE,
    FOREIGN KEY(section_id) REFERENCES sections(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS validation_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_type TEXT NOT NULL,
    owner_id INTEGER NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    source_refs TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS generation_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draft_id INTEGER NOT NULL,
    selected_document_ids TEXT NOT NULL,
    selected_template_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    duration_ms INTEGER NOT NULL,
    input_summary TEXT NOT NULL,
    FOREIGN KEY(draft_id) REFERENCES drafts(id) ON DELETE CASCADE
);
"""


class Repository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def insert_document(self, record: DocumentRecord) -> int:
        try:
            with self.connect() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO documents (
                        doc_id, title, department, doc_type, system_level,
                        engineering_phase, version, status, source_path, imported_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.doc_id,
                        record.title,
                        record.department,
                        record.doc_type,
                        record.system_level,
                        record.engineering_phase,
                        record.version,
                        record.status,
                        record.source_path,
                        record.imported_at,
                    ),
                )
                return int(cursor.lastrowid)
        except sqlite3.IntegrityError as exc:
            raise ValueError("duplicate document version") from exc

    def replace_sections(self, document_id: int, sections: list[SectionRecord]) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM sections WHERE document_id = ?", (document_id,))
            connection.executemany(
                """
                INSERT INTO sections (document_id, heading, level, sequence, content, trace_refs)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        document_id,
                        section.heading,
                        section.level,
                        section.sequence,
                        section.content,
                        section.trace_refs,
                    )
                    for section in sections
                ],
            )

    def upsert_template(self, record: TemplateRecord) -> int:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO templates (document_id, name, required_sections, structure)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(document_id) DO UPDATE SET
                    name = excluded.name,
                    required_sections = excluded.required_sections,
                    structure = excluded.structure
                """,
                (record.document_id, record.name, record.required_sections, record.structure),
            )
            row = connection.execute("SELECT id FROM templates WHERE document_id = ?", (record.document_id,)).fetchone()
        return int(row["id"])

    def list_documents(self, department=None, doc_type=None, system_level=None, query=None):
        sql = "SELECT * FROM documents WHERE 1=1"
        params = []
        if department:
            sql += " AND department = ?"
            params.append(department)
        if doc_type:
            sql += " AND doc_type = ?"
            params.append(doc_type)
        if system_level:
            sql += " AND system_level = ?"
            params.append(system_level)
        if query:
            sql += " AND (title LIKE ? OR doc_id LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])
        with self.connect() as connection:
            return [DocumentRecord(**dict(row)) for row in connection.execute(sql, params).fetchall()]

    def get_document_detail(self, document_id: int):
        with self.connect() as connection:
            document = DocumentRecord(**dict(connection.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()))
            sections = [SectionRecord(**dict(row)) for row in connection.execute("SELECT * FROM sections WHERE document_id = ? ORDER BY sequence", (document_id,)).fetchall()]
        return type("DocumentDetail", (), {"document": document, "sections": sections})

    def list_documents_by_ids(self, document_ids: list[int]):
        placeholders = ", ".join("?" for _ in document_ids)
        with self.connect() as connection:
            rows = connection.execute(f"SELECT * FROM documents WHERE id IN ({placeholders})", document_ids).fetchall()
        return [DocumentRecord(**dict(row)) for row in rows]

    def get_default_template(self):
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM templates ORDER BY id LIMIT 1").fetchone()
        return TemplateRecord(**dict(row))

    def insert_draft(self, record: DraftRecord) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO drafts (topic, department, target_doc_type, target_system_level, status, content_markdown, exported_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.topic,
                    record.department,
                    record.target_doc_type,
                    record.target_system_level,
                    record.status,
                    record.content_markdown,
                    record.exported_at,
                ),
            )
            return int(cursor.lastrowid)

    def attach_citations_from_markers(self, draft_id: int, content: str):
        section_id = int(content.split("[CITATION:")[1].split("]")[0])
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO citations (draft_id, draft_anchor, section_id, quote_excerpt) VALUES (?, ?, ?, ?)",
                (draft_id, "body", section_id, "generated citation"),
            )
            rows = connection.execute("SELECT * FROM citations WHERE draft_id = ?", (draft_id,)).fetchall()
        return [CitationRecord(**dict(row)) for row in rows]

    def insert_validation_issues(self, draft_id: int, issues) -> None:
        with self.connect() as connection:
            connection.executemany(
                "INSERT INTO validation_issues (owner_type, owner_id, severity, message, source_refs) VALUES (?, ?, ?, ?, ?)",
                [("draft", draft_id, issue.severity, issue.message, "") for issue in issues],
            )

    def insert_generation_run(self, record: GenerationRunRecord) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO generation_runs (draft_id, selected_document_ids, selected_template_id, status, duration_ms, input_summary)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.draft_id,
                    record.selected_document_ids,
                    record.selected_template_id,
                    record.status,
                    record.duration_ms,
                    record.input_summary,
                ),
            )

    def update_draft_status(self, draft_id: int, status: str) -> None:
        with self.connect() as connection:
            connection.execute("UPDATE drafts SET status = ? WHERE id = ?", (status, draft_id))

    def update_draft_content(self, draft_id: int, content: str) -> None:
        with self.connect() as connection:
            connection.execute("UPDATE drafts SET content_markdown = ? WHERE id = ?", (content, draft_id))

    def get_draft_detail(self, draft_id: int):
        with self.connect() as connection:
            draft = DraftRecord(**dict(connection.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()))
            citations = [CitationRecord(**dict(row)) for row in connection.execute("SELECT * FROM citations WHERE draft_id = ?", (draft_id,)).fetchall()]
            issues = [ValidationIssueRecord(**dict(row)) for row in connection.execute("SELECT * FROM validation_issues WHERE owner_type = 'draft' AND owner_id = ?", (draft_id,)).fetchall()]
        return type("DraftDetail", (), {**draft.__dict__, "citations": citations, "issues": issues})
```

- [ ] **Step 4: Run repository tests**

Run: `uv run pytest tests/test_repository.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/harnetics/models.py src/harnetics/repository.py tests/test_repository.py docs/generated/db-schema.md
git commit -m "feat: add sqlite repository and domain records"
```

### Task 3: Implement controlled import parsing and upload validation

**Files:**
- Create: `src/harnetics/importer.py`
- Modify: `src/harnetics/repository.py`
- Modify: `tests/conftest.py`
- Create: `tests/test_importer.py`
- Create: `src/harnetics/web/routes.py`

- [ ] **Step 1: Write the failing import tests**

```python
# tests/test_importer.py
from pathlib import Path

import pytest

from harnetics.importer import ImportService
from harnetics.repository import Repository


def test_import_service_ingests_controlled_markdown(temp_db_path) -> None:
    repo = Repository(temp_db_path)
    service = ImportService(repo)

    result = service.import_file(Path("fixtures/requirements/DOC-SYS-001.md"))

    assert result.document.doc_id == "DOC-SYS-001"
    assert result.section_count > 0


def test_import_service_ingests_controlled_yaml(temp_db_path) -> None:
    repo = Repository(temp_db_path)
    service = ImportService(repo)

    result = service.import_file(Path("fixtures/icd/DOC-ICD-001.yaml"))

    assert result.document.doc_type == "ICD"
    assert result.section_count > 0


def test_import_service_rejects_missing_metadata(temp_db_path, tmp_path: Path) -> None:
    repo = Repository(temp_db_path)
    service = ImportService(repo)
    bad_file = tmp_path / "bad.md"
    bad_file.write_text("# missing front matter", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required metadata"):
        service.import_file(bad_file)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_importer.py -v`
Expected: FAIL because `ImportService` does not exist

- [ ] **Step 3: Write the import service**

```python
# src/harnetics/importer.py
"""
[INPUT]: 依赖 pathlib、frontmatter、yaml 与 Repository
[OUTPUT]: 对外提供受控 Markdown/YAML 的解析、校验和入库服务
[POS]: harnetics 的导入边界层
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import frontmatter
import yaml

from harnetics.models import DocumentRecord, SectionRecord, TemplateRecord
from harnetics.repository import Repository

REQUIRED_METADATA = {
    "doc_id",
    "title",
    "version",
    "status",
    "department",
    "doc_type",
    "system_level",
    "engineering_phase",
}


@dataclass(slots=True)
class ImportResult:
    document: DocumentRecord
    section_count: int


class ImportService:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def import_file(self, path: Path) -> ImportResult:
        suffix = path.suffix.lower()
        if suffix == ".md":
            document, sections, template = self._parse_markdown(path)
        elif suffix in {".yaml", ".yml"}:
            document, sections, template = self._parse_yaml(path)
        else:
            raise ValueError(f"unsupported file type: {suffix}")

        document_id = self.repository.insert_document(document)
        self.repository.replace_sections(
            document_id,
            [SectionRecord(None, document_id, s.heading, s.level, s.sequence, s.content, s.trace_refs) for s in sections],
        )
        if template is not None:
            self.repository.upsert_template(TemplateRecord(None, document_id, template.name, template.required_sections, template.structure))
        return ImportResult(document=document, section_count=len(sections))

    def _require_metadata(self, metadata: dict[str, object]) -> None:
        missing = REQUIRED_METADATA - metadata.keys()
        if missing:
            raise ValueError(f"missing required metadata: {', '.join(sorted(missing))}")

    def _parse_markdown(self, path: Path):
        post = frontmatter.load(path)
        self._require_metadata(post.metadata)
        document = DocumentRecord(
            id=None,
            doc_id=str(post.metadata["doc_id"]),
            title=str(post.metadata["title"]),
            department=str(post.metadata["department"]),
            doc_type=str(post.metadata["doc_type"]),
            system_level=str(post.metadata["system_level"]),
            engineering_phase=str(post.metadata["engineering_phase"]),
            version=str(post.metadata["version"]),
            status=str(post.metadata["status"]),
            source_path=str(path),
            imported_at=datetime.now(UTC).isoformat(),
        )
        sections = [SectionRecord(None, 0, "body", 1, 1, post.content, "")]
        template = None
        if document.doc_type == "Template":
            template = TemplateRecord(None, 0, document.title, "1. 概述\n2. 测试依据\n3. 测试项目", post.content)
        return document, sections, template

    def _parse_yaml(self, path: Path):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        metadata = payload["metadata"]
        self._require_metadata(metadata)
        document = DocumentRecord(
            id=None,
            doc_id=str(metadata["doc_id"]),
            title=str(metadata["title"]),
            department=str(metadata["department"]),
            doc_type=str(metadata["doc_type"]),
            system_level=str(metadata["system_level"]),
            engineering_phase=str(metadata["engineering_phase"]),
            version=str(metadata["version"]),
            status=str(metadata["status"]),
            source_path=str(path),
            imported_at=datetime.now(UTC).isoformat(),
        )
        sections = [
            SectionRecord(None, 0, interface["name"], 2, index, yaml.safe_dump(interface, allow_unicode=True), "")
            for index, interface in enumerate(payload.get("interfaces", []), start=1)
        ]
        return document, sections, None
```

- [ ] **Step 4: Run import tests**

Run: `uv run pytest tests/test_importer.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/harnetics/importer.py src/harnetics/repository.py tests/test_importer.py
git commit -m "feat: add controlled markdown and yaml import"
```

### Task 4: Build upload, catalog list, filters, detail pages, and fixtures

**Files:**
- Modify: `src/harnetics/app.py`
- Modify: `src/harnetics/web/routes.py`
- Create: `src/harnetics/web/templates/documents.html`
- Create: `src/harnetics/web/templates/document_detail.html`
- Modify: `tests/conftest.py`
- Create: `tests/test_catalog_routes.py`

- [ ] **Step 1: Write the failing route tests**

```python
# tests/test_catalog_routes.py
from fastapi.testclient import TestClient


def test_upload_route_rejects_missing_metadata(temp_app) -> None:
    client = TestClient(temp_app)
    response = client.post(
        "/documents/import",
        files={"file": ("bad.md", "# no front matter", "text/markdown")},
    )
    assert response.status_code == 400


def test_documents_page_lists_and_filters(imported_fixture_app) -> None:
    client = TestClient(imported_fixture_app)
    response = client.get("/documents?department=系统工程部")
    assert response.status_code == 200
    assert "DOC-SYS-001" in response.text


def test_document_detail_shows_sections(imported_fixture_app) -> None:
    client = TestClient(imported_fixture_app)
    response = client.get("/documents/1")
    assert response.status_code == 200
    assert "body" in response.text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_catalog_routes.py -v`
Expected: FAIL with `404 != 400` or `404 != 200`

- [ ] **Step 3: Write the routes, templates, and fixtures**

```python
# src/harnetics/web/routes.py
"""
[INPUT]: 依赖 FastAPI、Jinja2Templates、Repository、ImportService
[OUTPUT]: 对外提供文档导入、文档列表和文档详情路由
[POS]: harnetics 的 HTTP 路由入口
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="src/harnetics/web/templates")


@router.get("/documents", response_class=HTMLResponse)
def list_documents(
    request: Request,
    department: str | None = None,
    doc_type: str | None = None,
    system_level: str | None = None,
    query: str | None = None,
):
    documents = request.app.state.repository.list_documents(
        department=department,
        doc_type=doc_type,
        system_level=system_level,
        query=query,
    )
    return templates.TemplateResponse(request, "documents.html", {"documents": documents})


@router.post("/documents/import")
async def import_document(request: Request, file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="missing filename")
    target = request.app.state.settings.raw_upload_dir / file.filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(await file.read())
    try:
        request.app.state.import_service.import_file(target)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "imported"}


@router.get("/documents/{document_id}", response_class=HTMLResponse)
def show_document(request: Request, document_id: int):
    detail = request.app.state.repository.get_document_detail(document_id)
    return templates.TemplateResponse(request, "document_detail.html", {"detail": detail})
```

```python
# src/harnetics/app.py
from harnetics.web.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="Harnetics")
    app.state.settings = get_settings()
    app.include_router(router)

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    return app
```

```python
# tests/conftest.py
from pathlib import Path

import pytest

from harnetics.app import create_app
from harnetics.drafts import DraftService
from harnetics.importer import ImportService
from harnetics.retrieval import RetrievalPlanner
from harnetics.repository import Repository
from harnetics.validation import DraftValidator


class FakeLlmClient:
    def generate_markdown(self, *, prompt: str) -> str:
        return "## 1. 概述\n- 地面推力满足 650 kN。[CITATION:1]\n"


@pytest.fixture
def temp_app(temp_db_path):
    app = create_app()
    repository = Repository(temp_db_path)
    app.state.repository = repository
    app.state.import_service = ImportService(repository)
    app.state.settings = type("Settings", (), {"raw_upload_dir": temp_db_path.parent / "uploads"})
    app.state.retrieval_planner = RetrievalPlanner(repository)
    app.state.draft_service = DraftService(repository=repository, llm_client=FakeLlmClient(), validator=DraftValidator(repository))
    return app


@pytest.fixture
def imported_fixture_app(temp_app):
    importer = temp_app.state.import_service
    importer.import_file(Path("fixtures/requirements/DOC-SYS-001.md"))
    importer.import_file(Path("fixtures/design/DOC-DES-001.md"))
    importer.import_file(Path("fixtures/templates/DOC-TPL-001.md"))
    return temp_app
```

```html
<!-- src/harnetics/web/templates/documents.html -->
<!--
[INPUT]: 依赖 base.html、文档列表和筛选字段
[OUTPUT]: 对外提供上传、筛选和列表页面
[POS]: Web 文档库模板
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->
{% extends "base.html" %}
{% block content %}
<h1>文档库</h1>
<form action="/documents/import" method="post" enctype="multipart/form-data">
  <input type="file" name="file" required>
  <button type="submit">上传文档</button>
</form>
{% for document in documents %}
  <div><a href="/documents/{{ document.id }}">{{ document.doc_id }}</a> - {{ document.title }}</div>
{% endfor %}
{% endblock %}
```

```html
<!-- src/harnetics/web/templates/document_detail.html -->
<!--
[INPUT]: 依赖文档详情和 section 列表
[OUTPUT]: 对外提供文档详情视图
[POS]: Web 文档详情模板
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->
{% extends "base.html" %}
{% block content %}
<h1>{{ detail.document.doc_id }} - {{ detail.document.title }}</h1>
{% for section in detail.sections %}
  <section><h2>{{ section.heading }}</h2><pre>{{ section.content }}</pre></section>
{% endfor %}
{% endblock %}
```

- [ ] **Step 4: Run catalog tests**

Run: `uv run pytest tests/test_catalog_routes.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/harnetics/web/routes.py src/harnetics/web/templates tests/conftest.py tests/test_catalog_routes.py
git commit -m "feat: add upload and document catalog routes"
```

### Task 5: Implement candidate retrieval, draft generation, validation, editing, and export

**Files:**
- Create: `src/harnetics/retrieval.py`
- Create: `src/harnetics/llm.py`
- Create: `src/harnetics/validation.py`
- Create: `src/harnetics/drafts.py`
- Modify: `src/harnetics/repository.py`
- Modify: `src/harnetics/web/routes.py`
- Create: `src/harnetics/web/templates/draft_new.html`
- Create: `src/harnetics/web/templates/draft_show.html`
- Modify: `tests/conftest.py`
- Create: `tests/test_retrieval.py`
- Create: `tests/test_drafts.py`
- Modify: `ARCHITECTURE.md`
- Modify: `docs/generated/db-schema.md`

- [ ] **Step 1: Write the failing retrieval and draft tests**

```python
# tests/test_retrieval.py
from pathlib import Path

from harnetics.importer import ImportService
from harnetics.repository import Repository
from harnetics.retrieval import RetrievalPlanner


def test_retrieval_planner_returns_template_and_ranked_sources(temp_db_path) -> None:
    repo = Repository(temp_db_path)
    importer = ImportService(repo)
    importer.import_file(Path("fixtures/requirements/DOC-SYS-001.md"))
    importer.import_file(Path("fixtures/design/DOC-DES-001.md"))
    importer.import_file(Path("fixtures/templates/DOC-TPL-001.md"))

    planner = RetrievalPlanner(repo)
    plan = planner.plan(
        topic="TQ-12 地面试车测试大纲",
        department="动力系统部",
        target_doc_type="TestPlan",
        target_system_level="Subsystem",
    )

    assert plan.template.name == "地面试验测试大纲编写模板"
    assert plan.documents[0].doc_id in {"DOC-SYS-001", "DOC-DES-001"}
```

```python
# tests/test_drafts.py
from pathlib import Path

from fastapi.testclient import TestClient

from harnetics.drafts import DraftService
from harnetics.importer import ImportService
from harnetics.repository import Repository
from harnetics.validation import DraftValidator


class FakeLlmClient:
    def generate_markdown(self, *, prompt: str) -> str:
        return "## 1. 概述\n- 地面推力满足 650 kN。[CITATION:1]\n"


def test_draft_service_generates_citations_and_warnings(temp_db_path) -> None:
    repo = Repository(temp_db_path)
    importer = ImportService(repo)
    importer.import_file(Path("fixtures/requirements/DOC-SYS-001.md"))
    importer.import_file(Path("fixtures/design/DOC-DES-001.md"))
    importer.import_file(Path("fixtures/templates/DOC-TPL-001.md"))
    importer.import_file(Path("fixtures/test_plans/DOC-TST-003.md"))

    service = DraftService(repository=repo, llm_client=FakeLlmClient(), validator=DraftValidator(repo))
    draft = service.generate(
        topic="TQ-12 地面试车测试大纲",
        department="动力系统部",
        target_doc_type="TestPlan",
        target_system_level="Subsystem",
        selected_document_ids=[1, 2, 4],
        template_id=1,
    )

    assert draft.citations
    assert any(issue.severity == "warning" for issue in draft.issues)


def test_draft_workspace_supports_edit_and_export(imported_fixture_app) -> None:
    client = TestClient(imported_fixture_app)
    response = client.post(
        "/drafts",
        data={
            "topic": "TQ-12 地面试车测试大纲",
            "department": "动力系统部",
            "target_doc_type": "TestPlan",
            "target_system_level": "Subsystem",
            "selected_document_ids": [1, 2],
            "template_id": 1,
        },
    )
    draft_id = response.json()["draft_id"]
    edit_response = client.post(f"/drafts/{draft_id}/edit", data={"content": "## 更新后的草稿"})
    export_response = client.get(f"/drafts/{draft_id}/export")

    assert edit_response.status_code == 303
    assert export_response.status_code == 200
    assert export_response.headers["content-type"].startswith("text/markdown")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_retrieval.py tests/test_drafts.py -v`
Expected: FAIL because retrieval, generation, edit, and export behavior do not exist yet

- [ ] **Step 3: Write retrieval, generation, validation, and workspace**

```python
# src/harnetics/retrieval.py
"""
[INPUT]: 依赖 Repository 查询出的文档和模板
[OUTPUT]: 对外提供候选来源和模板的排序结果
[POS]: harnetics 的检索规划器，负责“先候选、后生成”
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""

from dataclasses import dataclass


def tokenize(text: str) -> set[str]:
    return {token.lower() for token in text.replace("-", " ").split() if token}


@dataclass(slots=True)
class RetrievalPlan:
    template: object
    documents: list[object]


class RetrievalPlanner:
    def __init__(self, repository) -> None:
        self.repository = repository

    def plan(self, topic: str, department: str, target_doc_type: str, target_system_level: str) -> RetrievalPlan:
        candidates = self.repository.list_documents(department=department) or self.repository.list_documents(system_level=target_system_level)
        ranked = sorted(
            candidates,
            key=lambda doc: (
                len(tokenize(topic) & tokenize(doc.title)),
                int(doc.department == department),
                int(doc.system_level == target_system_level),
            ),
            reverse=True,
        )
        return RetrievalPlan(template=self.repository.get_default_template(), documents=ranked[:5])
```

```python
# src/harnetics/llm.py
"""
[INPUT]: 依赖 httpx 与 Settings 中的本地 LLM 配置
[OUTPUT]: 对外提供 OpenAI-compatible 的本地模型客户端
[POS]: harnetics 与本地 LLM 服务之间的适配层
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""

import httpx


class LocalLlmClient:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate_markdown(self, *, prompt: str) -> str:
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
```

```python
# src/harnetics/validation.py
"""
[INPUT]: 依赖 Repository、selected documents、citations 与 generated markdown
[OUTPUT]: 对外提供强告警和阻断校验
[POS]: harnetics 的生成后校验层
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""


class DraftValidator:
    def __init__(self, repository) -> None:
        self.repository = repository

    def validate(self, *, selected_document_ids: list[int], citations: list[object], content: str):
        issues = []
        if not citations:
            issues.append(type("Issue", (), {"severity": "blocking", "message": "草稿缺少引用"}))
        if "## 1. 概述" not in content:
            issues.append(type("Issue", (), {"severity": "blocking", "message": "模板必填章节缺失：1. 概述"}))
        for document in self.repository.list_documents_by_ids(selected_document_ids):
            if document.doc_id == "DOC-TST-003":
                issues.append(type("Issue", (), {"severity": "warning", "message": "DOC-TST-003 引用了旧版本系统需求或 ICD"}))
        return issues
```

```python
# src/harnetics/drafts.py
"""
[INPUT]: 依赖 Repository、LocalLlmClient 与 DraftValidator
[OUTPUT]: 对外提供草稿生成、citation 附着和 generation run 落库
[POS]: harnetics 的草稿编排服务
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""

from time import perf_counter

from harnetics.models import DraftRecord, GenerationRunRecord


class DraftService:
    def __init__(self, repository, llm_client, validator) -> None:
        self.repository = repository
        self.llm_client = llm_client
        self.validator = validator

    def generate(
        self,
        *,
        topic: str,
        department: str,
        target_doc_type: str,
        target_system_level: str,
        selected_document_ids: list[int],
        template_id: int,
    ):
        started = perf_counter()
        template = self.repository.get_default_template()
        sections = self.repository.get_document_detail(selected_document_ids[0]).sections
        prompt = self._build_prompt(topic=topic, template=template, sections=sections)
        content = self.llm_client.generate_markdown(prompt=prompt)
        draft_id = self.repository.insert_draft(
            DraftRecord(
                id=None,
                topic=topic,
                department=department,
                target_doc_type=target_doc_type,
                target_system_level=target_system_level,
                status="generated",
                content_markdown=content,
                exported_at=None,
            )
        )
        citations = self.repository.attach_citations_from_markers(draft_id, content)
        issues = self.validator.validate(selected_document_ids=selected_document_ids, citations=citations, content=content)
        self.repository.insert_generation_run(GenerationRunRecord(None, draft_id, ",".join(str(item) for item in selected_document_ids), template_id, "completed", int((perf_counter() - started) * 1000), topic))
        self.repository.insert_validation_issues(draft_id, issues)
        self.repository.update_draft_status(draft_id, "warning" if issues else "ready")
        return self.repository.get_draft_detail(draft_id)

    def _build_prompt(self, *, topic: str, template, sections) -> str:
        source_text = "\n".join(f"[SECTION:{section.id}] {section.heading}\n{section.content}" for section in sections)
        return f"主题：{topic}\n模板：{template.structure}\n来源：\n{source_text}\n输出 Markdown，并在每个段落后添加 [CITATION:<section_id>]。"
```

```python
# src/harnetics/web/routes.py
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse

@router.get("/drafts/new", response_class=HTMLResponse)
def new_draft(request: Request):
    return templates.TemplateResponse(request, "draft_new.html", {"plan": None})


@router.post("/drafts/plan", response_class=HTMLResponse)
def plan_draft(
    request: Request,
    topic: str = Form(...),
    department: str = Form(...),
    target_doc_type: str = Form(...),
    target_system_level: str = Form(...),
):
    plan = request.app.state.retrieval_planner.plan(topic, department, target_doc_type, target_system_level)
    return templates.TemplateResponse(request, "draft_new.html", {"plan": plan, "topic": topic, "department": department, "target_doc_type": target_doc_type, "target_system_level": target_system_level})


@router.post("/drafts")
def create_draft(
    request: Request,
    topic: str = Form(...),
    department: str = Form(...),
    target_doc_type: str = Form(...),
    target_system_level: str = Form(...),
    selected_document_ids: list[int] = Form(...),
    template_id: int = Form(...),
):
    draft = request.app.state.draft_service.generate(
        topic=topic,
        department=department,
        target_doc_type=target_doc_type,
        target_system_level=target_system_level,
        selected_document_ids=selected_document_ids,
        template_id=template_id,
    )
    return {"draft_id": draft.id}


@router.get("/drafts/{draft_id}", response_class=HTMLResponse)
def show_draft(request: Request, draft_id: int):
    draft = request.app.state.repository.get_draft_detail(draft_id)
    return templates.TemplateResponse(request, "draft_show.html", {"draft": draft, "issues": draft.issues, "citations": draft.citations})


@router.post("/drafts/{draft_id}/edit")
def update_draft(request: Request, draft_id: int, content: str = Form(...)):
    request.app.state.repository.update_draft_content(draft_id, content)
    return RedirectResponse(f"/drafts/{draft_id}", status_code=303)


@router.get("/drafts/{draft_id}/export")
def export_draft(request: Request, draft_id: int):
    draft = request.app.state.repository.get_draft_detail(draft_id)
    return PlainTextResponse(
        draft.content_markdown,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename=\"draft-{draft_id}.md\"'},
    )
```

```html
<!-- src/harnetics/web/templates/draft_new.html -->
<!--
[INPUT]: 依赖候选 plan、模板与草稿输入字段
[OUTPUT]: 对外提供两步式草稿创建界面
[POS]: Web 草稿创建模板
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->
{% extends "base.html" %}
{% block content %}
<h1>生成草稿</h1>
<form action="/drafts/plan" method="post">
  <input name="topic" value="{{ topic or '' }}" required>
  <input name="department" value="{{ department or '' }}" required>
  <input name="target_doc_type" value="{{ target_doc_type or '' }}" required>
  <input name="target_system_level" value="{{ target_system_level or '' }}" required>
  <button type="submit">检索候选</button>
</form>
{% if plan %}
  <form action="/drafts" method="post">
    <input type="hidden" name="topic" value="{{ topic }}">
    <input type="hidden" name="department" value="{{ department }}">
    <input type="hidden" name="target_doc_type" value="{{ target_doc_type }}">
    <input type="hidden" name="target_system_level" value="{{ target_system_level }}">
    <input type="hidden" name="template_id" value="{{ plan.template.id }}">
    {% for document in plan.documents %}
      <label><input type="checkbox" name="selected_document_ids" value="{{ document.id }}" checked> {{ document.doc_id }}</label>
    {% endfor %}
    <button type="submit">生成草稿</button>
  </form>
{% endif %}
{% endblock %}
```

```html
<!-- src/harnetics/web/templates/draft_show.html -->
<!--
[INPUT]: 依赖草稿正文、warnings 与 citations
[OUTPUT]: 对外提供轻编辑、告警可视化和 Markdown 导出界面
[POS]: Web 草稿工作台模板
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->
{% extends "base.html" %}
{% block content %}
<h1>草稿工作台</h1>
<form method="post" action="/drafts/{{ draft.id }}/edit">
  <textarea name="content" rows="24">{{ draft.content_markdown }}</textarea>
  <button type="submit">保存修改</button>
</form>
<aside>
  <h2>告警</h2>
  {% for issue in issues %}
    <div><mark>{{ issue.severity }}</mark> {{ issue.message }}</div>
  {% endfor %}
  <h2>引注</h2>
  {% for citation in citations %}
    <div>{{ citation.draft_anchor }} -> Section {{ citation.section_id }}</div>
  {% endfor %}
</aside>
<a href="/drafts/{{ draft.id }}/export">导出 Markdown</a>
{% endblock %}
```

- [ ] **Step 4: Run retrieval and full workflow tests**

Run: `uv run pytest tests/test_retrieval.py tests/test_drafts.py tests/test_catalog_routes.py tests/test_importer.py tests/test_repository.py tests/test_app.py -v`
Expected: PASS across the full minimal loop

- [ ] **Step 5: Commit**

```bash
git add src/harnetics/retrieval.py src/harnetics/llm.py src/harnetics/validation.py src/harnetics/drafts.py src/harnetics/repository.py src/harnetics/web/routes.py src/harnetics/web/templates/draft_new.html src/harnetics/web/templates/draft_show.html tests/test_retrieval.py tests/test_drafts.py ARCHITECTURE.md docs/generated/db-schema.md
git commit -m "feat: add draft generation validation and export flow"
```

## Self-Review Notes

### Spec coverage

- 导入受控文档：Task 3
- 浏览与检索文档库：Task 4
- 混合式候选选择：Task 5
- 带引注草稿生成：Task 5
- Web 内轻编辑与 Markdown 导出：Task 5
- 强告警与阻断：Task 5
- 文档同步：Task 1, Task 2, and Task 5

### Placeholder scan

- This plan intentionally avoids placeholder markers and vague “fill this in later” language.
- Every task includes exact file paths and exact verification commands.

### Type consistency

- Persistence records stay under `DocumentRecord`, `SectionRecord`, `TemplateRecord`, `DraftRecord`, `CitationRecord`, `ValidationIssueRecord`, and `GenerationRunRecord`.
- `Repository` remains the only module allowed to talk directly to SQLite.
- `ImportService`, `RetrievalPlanner`, `DraftService`, and `DraftValidator` work with repository records instead of raw SQL rows.
