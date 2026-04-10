# Data Model: Aerospace Document Alignment

**Phase**: 1 — Design & Contracts
**Date**: 2026-04-10
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

---

## Entity Relationship Overview

```
Document 1──* Section
Document 1──* Edge (as source or target)
Document 1──* ICDParameter (only for ICD type)
Document 1──* Version
Document *──1 Draft (via DraftRequest.related_doc_ids)
Document 1──* ImpactReport (as trigger)
Draft    1──* EvalResult
```

---

## Entities

### Document

航天技术文档实体——系统中所有数据的根对象。

| Field              | Type   | Constraints                                                                         | Description                |
|--------------------|--------|-------------------------------------------------------------------------------------|----------------------------|
| `doc_id`           | TEXT   | **PK**, format: `DOC-[A-Z]{3}-\d{3}`                                                | 文档唯一编号               |
| `title`            | TEXT   | NOT NULL                                                                             | 文档标题                   |
| `doc_type`         | TEXT   | NOT NULL, CHECK IN (ICD, Requirement, Design, TestPlan, TestReport, Analysis, Status, Template, QualityPlan, FMEA, OverallDesign) | 文档类型（11 种）           |
| `department`       | TEXT   |                                                                                     | 所属部门                   |
| `system_level`     | TEXT   | CHECK IN (Mission, System, Subsystem, Unit, Component)                               | 系统层级（5 级）            |
| `engineering_phase`| TEXT   | CHECK IN (Requirement, Design, Integration, Test, Operation)                         | 工程阶段                   |
| `version`          | TEXT   | NOT NULL                                                                             | 当前版本号                 |
| `status`           | TEXT   | DEFAULT 'Approved', CHECK IN (Draft, UnderReview, Approved, Superseded)              | 文档状态                   |
| `content_hash`     | TEXT   |                                                                                     | 文件内容 SHA256 哈希        |
| `file_path`        | TEXT   |                                                                                     | 原始文件存储路径            |
| `created_at`       | TEXT   | DEFAULT datetime('now')                                                              | 创建时间                   |
| `updated_at`       | TEXT   | DEFAULT datetime('now')                                                              | 更新时间                   |

**Validation Rules**:
- `doc_id` 格式必须匹配 `DOC-[A-Z]{3}-\d{3}`
- 上传同 `doc_id` 时视为版本更新，旧版本写入 `versions` 表，documents 表更新为新版本
- `content_hash` 用于去重——相同哈希视为重复上传

---

### Section

文档章节——从 Markdown 标题层级拆分而来。

| Field          | Type    | Constraints                              | Description            |
|----------------|---------|------------------------------------------|------------------------|
| `section_id`   | TEXT    | **PK**, format: `{doc_id}-sec-{heading}` | 章节唯一 ID             |
| `doc_id`       | TEXT    | **FK → documents**, ON DELETE CASCADE     | 所属文档编号            |
| `heading`      | TEXT    |                                          | 章节标题               |
| `content`      | TEXT    |                                          | 章节正文内容            |
| `level`        | INTEGER | DEFAULT 1                                | 标题层级 (1=H1, 2=H2…) |
| `order_index`  | INTEGER | DEFAULT 0                                | 章节排序索引            |
| `tags`         | TEXT    | DEFAULT '[]'                             | JSON array 标签         |

**Validation Rules**:
- `section_id` 自动生成：`{doc_id}-sec-{normalized_heading}`
- `level` 与 Markdown heading 层级对应
- `content` 存储该标题下到下一同级标题之间的全部正文

---

### Edge

文档间关系边——记录文档之间的引用、追溯、约束等关系。

| Field              | Type    | Constraints                                                           | Description        |
|--------------------|---------|-----------------------------------------------------------------------|--------------------|
| `edge_id`          | INTEGER | **PK**, AUTOINCREMENT                                                 | 自增主键           |
| `source_doc_id`    | TEXT    | **FK → documents**, NOT NULL                                          | 源文档编号          |
| `source_section_id`| TEXT    |                                                                       | 源章节 ID（可选）    |
| `target_doc_id`    | TEXT    | **FK → documents**, NOT NULL                                          | 目标文档编号        |
| `target_section_id`| TEXT    |                                                                       | 目标章节 ID（可选）  |
| `relation`         | TEXT    | NOT NULL, CHECK IN (traces_to, references, derived_from, constrained_by, supersedes, impacts) | 关系类型（6 种）     |
| `confidence`       | REAL    | DEFAULT 0.5                                                           | 置信度 [0.0, 1.0]   |
| `created_by`       | TEXT    | DEFAULT 'ai_ingest'                                                   | 创建来源            |
| `created_at`       | TEXT    | DEFAULT datetime('now')                                               | 创建时间            |

