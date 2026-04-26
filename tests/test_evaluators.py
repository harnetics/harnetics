# [INPUT]: 依赖 pytest、graph.store、evaluators.citation/icd/ai_quality 与 models
# [OUTPUT]: 提供 6 个在线评估器（EA2/EA3/EA4/EA5/EB1/ED3）的单元测试
# [POS]: tests 目录的评估器回归套件，每个评估器覆盖 PASS / FAIL / 边界场景
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

import pytest

from harnetics.evaluators.base import EvalStatus
from harnetics.evaluators.citation import (
    EA2_CitationReality,
    EA3_VersionFreshness,
    EA4_NoCyclicReferences,
    EA5_CoverageRate,
)
from harnetics.evaluators.icd import EB1_ICDConsistency
from harnetics.evaluators.ai_quality import ED3_ConflictMarked
from harnetics.graph import store
from harnetics.models.document import DocumentNode, DocumentEdge, Section
from harnetics.models.icd import ICDParameter


# ================================================================
# 公共 helpers
# ================================================================

def _doc(doc_id: str, status: str = "Approved") -> DocumentNode:
    return DocumentNode(
        doc_id=doc_id, title=f"测试文档 {doc_id}",
        doc_type="Test", department="研发部",
        system_level="Subsystem", engineering_phase="Design",
        version="v1.0", status=status,
    )


def _section(sec_id: str, doc_id: str, content: str) -> Section:
    return Section(
        section_id=sec_id, doc_id=doc_id,
        heading="测试章节", content=content,
        level=2, order_index=1,
    )


def _edge(src: str, tgt: str) -> DocumentEdge:
    return DocumentEdge(
        source_doc_id=src, source_section_id="",
        target_doc_id=tgt, target_section_id="",
        relation="references", confidence=1.0,
    )


# ================================================================
# EA2 — 引用文档真实性
# ================================================================

class TestEA2CitationReality:
    def test_pass_when_cited_doc_exists(self, graph_db_path) -> None:
        store.insert_document(_doc("DOC-EVA-001"))
        draft = {"content_md": "参见 [📎 DOC-EVA-001 §2.1] 中的要求。"}
        result = EA2_CitationReality().evaluate(draft)
        assert result.status == EvalStatus.PASS

    def test_fail_when_cited_doc_missing(self, graph_db_path) -> None:
        # DOC-TST-999 从未入库
        draft = {"content_md": "参见 [\U0001f4ce DOC-TST-999 §1.1] 的规定。"}
        result = EA2_CitationReality().evaluate(draft)
        assert result.status == EvalStatus.FAIL
        assert "DOC-TST-999" in result.detail

    def test_pass_when_no_citations(self, graph_db_path) -> None:
        # 草稿中没有📎标记，视为无引注，应跳过（不拦截）
        draft = {"content_md": "本章介绍系统概述，无外部引用。"}
        result = EA2_CitationReality().evaluate(draft)
        assert result.status == EvalStatus.PASS

    def test_fail_when_one_of_two_citations_missing(self, graph_db_path) -> None:
        store.insert_document(_doc("DOC-EVA-002"))
        draft = {
            "content_md": (
                "第一处 [\U0001f4ce DOC-EVA-002 §1.1]，"
                "第二处 [\U0001f4ce DOC-TST-000 §3.2]。"
            )
        }
        result = EA2_CitationReality().evaluate(draft)
        assert result.status == EvalStatus.FAIL
        assert "DOC-TST-000" in result.detail


# ================================================================
# EA3 — 引用版本最新
# ================================================================

class TestEA3VersionFreshness:
    def test_pass_when_doc_approved(self, graph_db_path) -> None:
        store.insert_document(_doc("DOC-VER-001", status="Approved"))
        draft = {"content_md": "引用 [📎 DOC-VER-001 §1.1]。"}
        result = EA3_VersionFreshness().evaluate(draft)
        assert result.status == EvalStatus.PASS

    def test_warn_when_doc_superseded(self, graph_db_path) -> None:
        store.insert_document(_doc("DOC-VER-002", status="Superseded"))
        draft = {"content_md": "引用 [📎 DOC-VER-002 §2.1] 中的旧版参数。"}
        result = EA3_VersionFreshness().evaluate(draft)
        assert result.status == EvalStatus.WARN
        assert "DOC-VER-002" in result.detail

    def test_pass_when_no_cited_docs(self, graph_db_path) -> None:
        draft = {"content_md": "无引注段落，纯文字描述。"}
        result = EA3_VersionFreshness().evaluate(draft)
        assert result.status == EvalStatus.PASS

    def test_warn_only_superseded_among_mixed(self, graph_db_path) -> None:
        store.insert_document(_doc("DOC-VER-003", status="Approved"))
        store.insert_document(_doc("DOC-VER-004", status="Superseded"))
        draft = {
            "content_md": (
                "有效引用 [📎 DOC-VER-003 §1.1] 和过期引用 [📎 DOC-VER-004 §2.1]。"
            )
        }
        result = EA3_VersionFreshness().evaluate(draft)
        assert result.status == EvalStatus.WARN
        assert "DOC-VER-004" in result.detail
        assert "DOC-VER-003" not in result.detail


