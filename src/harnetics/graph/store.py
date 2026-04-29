# [INPUT]: 依赖 sqlite3、pathlib、同目录 schema.sql 与 models 包 (DocumentNode/Section/DocumentEdge/ICDParameter)
# [OUTPUT]: 对外提供 init_db()、get_connection() 及文档/章节/边/ICD 参数的 CRUD 与关系折叠函数
# [POS]: graph 包的 SQLite 存储层，负责图谱库初始化、连接管理、全量读写与文档级关系去重
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

_SCHEMA_PATH = Path(__file__).with_name("schema.sql")

_EXPECTED_TABLE_COLUMNS: dict[str, set[str]] = {
    "documents": {
        "doc_id", "title", "doc_type", "department", "system_level",
        "engineering_phase", "version", "status", "content_hash",
        "file_path", "created_at", "updated_at",
    },
    "sections": {
        "section_id", "doc_id", "heading", "content", "level",
        "order_index", "tags",
    },
    "edges": {
        "edge_id", "source_doc_id", "source_section_id", "target_doc_id",
        "target_section_id", "relation", "confidence", "created_by",
        "created_at",
    },
    "icd_parameters": {
        "param_id", "doc_id", "name", "interface_type", "subsystem_a",
        "subsystem_b", "value", "unit", "range_", "owner_department",
        "version",
    },
    "versions": {
        "version_id", "doc_id", "version", "content_hash", "file_path",
        "created_at",
    },
    "drafts": {
        "draft_id", "request_json", "content_md", "citations_json",
        "conflicts_json", "eval_results_json", "status", "generated_by",
        "created_at", "reviewed_at",
    },
    "impact_reports": {
        "report_id", "trigger_doc_id", "old_version", "new_version",
        "changed_sections_json", "impacted_docs_json", "summary",
        "created_at",
    },
}

# ---- 模块级默认路径，由 init_db() 设置 ----
_db_path: Path = Path("var/harnetics-graph.db")


def init_db(db_path: Path | str | None = None) -> None:
    """建表 + 启用外键约束。启动时调用一次即可。"""
    global _db_path
    if db_path is not None:
        _db_path = Path(db_path)
    _db_path.parent.mkdir(parents=True, exist_ok=True)
    schema_sql = _SCHEMA_PATH.read_text(encoding="utf-8")
    with _connect(_db_path) as conn:
        _assert_graph_schema_compatible(conn, _db_path)
        conn.executescript(schema_sql)


@contextmanager
def get_connection(db_path: Path | str | None = None) -> Generator[sqlite3.Connection, None, None]:
    """获取一个启用外键约束的 SQLite 连接，自动提交/回滚。"""
    path = Path(db_path) if db_path is not None else _db_path
    conn = _connect(path)
    try:
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _assert_graph_schema_compatible(conn: sqlite3.Connection, db_path: Path) -> None:
    existing_tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    for table_name, required_columns in _EXPECTED_TABLE_COLUMNS.items():
        if table_name not in existing_tables:
            continue
        actual_columns = _get_table_columns(conn, table_name)
        missing_columns = required_columns - actual_columns
        if not missing_columns:
            continue
        missing_list = ", ".join(sorted(missing_columns))
        raise RuntimeError(
            f"Incompatible graph database at {db_path}: table '{table_name}' is missing columns [{missing_list}]. "
            "This path appears to point at the legacy repository database. "
            "Use the default graph path 'var/harnetics-graph.db', set HARNETICS_GRAPH_DB_PATH to a separate file, "
            "or rerun 'harnetics init --reset --db <path>'."
        )


def _get_table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row[1] for row in rows}


def insert_document(doc: "DocumentNode") -> None:
    with get_connection() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO documents
               (doc_id, title, doc_type, department, system_level,
                engineering_phase, version, status, content_hash, file_path)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (doc.doc_id, doc.title, doc.doc_type, doc.department,
             doc.system_level, doc.engineering_phase, doc.version,
             doc.status, doc.content_hash, doc.file_path),
        )


def insert_sections(sections: list["Section"]) -> None:
    if not sections:
        return
    with get_connection() as conn:
        conn.executemany(
            """INSERT OR REPLACE INTO sections
               (section_id, doc_id, heading, content, level, order_index, tags)
               VALUES (?,?,?,?,?,?,?)""",
            [(s.section_id, s.doc_id, s.heading, s.content,
              s.level, s.order_index, s.tags) for s in sections],
        )


