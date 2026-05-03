-- ============================================================
-- Harnetics 航天文档对齐 — 关系图谱 Schema
-- 7 tables + 7 indexes
-- ============================================================

-- ---- 文档节点 ----
CREATE TABLE IF NOT EXISTS documents (
    doc_id        TEXT PRIMARY KEY,
    title         TEXT NOT NULL,
    doc_type      TEXT NOT NULL,
    department    TEXT NOT NULL,
    system_level  TEXT NOT NULL,
    engineering_phase TEXT NOT NULL,
    version       TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'draft',
    content_hash  TEXT NOT NULL DEFAULT '',
    file_path     TEXT NOT NULL DEFAULT '',
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(doc_type);

-- ---- 章节 ----
CREATE TABLE IF NOT EXISTS sections (
    section_id   TEXT PRIMARY KEY,
    doc_id       TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    heading      TEXT NOT NULL,
    content      TEXT NOT NULL DEFAULT '',
    level        INTEGER NOT NULL DEFAULT 1,
    order_index  INTEGER NOT NULL DEFAULT 0,
    tags         TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_sections_doc ON sections(doc_id);

-- ---- 关系边 ----
CREATE TABLE IF NOT EXISTS edges (
    edge_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    source_doc_id     TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    source_section_id TEXT NOT NULL DEFAULT '',
    target_doc_id     TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    target_section_id TEXT NOT NULL DEFAULT '',
    relation          TEXT NOT NULL,
    confidence        REAL NOT NULL DEFAULT 1.0,
    created_by        TEXT NOT NULL DEFAULT 'system',
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_doc_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_doc_id);

-- ---- ICD 参数 ----
CREATE TABLE IF NOT EXISTS icd_parameters (
    param_id         TEXT PRIMARY KEY,
    doc_id           TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    name             TEXT NOT NULL,
    interface_type   TEXT NOT NULL,
    subsystem_a      TEXT NOT NULL,
    subsystem_b      TEXT NOT NULL,
    value            TEXT NOT NULL DEFAULT '',
    unit             TEXT NOT NULL DEFAULT '',
    range_           TEXT NOT NULL DEFAULT '',
    owner_department TEXT NOT NULL DEFAULT '',
    version          TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_icd_doc ON icd_parameters(doc_id);

-- ---- 版本快照 ----
CREATE TABLE IF NOT EXISTS versions (
    version_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id       TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    version      TEXT NOT NULL,
    content_hash TEXT NOT NULL DEFAULT '',
    file_path    TEXT NOT NULL DEFAULT '',
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_versions_doc ON versions(doc_id);

-- ---- 草稿 ----
CREATE TABLE IF NOT EXISTS drafts (
    draft_id          TEXT PRIMARY KEY,
    request_json      TEXT NOT NULL DEFAULT '{}',
    content_md        TEXT NOT NULL DEFAULT '',
    citations_json    TEXT NOT NULL DEFAULT '[]',
    conflicts_json    TEXT NOT NULL DEFAULT '[]',
    eval_results_json TEXT NOT NULL DEFAULT '{}',
    status            TEXT NOT NULL DEFAULT 'pending',
    generated_by      TEXT NOT NULL DEFAULT '',
    created_at        TEXT NOT NULL DEFAULT (datetime('now')),
    reviewed_at       TEXT
);

-- ---- 变更影响报告 ----
CREATE TABLE IF NOT EXISTS impact_reports (
    report_id            TEXT PRIMARY KEY,
    trigger_doc_id       TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    old_version          TEXT NOT NULL,
    new_version          TEXT NOT NULL,
    changed_sections_json TEXT NOT NULL DEFAULT '[]',
    impacted_docs_json   TEXT NOT NULL DEFAULT '[]',
    summary              TEXT NOT NULL DEFAULT '',
    created_at           TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_impact_trigger ON impact_reports(trigger_doc_id);

-- ---- 文档比对会话 ----
CREATE TABLE IF NOT EXISTS comparison_sessions (
    session_id         TEXT PRIMARY KEY,
    req_filename       TEXT NOT NULL DEFAULT '',
    resp_filename      TEXT NOT NULL DEFAULT '',
    req_sections_json  TEXT NOT NULL DEFAULT '[]',
    resp_sections_json TEXT NOT NULL DEFAULT '[]',
    analysis_md        TEXT NOT NULL DEFAULT '',
    findings_json      TEXT NOT NULL DEFAULT '[]',
    status             TEXT NOT NULL DEFAULT 'pending',
    created_at         TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_comparison_created ON comparison_sessions(created_at DESC);