# ================================================================
# EA4 — 无循环引用
# ================================================================

class TestEA4NoCyclicReferences:
    def test_pass_when_no_edges(self, graph_db_path) -> None:
        store.insert_document(_doc("DOC-CYC-001"))
        result = EA4_NoCyclicReferences().evaluate({})
        assert result.status == EvalStatus.PASS

    def test_pass_for_linear_chain(self, graph_db_path) -> None:
        # A → B → C，无环
        for did in ("DOC-CYC-A", "DOC-CYC-B", "DOC-CYC-C"):
            store.insert_document(_doc(did))
        store.insert_edges([_edge("DOC-CYC-A", "DOC-CYC-B")])
        store.insert_edges([_edge("DOC-CYC-B", "DOC-CYC-C")])
        result = EA4_NoCyclicReferences().evaluate({})
        assert result.status == EvalStatus.PASS

    def test_block_when_cycle_exists(self, graph_db_path) -> None:
        # A → B → A 形成环
        for did in ("DOC-CYC-X", "DOC-CYC-Y"):
            store.insert_document(_doc(did))
        store.insert_edges([_edge("DOC-CYC-X", "DOC-CYC-Y")])
        store.insert_edges([_edge("DOC-CYC-Y", "DOC-CYC-X")])
        result = EA4_NoCyclicReferences().evaluate({})
        assert result.status == EvalStatus.FAIL

    def test_block_when_self_loop(self, graph_db_path) -> None:
        store.insert_document(_doc("DOC-CYC-SELF"))
        store.insert_edges([_edge("DOC-CYC-SELF", "DOC-CYC-SELF")])
        result = EA4_NoCyclicReferences().evaluate({})
        assert result.status == EvalStatus.FAIL


# ================================================================
# EA5 — 引注覆盖率
# ================================================================

class TestEA5CoverageRate:
    def test_skip_when_no_tech_paragraphs(self, graph_db_path) -> None:
        draft = {"content_md": "本文档为纯文字描述，不含技术参数。"}
        result = EA5_CoverageRate().evaluate(draft)
        assert result.status == EvalStatus.SKIP

    def test_pass_when_full_coverage(self, graph_db_path) -> None:
        # 所有含数字段落都有 📎
        draft = {
            "content_md": (
                "燃烧室压力为 10 MPa [📎 DOC-COV-001 §2.1]。\n\n"
                "喷管出口速度 3200 m/s [📎 DOC-COV-001 §3.1]。\n\n"
                "点火延迟 0.3 s [📎 DOC-COV-001 §4.1]。\n\n"
                "推力 80 kN [📎 DOC-COV-001 §5.1]。\n\n"
                "质量流量 2.5 kg/s [📎 DOC-COV-001 §6.1]。"
            )
        }
        result = EA5_CoverageRate().evaluate(draft)
        assert result.status == EvalStatus.PASS

    def test_warn_when_coverage_below_threshold(self, graph_db_path) -> None:
        # 5个含数字段落，只有1个有 📎 → 20% < 80%
        draft = {
            "content_md": (
                "压力 10 MPa [📎 DOC-COV-002 §1.1]。\n\n"
                "温度 300 K，无引注。\n\n"
                "速度 500 m/s，无引注。\n\n"
                "质量 100 kg，无引注。\n\n"
                "时间 5 s，无引注。"
            )
        }
        result = EA5_CoverageRate().evaluate(draft)
        assert result.status == EvalStatus.WARN
        assert "20%" in result.detail or "0.2" in result.detail.lower() or "1/" in result.detail

    def test_pass_at_exact_threshold(self, graph_db_path) -> None:
        # 5个含数字段落，4个有 📎 → 80% = threshold → PASS
        draft = {
            "content_md": (
                "压力 10 MPa [📎 DOC-COV-003 §1.1]。\n\n"
                "温度 300 K [📎 DOC-COV-003 §2.1]。\n\n"
                "速度 500 m/s [📎 DOC-COV-003 §3.1]。\n\n"
                "质量 100 kg [📎 DOC-COV-003 §4.1]。\n\n"
                "时间 5 s，无引注。"
            )
        }
        result = EA5_CoverageRate().evaluate(draft)
        assert result.status == EvalStatus.PASS


# ================================================================
# EB1 — ICD 参数一致性
# ================================================================

