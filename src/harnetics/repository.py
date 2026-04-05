# [INPUT]: 依赖 sqlite3、pathlib 与 harnetics.models
# [OUTPUT]: 对外提供 SQLite schema 初始化和 domain query/update 接口
# [POS]: harnetics 的唯一持久化边界层
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

import re
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

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
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
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

    def delete_document_tree(self, document_id: int) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))

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
            row = connection.execute(
                "SELECT id FROM templates WHERE document_id = ?",
                (record.document_id,),
            ).fetchone()
        return int(row["id"])

    def list_documents(
        self,
        department: str | None = None,
        doc_type: str | None = None,
        system_level: str | None = None,
        query: str | None = None,
    ) -> list[DocumentRecord]:
        sql = "SELECT * FROM documents WHERE 1=1"
        params: list[object] = []
        if department is not None:
            sql += " AND department = ?"
            params.append(department)
        if doc_type is not None:
            sql += " AND doc_type = ?"
            params.append(doc_type)
        if system_level is not None:
            sql += " AND system_level = ?"
            params.append(system_level)
        if query is not None:
            sql += " AND (title LIKE ? OR doc_id LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])
        sql += " ORDER BY id"
        with self.connect() as connection:
            rows = connection.execute(sql, params).fetchall()
        return [DocumentRecord(**dict(row)) for row in rows]

    def get_document_detail(self, document_id: int):
        with self.connect() as connection:
            document_row = connection.execute(
                "SELECT * FROM documents WHERE id = ?",
                (document_id,),
            ).fetchone()
            if document_row is None:
                raise LookupError(f"document not found: {document_id}")
            section_rows = connection.execute(
                "SELECT * FROM sections WHERE document_id = ? ORDER BY sequence",
                (document_id,),
            ).fetchall()
        return SimpleNamespace(
            document=DocumentRecord(**dict(document_row)),
            sections=[SectionRecord(**dict(row)) for row in section_rows],
        )

    def list_documents_by_ids(self, document_ids: list[int]) -> list[DocumentRecord]:
        if not document_ids:
            return []
        placeholders = ", ".join("?" for _ in document_ids)
        with self.connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM documents WHERE id IN ({placeholders}) ORDER BY id",
                document_ids,
            ).fetchall()
        return [DocumentRecord(**dict(row)) for row in rows]

    def get_default_template(self) -> TemplateRecord:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM templates ORDER BY id LIMIT 1").fetchone()
        if row is None:
            raise LookupError("default template not found")
        return TemplateRecord(**dict(row))

    def get_template(self, template_id: int) -> TemplateRecord:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM templates WHERE id = ?",
                (template_id,),
            ).fetchone()
        if row is None:
            raise LookupError(f"template not found: {template_id}")
        return TemplateRecord(**dict(row))

    def insert_draft(self, record: DraftRecord) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO drafts (
                    topic, department, target_doc_type, target_system_level,
                    status, content_markdown, exported_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
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

    def attach_citations_from_markers(
        self,
        draft_id: int,
        content: str,
        *,
        allowed_section_ids: set[int] | None = None,
    ) -> list[CitationRecord]:
        marker_ids = [int(item) for item in re.findall(r"\[CITATION:(\d+)\]", content)]
        if not marker_ids:
            return []
        unique_marker_ids = list(dict.fromkeys(marker_ids))
        placeholders = ", ".join("?" for _ in unique_marker_ids)
        with self.connect() as connection:
            existing_rows = connection.execute(
                f"SELECT id FROM sections WHERE id IN ({placeholders})",
                unique_marker_ids,
            ).fetchall()
            existing_ids = {int(row["id"]) for row in existing_rows}
            if allowed_section_ids is not None:
                existing_ids &= allowed_section_ids
            valid_marker_ids = [section_id for section_id in marker_ids if section_id in existing_ids]
            if valid_marker_ids:
                connection.executemany(
                    "INSERT INTO citations (draft_id, draft_anchor, section_id, quote_excerpt) VALUES (?, ?, ?, ?)",
                    [
                        (draft_id, "body", section_id, "generated citation")
                        for section_id in valid_marker_ids
                    ],
                )
            rows = connection.execute(
                "SELECT * FROM citations WHERE draft_id = ? ORDER BY id",
                (draft_id,),
            ).fetchall()
        return [CitationRecord(**dict(row)) for row in rows]

    def clear_citations(self, draft_id: int) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM citations WHERE draft_id = ?", (draft_id,))

    def insert_validation_issues(
        self,
        draft_id: int,
        issues: list[ValidationIssueRecord],
    ) -> None:
        with self.connect() as connection:
            connection.executemany(
                "INSERT INTO validation_issues (owner_type, owner_id, severity, message, source_refs) VALUES (?, ?, ?, ?, ?)",
                [
                    (
                        "draft",
                        draft_id,
                        issue.severity,
                        issue.message,
                        getattr(issue, "source_refs", ""),
                    )
                    for issue in issues
                ],
            )

    def insert_generation_run(self, record: GenerationRunRecord) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO generation_runs (
                    draft_id, selected_document_ids, selected_template_id,
                    status, duration_ms, input_summary
                ) VALUES (?, ?, ?, ?, ?, ?)
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

    def get_selected_document_ids_for_draft(self, draft_id: int) -> list[int]:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT selected_document_ids
                FROM generation_runs
                WHERE draft_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (draft_id,),
            ).fetchone()
        if row is None:
            return []
        return [int(item) for item in row["selected_document_ids"].split(",") if item]

    def update_draft_status(self, draft_id: int, status: str) -> None:
        with self.connect() as connection:
            connection.execute("UPDATE drafts SET status = ? WHERE id = ?", (status, draft_id))

    def update_draft_content(self, draft_id: int, content: str) -> None:
        with self.connect() as connection:
            connection.execute("UPDATE drafts SET content_markdown = ? WHERE id = ?", (content, draft_id))

    def mark_draft_exported(self, draft_id: int, exported_at: datetime) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE drafts SET exported_at = ? WHERE id = ?",
                (exported_at.isoformat(), draft_id),
            )

    def clear_validation_issues(self, draft_id: int) -> None:
        with self.connect() as connection:
            connection.execute(
                "DELETE FROM validation_issues WHERE owner_type = 'draft' AND owner_id = ?",
                (draft_id,),
            )

    def get_draft_detail(self, draft_id: int):
        with self.connect() as connection:
            draft_row = connection.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,)).fetchone()
            if draft_row is None:
                raise LookupError(f"draft not found: {draft_id}")
            citation_rows = connection.execute(
                "SELECT * FROM citations WHERE draft_id = ? ORDER BY id",
                (draft_id,),
            ).fetchall()
            issue_rows = connection.execute(
                "SELECT * FROM validation_issues WHERE owner_type = 'draft' AND owner_id = ? ORDER BY id",
                (draft_id,),
            ).fetchall()
        draft = DraftRecord(**dict(draft_row))
        return SimpleNamespace(
            **asdict(draft),
            citations=[CitationRecord(**dict(row)) for row in citation_rows],
            issues=[ValidationIssueRecord(**dict(row)) for row in issue_rows],
        )


__all__ = ["Repository"]
