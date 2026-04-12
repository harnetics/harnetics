"""
# [INPUT]: 依赖 pytest、FastAPI TestClient、graph.store、graph.indexer、evaluators、engine
# [OUTPUT]: MVP 端到端场景测试：init→ingest→verify→draft(mock LLM)→evaluate→impact
# [POS]: tests/test_e2e 的主场景，覆盖 US1-US6 完整用户旅程
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---- 夹具 ---------------------------------------------------------------

@pytest.fixture()
def e2e_app(tmp_path: Path):
    """隔离环境：独立 SQLite + ChromaDB，不影响开发数据库。"""
    import os
    db_path = tmp_path / "e2e.db"
    chroma_path = tmp_path / "chroma"

    os.environ["HARNETICS_GRAPH_DB_PATH"] = str(db_path)
    os.environ["HARNETICS_CHROMA_DIR"] = str(chroma_path)

    from harnetics.graph.store import init_db
    init_db(db_path)

    from harnetics.api.app import create_api_app
    return create_api_app()


@pytest.fixture()
def client(e2e_app):
    with TestClient(e2e_app, raise_server_exceptions=True) as c:
        yield c


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures"


def _upload_inline_markdown(client: TestClient, filename: str, content: str) -> str:
    res = client.post(
        "/api/documents/upload",
        files={"file": (filename, content.encode("utf-8"), "text/markdown")},
    )
    assert res.status_code == 200, res.text
    return res.json()["doc_id"]


# ================================================================
# T1: 健康检查
# ================================================================

def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


# ================================================================
# T2: 文档上传（US1）
# ================================================================

def test_upload_markdown_documents(client):
    """上传 fixtures/design/DOC-DES-001.md，验证文档进入库。"""
    md_file = FIXTURE_ROOT / "design" / "DOC-DES-001.md"
    if not md_file.exists():
        pytest.skip("fixture file not found")

    with md_file.open("rb") as f:
        res = client.post(
            "/api/documents/upload",
            files={"file": (md_file.name, f, "text/markdown")},
        )
    assert res.status_code == 200, res.text
    data = res.json()
    assert "doc_id" in data

    doc_id = data["doc_id"]

    # 验证文档可查询
    res2 = client.get("/api/documents")
    assert res2.status_code == 200
    body = res2.json()
    # /api/documents 返回 {"total": N, "documents": [...]}
    docs_list = body.get("documents", body) if isinstance(body, dict) else body
    ids = [d["doc_id"] for d in docs_list]
    assert doc_id in ids


def test_upload_icd_yaml(client):
    """上传 ICD YAML，验证 ICD 参数被解析入库。"""
    yaml_file = FIXTURE_ROOT / "icd" / "DOC-ICD-001.yaml"
    if not yaml_file.exists():
        pytest.skip("fixture file not found")

    with yaml_file.open("rb") as f:
        res = client.post(
            "/api/documents/upload",
            files={"file": (yaml_file.name, f, "application/x-yaml")},
        )
    assert res.status_code == 200, res.text

    res_icd = client.get("/api/icd/parameters")
    assert res_icd.status_code == 200
    params = res_icd.json()
    assert len(params) > 0, "ICD 参数应被解析入库"


# ================================================================
# T3: 文档详情 & 章节（US1）
# ================================================================

def test_document_detail_and_sections(client):
    md_file = FIXTURE_ROOT / "requirements" / "DOC-SYS-001.md"
    if not md_file.exists():
        pytest.skip("fixture file not found")

    with md_file.open("rb") as f:
        res = client.post(
            "/api/documents/upload",
            files={"file": (md_file.name, f, "text/markdown")},
        )
    assert res.status_code == 200
    doc_id = res.json()["doc_id"]

    res_detail = client.get(f"/api/documents/{doc_id}")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    # /api/documents/{doc_id} 返回 {"document": {...}, "sections": [...], ...}
    doc_data = detail.get("document", detail)
    assert doc_data.get("doc_id") == doc_id

    res_secs = client.get(f"/api/documents/{doc_id}/sections")
    assert res_secs.status_code == 200
    secs_body = res_secs.json()
    secs_list = secs_body.get("sections", secs_body) if isinstance(secs_body, dict) else secs_body
    assert isinstance(secs_list, list)


# ================================================================
# T4: 草稿生成（US2，mock LLM）
# ================================================================

def test_draft_generation_with_mock_llm(client):
    """注入 mock LLM 客户端，避免真实 Ollama 调用。"""
    mock_draft_content = (
        "# 测试草稿\n"
        "推进系统推力参数：650 kN。[📎 DOC-SYS-001 §sec-1]\n"
    )

    with patch("harnetics.api.routes.draft.HarneticsLLM") as MockLLM:
        instance = MockLLM.return_value
        instance.generate_draft.return_value = mock_draft_content
        instance.check_availability.return_value = True

        res = client.post(
            "/api/draft/generate",
            json={
                "subject": "推进与结构接口规格草稿",
                "related_doc_ids": [],
                "template_id": "",
            },
        )

    assert res.status_code == 200, res.text
    data = res.json()
    assert "draft_id" in data
    assert data["status"] in ("completed", "pending", "eval_pass", "blocked")

    draft_id = data["draft_id"]

    # 验证草稿可查询
    res2 = client.get(f"/api/draft/{draft_id}")
    assert res2.status_code == 200
    assert res2.json()["draft_id"] == draft_id


# ================================================================
# T5: 评估流程（US6）
# ================================================================

def test_evaluator_run_on_draft(client):
    """生成草稿后运行评估，验证返回 EvalResult 列表。"""
    mock_content = "## 草稿\n本文档无引注内容，评估应产生警告。\n"

    with patch("harnetics.api.routes.draft.HarneticsLLM") as MockLLM:
        instance = MockLLM.return_value
        instance.generate_draft.return_value = mock_content

        gen_res = client.post(
            "/api/draft/generate",
            json={"subject": "评估测试草稿", "related_doc_ids": []},
        )
    assert gen_res.status_code == 200
    draft_id = gen_res.json()["draft_id"]

    eval_res = client.post(f"/api/evaluate/{draft_id}")
    assert eval_res.status_code == 200
    data = eval_res.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) > 0


# ================================================================
# T6: 影响分析（US3）
# ================================================================

def test_impact_analysis(client):
    """上传文档后触发影响分析，验证返回报告。"""
    md_file = FIXTURE_ROOT / "design" / "DOC-OVR-001.md"
    if not md_file.exists():
        pytest.skip("fixture file not found")

    with md_file.open("rb") as f:
        res = client.post(
            "/api/documents/upload",
            files={"file": (md_file.name, f, "text/markdown")},
        )
    assert res.status_code == 200
    doc_id = res.json()["doc_id"]

    impact_res = client.post(
        "/api/impact/analyze",
        json={"doc_id": doc_id, "old_version": "v1.0", "new_version": "v2.0"},
    )
    assert impact_res.status_code == 200
    data = impact_res.json()
    assert data["trigger_doc_id"] == doc_id
    assert data["analysis_mode"] in {"ai_vector", "heuristic"}
    assert "impacted_docs" in data
    assert "report_id" in data


def test_impact_analysis_finds_documents_that_reference_trigger_doc(client):
    source_doc_id = _upload_inline_markdown(
        client,
        "DOC-SRC-001.md",
        """---