**Relation Types**:
- `traces_to`: 设计→需求、测试→设计 的追溯关系
- `references`: 通用引用关系（如质量计划引用标准）
- `derived_from`: 派生关系（如 ICD 从需求派生）
- `constrained_by`: 约束关系（如设计被 ICD 约束）
- `supersedes`: 版本替代关系
- `impacts`: 变更影响关系（由影响分析生成）

**Validation Rules**:
- `source_doc_id != target_doc_id`（不允许自引用）
- `(source_doc_id, target_doc_id, relation)` 唯一约束防止重复边
- 精确编号匹配的边 confidence=1.0，上下文推断的边 confidence=0.85

---

### ICDParameter

ICD 接口控制参数——从 ICD YAML 文档提取。

| Field              | Type | Constraints                                                                      | Description    |
|--------------------|------|----------------------------------------------------------------------------------|----------------|
| `param_id`         | TEXT | **PK**, format: `ICD-[A-Z]{3}-\d{3}`                                             | 参数唯一编号    |
| `doc_id`           | TEXT | **FK → documents**, NOT NULL                                                      | 所属 ICD 文档   |
| `name`             | TEXT | NOT NULL                                                                          | 参数名称        |
| `interface_type`   | TEXT | CHECK IN (Mechanical, Electrical, Software, Thermal, Data, Propellant)            | 接口类型（6 种）|
| `subsystem_a`      | TEXT |                                                                                  | 子系统 A        |
| `subsystem_b`      | TEXT |                                                                                  | 子系统 B        |
| `value`            | TEXT |                                                                                  | 参数值          |
| `unit`             | TEXT |                                                                                  | 单位            |
| `range`            | TEXT |                                                                                  | 值域范围        |
| `owner_department` | TEXT |                                                                                  | 负责部门        |
| `version`          | TEXT |                                                                                  | ICD 版本号      |

**Validation Rules**:
- `param_id` 格式匹配 `ICD-[A-Z]{3}-\d{3}`
- 一个 ICD 文档可有多个参数（DOC-ICD-001 含 12 个）
- `value` 存储为 TEXT，包含单位和范围的原始表示

---

### Draft

AI 生成的对齐草稿——包含请求配置、生成内容、引注和评估结果。

| Field             | Type | Constraints                                                     | Description          |
|-------------------|------|-----------------------------------------------------------------|----------------------|
| `draft_id`        | TEXT | **PK**, format: `DRAFT-YYYYMMDD-NNN`                            | 草稿唯一编号          |
| `request_json`    | TEXT | NOT NULL                                                         | 请求参数 JSON         |
| `content_md`      | TEXT |                                                                 | 生成的 Markdown 内容   |
| `citations_json`  | TEXT | DEFAULT '[]'                                                     | 引注列表 JSON         |
| `conflicts_json`  | TEXT | DEFAULT '[]'                                                     | 冲突列表 JSON         |
| `eval_results_json`| TEXT| DEFAULT '[]'                                                     | Evaluator 结果 JSON    |
| `status`          | TEXT | DEFAULT 'generated', CHECK IN (generating, completed, reviewed, exported) | 草稿状态              |
| `generated_by`    | TEXT | DEFAULT 'gemma4-26b'                                             | 生成模型标识          |
| `created_at`      | TEXT | DEFAULT datetime('now')                                          | 创建时间              |
| `reviewed_at`     | TEXT |                                                                 | 审核时间              |

**request_json schema**:
```json
{
  "requester_department": "动力系统部",
  "doc_type": "TestPlan",
  "system_level": "Subsystem",
  "subject": "TQ-12液氧甲烷发动机地面全工况热试车测试大纲",
  "parent_doc_id": "DOC-SYS-001",
  "template_id": "DOC-TPL-001",
  "related_doc_ids": ["DOC-ICD-001", "DOC-DES-001"]
}
```