class TestEB1ICDConsistency:
    def test_skip_when_no_icd_params(self, graph_db_path) -> None:
        draft = {"content_md": "燃烧室压力 10 MPa，喷管温度 3200 K。"}
        result = EB1_ICDConsistency().evaluate(draft)
        assert result.status == EvalStatus.SKIP

    def test_pass_when_values_match_icd(self, graph_db_path) -> None:
        store.insert_document(_doc("DOC-ICD-E01"))
        store.insert_icd_parameters([
            ICDParameter(
                param_id="P-E01-001", doc_id="DOC-ICD-E01",
                name="燃烧室压力", interface_type="Pressure",
                subsystem_a="推进系统", subsystem_b="控制系统",
                value="10", unit="MPa",
            )
        ])
        # 草稿中写的是 10，与 ICD 一致
        draft = {"content_md": "系统要求燃烧室压力为 10 MPa，符合 ICD 规定。"}
        result = EB1_ICDConsistency().evaluate(draft)
        assert result.status == EvalStatus.PASS

    def test_fail_when_value_differs_from_icd(self, graph_db_path) -> None:
        store.insert_document(_doc("DOC-ICD-E02"))
        store.insert_icd_parameters([
            ICDParameter(
                param_id="P-E02-001", doc_id="DOC-ICD-E02",
                name="燃烧室压力", interface_type="Pressure",
                subsystem_a="推进系统", subsystem_b="控制系统",
                value="10", unit="MPa",
            )
        ])
        # 直接使用参数名开头，避免前缀导致正则误吞参数名
        draft = {"content_md": "燃烧室压力为 15 MPa。"}
        result = EB1_ICDConsistency().evaluate(draft)
        assert result.status == EvalStatus.FAIL
        assert "燃烧室压力" in result.detail or "15" in str(result.locations)

    def test_pass_when_param_not_in_content(self, graph_db_path) -> None:
        store.insert_document(_doc("DOC-ICD-E03"))
        store.insert_icd_parameters([
            ICDParameter(
                param_id="P-E03-001", doc_id="DOC-ICD-E03",
                name="氧化剂流量", interface_type="Flow",
                subsystem_a="推进系统", subsystem_b="控制系统",
                value="5", unit="kg/s",
            )
        ])
        # 草稿中完全没提到氧化剂流量参数
        draft = {"content_md": "本章描述总体方案，不涉及具体参数。"}
        result = EB1_ICDConsistency().evaluate(draft)
        assert result.status == EvalStatus.PASS


# ================================================================
# ED3 — 冲突明确标记
# ================================================================

class TestED3ConflictMarked:
    def test_pass_when_no_conflicts(self, graph_db_path) -> None:
        draft = {
            "content_md": "系统各参数已完成对齐，无冲突。",
            "conflicts": [],
        }
        result = ED3_ConflictMarked().evaluate(draft)
        assert result.status == EvalStatus.PASS

    def test_pass_when_all_conflicts_marked(self, graph_db_path) -> None:
        draft = {
            "content_md": (
                "推力要求 80 kN ⚠️ 与动力系统 §3.1 存在参数差异，需协调。\n\n"
                "质量预算 500 kg ⚠️ 与结构分析报告存在 50 kg 偏差。"
            ),
            "conflicts": [
                {"doc_a_id": "DOC-A", "doc_b_id": "DOC-B", "description": "推力冲突", "severity": "major"},
                {"doc_a_id": "DOC-A", "doc_b_id": "DOC-C", "description": "质量冲突", "severity": "minor"},
            ],
        }
        result = ED3_ConflictMarked().evaluate(draft)
        assert result.status == EvalStatus.PASS

    def test_fail_when_conflict_not_marked(self, graph_db_path) -> None:
        draft = {
            "content_md": "推力要求 80 kN，符合系统需求。质量预算 500 kg。",
            "conflicts": [
                {"doc_a_id": "DOC-A", "doc_b_id": "DOC-B", "description": "推力冲突", "severity": "major"},
            ],
        }
        result = ED3_ConflictMarked().evaluate(draft)
        assert result.status == EvalStatus.FAIL
        assert "⚠️" in result.detail

    def test_fail_when_fewer_markers_than_conflicts(self, graph_db_path) -> None:
        # 2 个冲突，只有 1 个 ⚠️
        draft = {
            "content_md": "推力 80 kN ⚠️ 存在冲突。质量 500 kg，无标记。",
            "conflicts": [
                {"doc_a_id": "DOC-A", "doc_b_id": "DOC-B", "description": "冲突1", "severity": "major"},
                {"doc_a_id": "DOC-A", "doc_b_id": "DOC-C", "description": "冲突2", "severity": "minor"},
            ],
        }
        result = ED3_ConflictMarked().evaluate(draft)
        assert result.status == EvalStatus.FAIL