doc_id: DOC-SRC-001
title: 上游需求文档
doc_type: Requirement
department: 系统工程部
system_level: System
engineering_phase: Requirement
version: v1.0
status: Approved
---
# 1. 文档说明
这里定义系统级需求。
""",
    )
    dependent_doc_id = _upload_inline_markdown(
        client,
        "DOC-DEP-001.md",
        """---
doc_id: DOC-DEP-001
title: 依赖该需求的设计文档
doc_type: Design
department: 动力系统部
system_level: Subsystem
engineering_phase: Design
version: v1.0
status: Approved
---
# 1. 设计约束
本文档基于 DOC-SRC-001 中的约束展开详细设计。
""",
    )

    impact_res = client.post(
        "/api/impact/analyze",
        json={"doc_id": source_doc_id, "old_version": "v1.0", "new_version": "v1.1"},
    )

    assert impact_res.status_code == 200, impact_res.text
    data = impact_res.json()
    impacted_ids = [doc["doc_id"] for doc in data["impacted_docs"]]
    assert dependent_doc_id in impacted_ids


def test_draft_route_uses_app_settings_for_llm(client):
    from types import SimpleNamespace

    from harnetics.config import Settings

    client.app.state.settings = Settings(
        graph_db_path=client.app.state.settings.graph_db_path,
        chromadb_path=client.app.state.settings.chromadb_path,
        llm_model="gemma4:26b",
        llm_base_url="http://localhost:11434",
        llm_api_key="sk-test",
    )

    with patch("harnetics.api.routes.draft.HarneticsLLM") as MockLLM, patch(
        "harnetics.api.routes.draft.DraftGenerator"
    ) as MockGenerator:
        llm_instance = MockLLM.return_value
        MockGenerator.return_value.generate.return_value = SimpleNamespace(
            draft_id="DRAFT-TEST-001",
            status="completed",
            content_md="# test",
            citations=[],
            conflicts=[],
            eval_results_json="[]",
            generated_by="gemma4:26b",
            created_at="",
        )

        res = client.post(
            "/api/draft/generate",
            json={
                "subject": "路由配置传递测试",
                "related_doc_ids": [],
                "template_id": "",
                "source_report_id": "RPT-001",
            },
        )

    assert res.status_code == 200, res.text
    MockLLM.assert_called_once_with(
        model="gemma4:26b",
        api_base="http://localhost:11434",
        api_key="sk-test",
    )
    MockGenerator.assert_called_once_with(llm=llm_instance)
    assert MockGenerator.return_value.generate.call_args.args[0]["source_report_id"] == "RPT-001"


def test_impact_analysis_localizes_sections_for_section_aware_edges(client):
    upstream_doc_id = _upload_inline_markdown(
        client,
        "DOC-UPR-001.md",
        """---