**citations_json schema**:
```json
[
  {
    "source_doc_id": "DOC-SYS-001",
    "source_section_id": "sec-3.2",
    "source_text_snippet": "动力系统地面推力 ≥ 650 kN...",
    "relation": "需求依据"
  }
]
```

**conflicts_json schema**:
```json
[
  {
    "parameter": "地面推力",
    "doc_a": {"doc_id": "DOC-ICD-001", "version": "v2.3"},
    "value_a": "650 kN",
    "doc_b": {"doc_id": "DOC-TST-003", "version": "v1.1"},
    "value_b": "600 kN",
    "resolution": "DOC-TST-003 引用 ICD v2.1，应更新至 v2.3"
  }
]
```

---

### ImpactReport

变更影响报告——记录一次文档变更的影响分析结果。

| Field                 | Type | Constraints                    | Description          |
|-----------------------|------|--------------------------------|----------------------|
| `report_id`           | TEXT | **PK**                         | 报告唯一编号          |
| `trigger_doc_id`      | TEXT | **FK → documents**, NOT NULL   | 触发变更的文档        |
| `old_version`         | TEXT |                                | 旧版本号              |
| `new_version`         | TEXT |                                | 新版本号              |
| `changed_sections_json`| TEXT| DEFAULT '[]'                   | 变更章节 JSON         |
| `impacted_docs_json`  | TEXT | DEFAULT '[]'                   | 受影响文档 JSON       |
| `summary`             | TEXT |                                | 影响摘要              |
| `created_at`          | TEXT | DEFAULT datetime('now')        | 创建时间              |

**impacted_docs_json schema**:
```json
[
  {
    "doc_id": "DOC-DES-001",
    "department": "动力系统部",
    "severity": "Critical",
    "affected_sections": ["§3.1 推力设计点"],
    "recommendation": "更新"
  }
]
```

**Severity Rules**:
- `Critical`: 直接引用变更参数（edges 深度 1，relation = constrained_by/traces_to）
- `Major`: 间接引用（edges 深度 2）或 references 关系
- `Minor`: edges 深度 ≥3 或弱关联

---

### Version

文档版本历史——记录每次版本更新。

| Field          | Type    | Constraints                      | Description      |
|----------------|---------|----------------------------------|------------------|
| `version_id`   | INTEGER | **PK**, AUTOINCREMENT            | 自增主键          |
| `doc_id`       | TEXT    | **FK → documents**, NOT NULL     | 文档编号          |
| `version`      | TEXT    | NOT NULL                         | 版本号            |
| `content_hash` | TEXT    |                                  | 该版本内容哈希    |
| `file_path`    | TEXT    |                                  | 该版本文件路径    |
| `created_at`   | TEXT    | DEFAULT datetime('now')          | 版本时间          |

---

### EvalResult (embedded in Draft)

质量检查结果——存储在 Draft.eval_results_json 中。

| Field          | Type   | Constraints                                  | Description    |
|----------------|--------|----------------------------------------------|----------------|
| `evaluator_id` | TEXT   | e.g. "EA.1"                                  | 评估器 ID       |
| `name`         | TEXT   | e.g. "引注完整性"                              | 评估器名称      |
| `status`       | TEXT   | IN (pass, fail, warn, skip)                   | 检查结果        |
| `level`        | TEXT   | IN (block, warn)                              | 严重级别        |
| `detail`       | TEXT   |                                              | 问题描述        |
| `locations`    | LIST   | JSON array of strings                         | 问题位置列表    |

---

## SQLite Schema (DDL)

