# [INPUT]: 依赖 re、graph.store、evaluators.base
# [OUTPUT]: 对外提供 ED1_NoFabrication, ED3_ConflictMarked
# [POS]: evaluators 包的 AI 质量检查域，防止捏造数据和确保冲突标记
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

import re

from harnetics.evaluators.base import (
    BaseEvaluator, EvalLevel, EvalResult, EvalStatus,
)

_NUMBER_RE = re.compile(r"\b(\d+(?:\.\d+)?)\s*(?:kN|MPa|K|km|s|kg|m/s|t|%|°C|Hz|kPa|m|mm|N|W|A|V)?")
_DOC_REF_RE = re.compile(r"DOC-[A-Z]{3}-\d{3}")
_CONFLICT_ANCHOR_RE = re.compile(r"⚠️")


# ============================================================
# [DISABLED] ED1_NoFabrication
# 原因：草稿数字需可追溯到引用文档，误判率高（LLM 改写数字表述后
#       正则无法匹配），导致几乎所有草稿报 WARN/BLOCK。暂时禁用。
# ============================================================
class ED1_NoFabrication:  # DISABLED — 不注册到总线
    """[已禁用] 草稿数字必须可在引用文档溯源。暂时太严格。"""
    evaluator_id = "ED.1"

class ED3_ConflictMarked(BaseEvaluator):
    """检测到的冲突必须在草稿正文中有对应 ⚠️ 标记。"""
    evaluator_id = "ED.3"
    name = "冲突明确标记"
    level = EvalLevel.BLOCK

    def evaluate(self, draft: dict, graph_conn=None) -> EvalResult:
        content = draft.get("content_md", "")
        conflicts = draft.get("conflicts", [])
        if not conflicts:
            return EvalResult(
                evaluator_id=self.evaluator_id, name=self.name,
                status=EvalStatus.PASS, level=self.level,
                detail="无检测到的冲突，无需标记", locations=[],
            )
        conflict_markers = _CONFLICT_ANCHOR_RE.findall(content)
        if len(conflict_markers) < len(conflicts):
            return EvalResult(
                evaluator_id=self.evaluator_id, name=self.name,
                status=EvalStatus.FAIL, level=self.level,
                detail=f"检测到 {len(conflicts)} 处冲突但正文只有 {len(conflict_markers)} 个 ⚠️ 标记",
                locations=[],
            )
        return EvalResult(
            evaluator_id=self.evaluator_id, name=self.name,
            status=EvalStatus.PASS, level=self.level,
            detail=f"{len(conflicts)} 处冲突均已用 ⚠️ 标记", locations=[],
        )
