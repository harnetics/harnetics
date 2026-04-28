# [INPUT]: 依赖 llm.client.HarneticsLLM、models.document.Section，无图谱依赖（纯计算）
# [OUTPUT]: 对外提供 ComparisonAnalyzer 类：输入双文件章节列表 → 输出 {findings, analysis_md}
# [POS]: engine 包的文档比对核心，对标 draft_generator，专用于审查大纲 vs 应答文件的符合性逐条审查
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

import json
import logging
import re

from harnetics.llm.client import HarneticsLLM
from harnetics.models.document import Section

logger = logging.getLogger("harnetics.comparison")

# ================================================================
# System Prompt — 核安全审查专家角色
# ================================================================

_COMPARISON_SYSTEM_PROMPT = """\
你是一名资深核安全审查专家，专职负责核电站安全分析报告的符合性审查。

## 审查任务
你将收到两份文件的内容：
1. 【审查大纲】：规定了应答文件必须满足的具体审查要素（条款、指标、证明材料要求）
2. 【应答文件】：待审查的最终安全分析报告，需证明符合审查大纲的所有要求

## 审查原则
- 逐条覆盖：审查大纲的每一个实质性审查要素都必须在应答文件中得到回应
- 具体可追溯：意见要精确指出应答文件的哪些章节/页面满足或未满足要求
- 专业严谨：意见措辞参照核安全监督局审查实践，避免模糊表述
- 发现缺口：重点识别"应答文件未涵盖"或"回应不充分"的条款

## 严格输出格式
你必须仅输出一个 JSON 数组，不含任何其他文字（不含 markdown 代码块标记），格式如下：
[
  {
    "finding_id": "F001",
    "chapter": "章节编号和名称",
    "requirement_heading": "该要求条款的标题（来自审查大纲）",
    "requirement_content": "要求条款原文前100字",
    "status": "covered 或 partial 或 missing 或 unclear",
    "detail": "具体审查意见：指出应答文件对应位置和覆盖情况，partial/missing须详述缺失内容",
    "requirement_ref": "审查大纲章节/页码标识（如'Page 3'或'6.2节'）",
    "response_ref": "应答文件中对应内容位置（如'Page 15-17'）或'未找到对应内容'"
  }
]

status 值含义：
- covered：应答文件完整覆盖了该要求
- partial：应答文件部分回应了该要求，存在遗漏或不充分
- missing：应答文件未涵盖该要求
- unclear：应答文件相关内容不清晰，无法判断是否满足要求
"""

# 要求文件和应答文件的最大字符数（防止超出模型上下文）
_MAX_REQ_CHARS = 12000
_MAX_RESP_CHARS = 16000


# ================================================================
# 上下文构建
# ================================================================

def _build_comparison_context(req_sections: list[Section], resp_sections: list[Section]) -> str:
    """将双文件章节拼装为 LLM 用户消息，超限截断。"""

    def _render_sections(sections: list[Section], max_chars: int) -> str:
        parts: list[str] = []
        total = 0
        for sec in sections:
            chunk = f"[{sec.heading}]\n{sec.content}\n\n"
            if total + len(chunk) > max_chars:
                remaining = len(sections) - sections.index(sec)
                parts.append(f"...（余 {remaining} 节内容因长度截断，建议缩短文件或分章节比对）\n")
                break
            parts.append(chunk)
            total += len(chunk)
        return "".join(parts)

    req_text = _render_sections(req_sections, _MAX_REQ_CHARS)
    resp_text = _render_sections(resp_sections, _MAX_RESP_CHARS)

    return (
        "## 【审查大纲】内容\n\n"
        + req_text
        + "\n---\n\n"
        + "## 【应答文件】内容\n\n"
        + resp_text
    )


# ================================================================
# Findings 解析
# ================================================================

def _parse_findings(raw: str) -> list[dict]:
    """从 LLM 原始输出中提取 JSON 数组，容错处理。"""
    # 去除 markdown 代码块标记
    cleaned = re.sub(r"```(?:json)?\s*", "", raw.strip())
    cleaned = re.sub(r"```\s*$", "", cleaned.strip())

    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start == -1 or end == -1 or end <= start:
        logger.warning("comparison.parse_findings: no JSON array found in LLM response (len=%d)", len(raw))
        return []
    try:
        data = json.loads(cleaned[start : end + 1])
        if isinstance(data, list):
            return data
        return []
    except json.JSONDecodeError as exc:
        logger.warning("comparison.parse_findings: JSON decode error=%s", exc)
        return []