def insert_edges(edges: list["DocumentEdge"]) -> None:
    if not edges:
        return
    with get_connection() as conn:
        conn.executemany(
            """INSERT INTO edges
               (source_doc_id, source_section_id, target_doc_id,
                target_section_id, relation, confidence, created_by)
               VALUES (?,?,?,?,?,?,?)""",
            [(e.source_doc_id, e.source_section_id, e.target_doc_id,
              e.target_section_id, e.relation, e.confidence, e.created_by)
             for e in edges],
        )


def replace_edges_for_source(source_doc_id: str, edges: list["DocumentEdge"]) -> None:
    """用最新提取结果替换一个源文档的全部 outgoing edges。"""
    with get_connection() as conn:
        conn.execute("DELETE FROM edges WHERE source_doc_id=?", (source_doc_id,))
        if not edges:
            return
        conn.executemany(
            """INSERT INTO edges
               (source_doc_id, source_section_id, target_doc_id,
                target_section_id, relation, confidence, created_by)
               VALUES (?,?,?,?,?,?,?)""",
            [(e.source_doc_id, e.source_section_id, e.target_doc_id,
              e.target_section_id, e.relation, e.confidence, e.created_by)
             for e in edges],
        )


def insert_icd_parameters(params: list["ICDParameter"]) -> None:
    if not params:
        return
    with get_connection() as conn:
        conn.executemany(
            """INSERT OR REPLACE INTO icd_parameters
               (param_id, doc_id, name, interface_type, subsystem_a,
                subsystem_b, value, unit, range_, owner_department, version)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            [(p.param_id, p.doc_id, p.name, p.interface_type,
              p.subsystem_a, p.subsystem_b, p.value, p.unit,
              p.range_, p.owner_department, p.version) for p in params],
        )


# ================================================================
# CRUD — 查询
# ================================================================

def _row_to_document(row: sqlite3.Row) -> "DocumentNode":
    from harnetics.models.document import DocumentNode
    return DocumentNode(
        doc_id=row["doc_id"], title=row["title"], doc_type=row["doc_type"],
        department=row["department"], system_level=row["system_level"],
        engineering_phase=row["engineering_phase"], version=row["version"],
        status=row["status"], content_hash=row["content_hash"],
        file_path=row["file_path"], created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_section(row: sqlite3.Row) -> "Section":
    from harnetics.models.document import Section
    return Section(
        section_id=row["section_id"], doc_id=row["doc_id"],
        heading=row["heading"], content=row["content"],
        level=row["level"], order_index=row["order_index"],
        tags=row["tags"],
    )


def _row_to_edge(row: sqlite3.Row) -> "DocumentEdge":
    from harnetics.models.document import DocumentEdge
    return DocumentEdge(
        edge_id=row["edge_id"], source_doc_id=row["source_doc_id"],
        source_section_id=row["source_section_id"],
        target_doc_id=row["target_doc_id"],
        target_section_id=row["target_section_id"],
        relation=row["relation"], confidence=row["confidence"],
        created_by=row["created_by"], created_at=row["created_at"],
    )


def _row_to_icd(row: sqlite3.Row) -> "ICDParameter":
    from harnetics.models.icd import ICDParameter
    return ICDParameter(
        param_id=row["param_id"], doc_id=row["doc_id"],
        name=row["name"], interface_type=row["interface_type"],
        subsystem_a=row["subsystem_a"], subsystem_b=row["subsystem_b"],
        value=row["value"], unit=row["unit"], range_=row["range_"],
        owner_department=row["owner_department"], version=row["version"],
    )


def get_document(doc_id: str) -> "DocumentNode | None":
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM documents WHERE doc_id=?", (doc_id,)).fetchone()
        return _row_to_document(row) if row else None


def get_documents(
    department: str | None = None,
    doc_type: str | None = None,
    system_level: str | None = None,
    status: str | None = None,
    q: str | None = None,
) -> list["DocumentNode"]:
    clauses: list[str] = []
    params: list[str] = []
    if department:
        clauses.append("department = ?")
        params.append(department)
    if doc_type:
        clauses.append("doc_type = ?")
        params.append(doc_type)
    if system_level:
        clauses.append("system_level = ?")
        params.append(system_level)
    if status:
        clauses.append("status = ?")
        params.append(status)
    if q:
        clauses.append("(title LIKE ? OR doc_id LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])
    where = " AND ".join(clauses)
    sql = "SELECT * FROM documents"
    if where:
        sql += " WHERE " + where
    sql += " ORDER BY doc_id"
    with get_connection() as conn:
        return [_row_to_document(r) for r in conn.execute(sql, params).fetchall()]


def get_sections(doc_id: str) -> list["Section"]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM sections WHERE doc_id=? ORDER BY order_index",
            (doc_id,),
        ).fetchall()
        return [_row_to_section(r) for r in rows]


def get_icd_parameters(doc_id: str | None = None) -> list["ICDParameter"]:
    with get_connection() as conn:
        if doc_id:
            rows = conn.execute(
                "SELECT * FROM icd_parameters WHERE doc_id=?", (doc_id,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM icd_parameters").fetchall()
        return [_row_to_icd(r) for r in rows]


def get_icd_parameter(param_id: str) -> "ICDParameter | None":
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM icd_parameters WHERE param_id=?", (param_id,)
        ).fetchone()
        return _row_to_icd(row) if row else None


def delete_document(doc_id: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM documents WHERE doc_id=?", (doc_id,))


def get_edges_for_doc(doc_id: str) -> tuple[list["DocumentEdge"], list["DocumentEdge"]]:
    """返回 (upstream, downstream)。
    upstream: 本文档引用的上游文档，即以本文档为 source 的边。
    downstream: 引用了本文档的下游文档，即以本文档为 target 的边。
    """
    with get_connection() as conn:
        up = conn.execute(
            "SELECT * FROM edges WHERE source_doc_id=?", (doc_id,)
        ).fetchall()
        down = conn.execute(
            "SELECT * FROM edges WHERE target_doc_id=?", (doc_id,)
        ).fetchall()
        return ([_row_to_edge(r) for r in up], [_row_to_edge(r) for r in down])


def collapse_doc_edges(doc_id: str, edges: list["DocumentEdge"]) -> list["DocumentEdge"]:
    """把 section-level 边折叠成文档详情页所需的文档级唯一关系。"""
    collapsed: dict[tuple[str, str], "DocumentEdge"] = {}
    for edge in edges:
        other_doc_id = edge.target_doc_id if edge.source_doc_id == doc_id else edge.source_doc_id
        key = (other_doc_id, edge.relation)
        current = collapsed.get(key)
        if current is None or edge.confidence > current.confidence:
            collapsed[key] = edge

    def _sort_key(edge: "DocumentEdge") -> tuple[str, str, float]:
        other_doc_id = edge.target_doc_id if edge.source_doc_id == doc_id else edge.source_doc_id
        return (other_doc_id, edge.relation, -float(edge.confidence))

    return sorted(collapsed.values(), key=_sort_key)


def search_documents(q: str) -> list["DocumentNode"]:
    pattern = f"%{q}%"
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT DISTINCT d.* FROM documents d
               LEFT JOIN sections s ON s.doc_id = d.doc_id
               WHERE d.title LIKE ? OR d.doc_id LIKE ? OR s.content LIKE ?
               ORDER BY d.doc_id""",
            (pattern, pattern, pattern),
        ).fetchall()
        return [_row_to_document(r) for r in rows]