```sql
-- ================================================================
-- Harnetics 航天文档对齐系统 — 数据库 Schema
-- 引擎: SQLite 3.35+
-- ================================================================

-- 文档表
CREATE TABLE documents (
    doc_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    doc_type TEXT NOT NULL CHECK(doc_type IN (
        'ICD','Requirement','Design','TestPlan','TestReport',
        'Analysis','Status','Template','QualityPlan','FMEA','OverallDesign'
    )),
    department TEXT,
    system_level TEXT CHECK(system_level IN (
        'Mission','System','Subsystem','Unit','Component'
    )),
    engineering_phase TEXT CHECK(engineering_phase IN (
        'Requirement','Design','Integration','Test','Operation'
    )),
    version TEXT NOT NULL,
    status TEXT DEFAULT 'Approved' CHECK(status IN (
        'Draft','UnderReview','Approved','Superseded'
    )),
    content_hash TEXT,
    file_path TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- 章节表
CREATE TABLE sections (
    section_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    heading TEXT,
    content TEXT,
    level INTEGER DEFAULT 1,
    order_index INTEGER DEFAULT 0,
    tags TEXT DEFAULT '[]'
);

-- 文档关系边
CREATE TABLE edges (
    edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_doc_id TEXT NOT NULL REFERENCES documents(doc_id),
    source_section_id TEXT,
    target_doc_id TEXT NOT NULL REFERENCES documents(doc_id),
    target_section_id TEXT,
    relation TEXT NOT NULL CHECK(relation IN (
        'traces_to','references','derived_from',
        'constrained_by','supersedes','impacts'
    )),
    confidence REAL DEFAULT 0.5,
    created_by TEXT DEFAULT 'ai_ingest',
    created_at TEXT DEFAULT (datetime('now'))
);

-- ICD 参数表
CREATE TABLE icd_parameters (
    param_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL REFERENCES documents(doc_id),
    name TEXT NOT NULL,
    interface_type TEXT CHECK(interface_type IN (
        'Mechanical','Electrical','Software','Thermal','Data','Propellant'
    )),
    subsystem_a TEXT,
    subsystem_b TEXT,
    value TEXT,
    unit TEXT,
    range TEXT,
    owner_department TEXT,
    version TEXT
);

-- 文档版本历史
CREATE TABLE versions (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT NOT NULL REFERENCES documents(doc_id),
    version TEXT NOT NULL,
    content_hash TEXT,
    file_path TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- AI 生成的草稿
CREATE TABLE drafts (
    draft_id TEXT PRIMARY KEY,
    request_json TEXT NOT NULL,
    content_md TEXT,
    citations_json TEXT DEFAULT '[]',
    conflicts_json TEXT DEFAULT '[]',
    eval_results_json TEXT DEFAULT '[]',
    status TEXT DEFAULT 'generated' CHECK(status IN (
        'generating','completed','reviewed','exported'
    )),
    generated_by TEXT DEFAULT 'gemma4-26b',
    created_at TEXT DEFAULT (datetime('now')),
    reviewed_at TEXT
);

-- 变更影响报告
CREATE TABLE impact_reports (
    report_id TEXT PRIMARY KEY,
    trigger_doc_id TEXT NOT NULL REFERENCES documents(doc_id),
    old_version TEXT,
    new_version TEXT,
    changed_sections_json TEXT DEFAULT '[]',
    impacted_docs_json TEXT DEFAULT '[]',
    summary TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- ================================================================
-- 索引
-- ================================================================
CREATE INDEX idx_sections_doc ON sections(doc_id);
CREATE INDEX idx_edges_source ON edges(source_doc_id);
CREATE INDEX idx_edges_target ON edges(target_doc_id);
CREATE INDEX idx_edges_relation ON edges(relation);
CREATE INDEX idx_icd_params_doc ON icd_parameters(doc_id);
CREATE INDEX idx_documents_dept ON documents(department);
CREATE INDEX idx_documents_type ON documents(doc_type);
```

---

## Indexes Summary

| Index                 | Table          | Column(s)       | Rationale                        |
|-----------------------|----------------|-----------------|----------------------------------|
| idx_sections_doc      | sections       | doc_id          | 按文档查章节（高频）              |
| idx_edges_source      | edges          | source_doc_id   | 下游追溯查询                     |
| idx_edges_target      | edges          | target_doc_id   | 上游追溯查询                     |
| idx_edges_relation    | edges          | relation        | 按关系类型过滤                   |
| idx_icd_params_doc    | icd_parameters | doc_id          | 按 ICD 文档查参数                |
| idx_documents_dept    | documents      | department      | 按部门筛选文档列表               |
| idx_documents_type    | documents      | doc_type        | 按类型筛选文档列表               |