# ================================================================
# 报告渲染
# ================================================================

def _build_analysis_md(
    findings: list[dict],
    req_filename: str,
    resp_filename: str,
) -> str:
    """将 findings 列表渲染为可读的 Markdown 审查报告。"""
    status_labels = {
        "covered": "✅ 已覆盖",
        "partial": "⚠️ 部分覆盖",
        "missing": "❌ 未覆盖",
        "unclear": "❓ 待明确",
    }

    covered = sum(1 for f in findings if f.get("status") == "covered")
    partial = sum(1 for f in findings if f.get("status") == "partial")
    missing = sum(1 for f in findings if f.get("status") == "missing")
    unclear = sum(1 for f in findings if f.get("status") == "unclear")
    total = len(findings)

    lines = [
        "# 符合性审查报告",
        "",
        f"- **要求文件**：{req_filename}",
        f"- **应答文件**：{resp_filename}",
        "",
        "## 审查概览",
        "",
        "| 状态 | 条款数 | 占比 |",
        "|------|--------|------|",
    ]
    if total > 0:
        lines += [
            f"| ✅ 已覆盖 | {covered} | {covered / total * 100:.0f}% |",
            f"| ⚠️ 部分覆盖 | {partial} | {partial / total * 100:.0f}% |",
            f"| ❌ 未覆盖 | {missing} | {missing / total * 100:.0f}% |",
            f"| ❓ 待明确 | {unclear} | {unclear / total * 100:.0f}% |",
            f"| **合计** | **{total}** | 100% |",
        ]
    else:
        lines.append("| — | 0 | — |")

    lines += ["", "## 逐条审查意见", ""]

    for f in findings:
        status = f.get("status", "unclear")
        label = status_labels.get(status, status)
        req_ref = f.get("requirement_ref", "")
        resp_ref = f.get("response_ref", "")
        req_content = f.get("requirement_content", "")

        lines.append(f"### {f.get('finding_id', '')} {f.get('chapter', '')} — {label}")
        lines.append("")
        lines.append(
            f"**审查条款**：{f.get('requirement_heading', '')} "
            + (f"`[{req_ref}]`" if req_ref else "")
        )
        lines.append("")
        if req_content:
            lines.append(f"> {req_content[:120]}{'...' if len(req_content) > 120 else ''}")
            lines.append("")
        lines.append(f"**审查意见**：{f.get('detail', '')}")
        lines.append("")
        if resp_ref:
            lines.append(f"**应答文件对应位置**：`{resp_ref}`")
            lines.append("")

    return "\n".join(lines)


# ================================================================
# 主引擎
# ================================================================

class ComparisonAnalyzer:
    """文档比对审查引擎：双文件章节 → LLM 逐条审查 → 结构化 findings。"""

    def __init__(self, llm: HarneticsLLM | None = None) -> None:
        self._llm = llm or HarneticsLLM()

    def analyze(
        self,
        session_id: str,
        req_sections: list[Section],
        resp_sections: list[Section],
        req_filename: str,
        resp_filename: str,
    ) -> dict:
        """执行比对分析，返回 {findings: list[dict], analysis_md: str}。"""
        context = _build_comparison_context(req_sections, resp_sections)

        logger.info(
            "comparison.analyze.start session_id=%s req_sections=%d resp_sections=%d context_chars=%d",
            session_id,
            len(req_sections),
            len(resp_sections),
            len(context),
        )

        raw = self._llm.generate_draft(
            system_prompt=_COMPARISON_SYSTEM_PROMPT,
            context=context,
            user_request=(
                "请基于上面的【审查大纲】对【应答文件】进行逐条符合性审查，"
                "输出 JSON 数组格式的审查意见，不含任何其他文字。"
            ),
        )

        findings = _parse_findings(raw)
        logger.info(
            "comparison.analyze.done session_id=%s findings=%d",
            session_id,
            len(findings),
        )

        analysis_md = _build_analysis_md(findings, req_filename, resp_filename)
        return {"findings": findings, "analysis_md": analysis_md}
