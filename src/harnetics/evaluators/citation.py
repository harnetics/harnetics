# [INPUT]: 依赖 re、graph.store、evaluators.base
# [OUTPUT]: 对外提供 EA1-EA5 五个引注质量检查器
# [POS]: evaluators 包的引注检查域，验证草稿引注完整性、真实性、版本与覆盖率
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

import re

from harnetics.evaluators.base import (
    BaseEvaluator, EvalLevel, EvalResult, EvalStatus,
)

# 📎 引注标记正则：匹配 [📎 DOC-XXX-YYY §X.X]
_CITATION_RE = re.compile(r"\[📎\s*(DOC-[A-Z]{3}-\d{3})\s*§[\d.]+\]")
# 纯文档编号引用
_DOC_REF_RE = re.compile(r"DOC-[A-Z]{3}-\d{3}")
# 含数字/参数的技术段落（数字 + 可选单位）
_TECH_PARA_RE = re.compile(r"\d+(?:\.\d+)?\s*(?:kN|MPa|K|km|s|kg|m/s|t|%|°C|Hz)?")


# ============================================================
# [DISABLED] EA1_CitationCompleteness
# 原因：要求每个含数字段落都有 📎 标记，LLM 输出很难稳定满足，
#       导致几乎所有草稿都被阻断。暂时禁用，待提示词工程成熟后重启。
# ============================================================
# class EA1_CitationCompleteness(BaseEvaluator):
#     """每个含数字/参数的技术段落必须有📎来源标注。"""
#     evaluator_id = "EA.1"
#     name = "引注完整性"
#     level = EvalLevel.BLOCK
#
#     def evaluate(self, draft: dict, graph_conn=None) -> EvalResult:
#         content = draft.get("content_md", "")
#         paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
#         missing: list[str] = []
#         for p in paragraphs:
#             if _TECH_PARA_RE.search(p) and "📎" not in p:
#                 snippet = p[:60].replace("\n", " ")
#                 missing.append(snippet)
#         if missing:
#             return EvalResult(
#                 evaluator_id=self.evaluator_id, name=self.name,
#                 status=EvalStatus.FAIL, level=self.level,
#                 detail=f"发现 {len(missing)} 个含数字段落缺少引注标记",
#                 locations=missing[:5],
#             )
#         return EvalResult(
#             evaluator_id=self.evaluator_id, name=self.name,
#             status=EvalStatus.PASS, level=self.level,
#             detail="所有技术段落均有来源引注", locations=[],
#         )


class EA1_CitationCompleteness:  # DISABLED — 不注册到总线
    """[已禁用] 每个含数字段落必须有 📎。暂时太严格。"""
    evaluator_id = "EA.1"

class EA2_CitationReality(BaseEvaluator):
    """引注中的文档编号必须在图谱中真实存在。"""
    evaluator_id = "EA.2"
    name = "引用文档真实性"
    level = EvalLevel.BLOCK

    def evaluate(self, draft: dict, graph_conn=None) -> EvalResult:
        from harnetics.graph import store
        content = draft.get("content_md", "")
        cited = set(_CITATION_RE.findall(content))
        missing = [d for d in cited if store.get_document(d) is None]
        if missing:
            return EvalResult(
                evaluator_id=self.evaluator_id, name=self.name,
                status=EvalStatus.FAIL, level=self.level,
                detail=f"引注文档不存在：{', '.join(missing)}",
                locations=missing,
            )
        return EvalResult(
            evaluator_id=self.evaluator_id, name=self.name,
            status=EvalStatus.PASS, level=self.level,
            detail=f"所有 {len(cited)} 个引注文档均在图谱中存在", locations=[],
        )


class EA3_VersionFreshness(BaseEvaluator):
    """引注版本应为最新，否则警告。"""
    evaluator_id = "EA.3"
    name = "引用版本最新"
    level = EvalLevel.WARN

    def evaluate(self, draft: dict, graph_conn=None) -> EvalResult:
        from harnetics.graph import store
        # 检查草稿的引用文档列表中有无已被 Superseded 的版本
        content = draft.get("content_md", "")
        cited_ids = set(_CITATION_RE.findall(content))
        stale: list[str] = []
        for doc_id in cited_ids:
            doc = store.get_document(doc_id)
            if doc and doc.status == "Superseded":
                stale.append(doc_id)
        if stale:
            return EvalResult(
                evaluator_id=self.evaluator_id, name=self.name,
                status=EvalStatus.WARN, level=self.level,
                detail=f"引用文档版本已过期：{', '.join(stale)}",
                locations=stale,
            )
        return EvalResult(
            evaluator_id=self.evaluator_id, name=self.name,
            status=EvalStatus.PASS, level=self.level,
            detail="所有引用文档版本均为最新", locations=[],
        )


class EA4_NoCyclicReferences(BaseEvaluator):
    """文档图谱中不能存在循环引用（DFS 环检测）。"""
    evaluator_id = "EA.4"
    name = "无循环引用"
    level = EvalLevel.BLOCK

    def evaluate(self, draft: dict, graph_conn=None) -> EvalResult:
        from harnetics.graph import store
        docs = store.get_documents()
        # 构建邻接表
        graph: dict[str, list[str]] = {d.doc_id: [] for d in docs}
        for d in docs:
            _, downstream = store.get_edges_for_doc(d.doc_id)
            for edge in downstream:
                graph.setdefault(edge.source_doc_id, []).append(edge.target_doc_id)
        # DFS 环检测
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for nb in graph.get(node, []):
                if nb not in visited:
                    if has_cycle(nb):
                        return True
                elif nb in rec_stack:
                    return True
            rec_stack.discard(node)
            return False

        cycle_nodes: list[str] = []
        for node in list(graph):
            if node not in visited:
                if has_cycle(node):
                    cycle_nodes.append(node)

        if cycle_nodes:
            return EvalResult(
                evaluator_id=self.evaluator_id, name=self.name,
                status=EvalStatus.FAIL, level=self.level,
                detail=f"检测到循环引用节点：{', '.join(cycle_nodes)}",
                locations=cycle_nodes,
            )
        return EvalResult(
            evaluator_id=self.evaluator_id, name=self.name,
            status=EvalStatus.PASS, level=self.level,
            detail="文档图谱无循环引用", locations=[],
        )


class EA5_CoverageRate(BaseEvaluator):
    """技术段落引注覆盖率应 ≥ 80%。"""
    evaluator_id = "EA.5"
    name = "引注覆盖率"
    level = EvalLevel.WARN

    THRESHOLD = 0.8

    def evaluate(self, draft: dict, graph_conn=None) -> EvalResult:
        content = draft.get("content_md", "")
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        tech = [p for p in paragraphs if _TECH_PARA_RE.search(p)]
        if not tech:
            return EvalResult(
                evaluator_id=self.evaluator_id, name=self.name,
                status=EvalStatus.SKIP, level=self.level,
                detail="未发现技术段落，跳过覆盖率检查", locations=[],
            )
        cited = [p for p in tech if "📎" in p]
        rate = len(cited) / len(tech)
        if rate < self.THRESHOLD:
            return EvalResult(
                evaluator_id=self.evaluator_id, name=self.name,
                status=EvalStatus.WARN, level=self.level,
                detail=f"引注覆盖率 {rate:.0%}（要求 ≥ {self.THRESHOLD:.0%}），共 {len(tech)} 技术段，{len(cited)} 有引注",
                locations=[],
            )
        return EvalResult(
            evaluator_id=self.evaluator_id, name=self.name,
            status=EvalStatus.PASS, level=self.level,
            detail=f"引注覆盖率 {rate:.0%}，满足要求", locations=[],
        )