# ================================================================
# 文档比对会话 CRUD
# ================================================================

import json as _json  # noqa: E402  — 局部导入避免顶层冲突


def create_comparison_session(
    session_id: str,
    req_filename: str,
    resp_filename: str,
    req_sections: list[dict],
    resp_sections: list[dict],
) -> None:
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO comparison_sessions
               (session_id, req_filename, resp_filename, req_sections_json, resp_sections_json, status)
               VALUES (?, ?, ?, ?, ?, 'pending')""",
            (
                session_id,
                req_filename,
                resp_filename,
                _json.dumps(req_sections, ensure_ascii=False),
                _json.dumps(resp_sections, ensure_ascii=False),
            ),
        )


def update_comparison_session(
    session_id: str,
    analysis_md: str,
    findings: list[dict],
    status: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """UPDATE comparison_sessions
               SET analysis_md = ?, findings_json = ?, status = ?
               WHERE session_id = ?""",
            (analysis_md, _json.dumps(findings, ensure_ascii=False), status, session_id),
        )


def append_comparison_findings(
    session_id: str,
    new_findings: list[dict],
    status: str,
) -> None:
    """追加批次 findings，同步更新 status（流式端点每批完成后调用）。"""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT findings_json FROM comparison_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        existing: list[dict] = _json.loads(row["findings_json"] or "[]") if row else []
        merged = existing + new_findings
        conn.execute(
            """UPDATE comparison_sessions
               SET findings_json = ?, status = ?
               WHERE session_id = ?""",
            (_json.dumps(merged, ensure_ascii=False), status, session_id),
        )


def get_comparison_session(session_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM comparison_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    if row is None:
        return None
    return dict(row)


def list_comparison_sessions() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT session_id, req_filename, resp_filename, findings_json, status, created_at "
            "FROM comparison_sessions ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def delete_comparison_session(session_id: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM comparison_sessions WHERE session_id = ?", (session_id,))