doc_id: DOC-UPR-001
title: 上游需求文档
doc_type: Requirement
department: 系统工程部
system_level: System
engineering_phase: Requirement
version: v1.0
status: Approved
---
# 上游需求

## 1. 动力需求

**REQ-UPR-001** 发动机点火压力应不低于 10.0 MPa。
""",
    )
    downstream_doc_id = _upload_inline_markdown(
        client,
        "DOC-DSN-001.md",
        """---
doc_id: DOC-DSN-001
title: 下游设计文档
doc_type: Design
department: 动力系统部
system_level: Subsystem
engineering_phase: Design
version: v1.0
status: Approved
---
# 下游设计

## 1. 设计约束

本设计基于 DOC-UPR-001 的 **REQ-UPR-001**，将点火压力设计值设置为 10.2 MPa。
""",
    )

    sections_res = client.get(f"/api/documents/{upstream_doc_id}/sections")
    assert sections_res.status_code == 200
    sections_body = sections_res.json()
    sections = sections_body.get("sections", sections_body)
    changed_section_id = next(
        section["section_id"] for section in sections if "REQ-UPR-001" in section["content"]
    )

    impact_res = client.post(
        "/api/impact/analyze",
        json={
            "doc_id": upstream_doc_id,
            "old_version": "v1.0",
            "new_version": "v1.1",
            "changed_section_ids": [changed_section_id],
        },
    )

    assert impact_res.status_code == 200, impact_res.text
    impacted = next(
        doc for doc in impact_res.json()["impacted_docs"] if doc["doc_id"] == downstream_doc_id
    )
    assert impacted["affected_sections"]
    assert impacted["analysis_mode"] in {"ai_vector", "heuristic"}
    first_section = impacted["affected_sections"][0]
    assert "section_id" in first_section


def test_document_search_route_falls_back_to_keyword_when_embedding_unavailable(client):
    client.app.state.embedding_store = None

    target_doc_id = _upload_inline_markdown(
        client,
        "DOC-TST-002.md",
        """---
doc_id: DOC-TST-002
title: 涡轮泵性能试验大纲
doc_type: TestPlan
department: 试验与验证部
system_level: Subsystem
engineering_phase: Test
version: v1.0
status: Approved
---
# 涡轮泵试验

本文档定义涡轮泵性能试验工况与验收准则。
""",
    )
    _upload_inline_markdown(
        client,
        "DOC-ICD-009.md",
        """---
doc_id: DOC-ICD-009
title: 异构载荷接口控制文件
doc_type: ICD
department: 航电部
system_level: System
engineering_phase: Design
version: v1.0
status: Approved
---
# 接口控制

本文档描述载荷电气接口。
""",
    )

    res = client.get("/api/documents/search?q=涡轮泵性能试验&top_k=5")

    assert res.status_code == 200, res.text
    data = res.json()
    assert data["analysis_mode"] == "keyword"
    assert data["results"][0]["doc_id"] == target_doc_id
    assert data["results"][0]["relevance_score"] > 0


# ================================================================
# T7: 图谱 API（US4）
# ================================================================

def test_graph_api_returns_structure(client):
    res = client.get("/api/graph")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "edges" in data


def test_stale_references_endpoint(client):
    res = client.get("/api/graph/stale")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


# ================================================================
# T8: 系统状态（US5）
# ================================================================

def test_status_endpoint(client):
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert "documents" in data
    assert "drafts" in data
    assert "stale_references" in data
    assert "llm_model" in data
    assert "llm_base_url" in data
    assert "llm_effective_model" in data
    assert "llm_effective_base_url" in data
    assert "embedding_model" in data
    assert "embedding_base_url" in data
    assert "llm_error" in data
    assert "embedding_error" in data
    assert "config_env_file" in data


def test_dashboard_stats_alias_endpoint(client):
    status_res = client.get("/api/status")
    stats_res = client.get("/api/dashboard/stats")

    assert status_res.status_code == 200
    assert stats_res.status_code == 200
    assert stats_res.json() == status_res.json()
