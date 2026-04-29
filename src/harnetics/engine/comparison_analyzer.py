# [INPUT]: 依赖 llm.client.HarneticsLLM、models.document.Section，无图谱依赖（纯计算）
# [OUTPUT]: 对外提供 ComparisonAnalyzer 类：输入双文件章节列表 → 输出 {findings, analysis_md}；
#           analyze_streaming() 生成器 yield SSE 事件 dict（started/batch_progress/completed/error）
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

# 要求文件和应答文件的最大字符数
# 模型规格：Context 1M tokens / Max output 384K tokens
# 中文约 1.5~2 字/token；输入预算 ≈ 600K tokens ≈ 30 万~40 万字符
# 单批最大值留足系统提示与输出空间：req+resp ≤ ~50 万字符
_BATCH_REQ_CHARS = 240_000   # 单批审查大纲最大字符（约 120K~160K tokens）
_BATCH_RESP_CHARS = 240_000  # 单批应答文件最大字符（约 120K~160K tokens）
# 兼容旧调用（保留原名称，指向新常量）
_MAX_REQ_CHARS = _BATCH_REQ_CHARS
_MAX_RESP_CHARS = _BATCH_RESP_CHARS


def _normalize_text(text: str) -> str:
    """归一化文本，便于要求项与模型输出做宽松匹配。"""
    return re.sub(r"\s+", "", text).strip().lower()


def _is_substantive_requirement(section: Section) -> bool:
    """判断章节是否应计入输出校验范围。"""
    heading = section.heading.strip()
    content = section.content.strip()
    if not heading and not content:
        return False
    if heading == "全文":
        return False
    return True


def _expected_requirement_sections(sections: list[Section]) -> list[Section]:
    """返回当前批次预期应产生 findings 的要求项列表。"""
    return [section for section in sections if _is_substantive_requirement(section)]


def _estimate_output_tokens(expected_count: int) -> int:
    """基于要求项数量估算本批输出上限。

    经验值：每条 finding 约 200~350 tokens，给足冗余后按 320 tokens/项估算。
    """
    return max(24_576, min(131_072, expected_count * 320))


def _build_review_request(expected_sections: list[Section], attempt: int) -> str:
    """构造对数量敏感的审查请求，强制模型逐项输出。"""
    headings = "\n".join(
        f"{index + 1}. {section.heading}"
        for index, section in enumerate(expected_sections)
    )
    retry_notice = ""
    if attempt > 1:
        retry_notice = (
            "上一次返回的审查项数量不足。此次必须补齐所有遗漏项，"
            "严格保证输出条数与要求项条数完全一致。\n\n"
        )
    return (
        f"{retry_notice}"
        f"本批【审查大纲】共有 {len(expected_sections)} 个要求项。"
        f"你必须输出严格 {len(expected_sections)} 个 JSON 对象，"
        "并与要求项一一对应，不得合并、不得省略、不得汇总多个要求项。\n\n"
        "要求项清单如下，请逐项输出：\n"
        f"{headings}\n\n"
        "请基于上面的【审查大纲】对【应答文件】进行逐条符合性审查，"
        "输出 JSON 数组格式的审查意见，不含任何其他文字。"
    )


def _matches_requirement(section: Section, finding: dict) -> bool:
    """宽松匹配单个 finding 是否对应某个要求项。"""
    expected = _normalize_text(section.heading)
    if not expected:
        return False
    candidates = [
        _normalize_text(str(finding.get("requirement_heading", ""))),
        _normalize_text(str(finding.get("requirement_ref", ""))),
        _normalize_text(str(finding.get("chapter", ""))),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        if candidate == expected or expected in candidate or candidate in expected:
            return True
    return False


def _placeholder_finding(section: Section) -> dict:
    """当模型漏掉某个要求项时，生成显式占位结果，便于调试和人工复核。"""
    return {
        "chapter": section.heading,
        "requirement_heading": section.heading,
        "requirement_content": section.content[:100],
        "status": "unclear",
        "detail": "模型未返回该要求项的独立审查结果；此项由输出校验逻辑自动补齐，需人工复核。",
        "requirement_ref": section.heading,
        "response_ref": "模型未返回对应结果",
        "_validation_missing": True,
    }


def _validate_findings_against_requirements(
    expected_sections: list[Section],
    findings: list[dict],
    *,
    fill_missing: bool,
) -> tuple[list[dict], list[str], list[str]]:
    """按要求项清单对齐模型输出。

    返回：
    - aligned findings：按 expected_sections 顺序输出；若 fill_missing=True 则补齐缺失项
    - missing headings
    - extra headings
    """
    remaining = findings.copy()
    aligned: list[dict] = []
    missing: list[str] = []

    for section in expected_sections:
        match_index = next(
            (index for index, finding in enumerate(remaining) if _matches_requirement(section, finding)),
            None,
        )
        if match_index is None:
            missing.append(section.heading)
            if fill_missing:
                aligned.append(_placeholder_finding(section))
            continue
        aligned.append(remaining.pop(match_index))

    extra = [
        str(finding.get("requirement_heading") or finding.get("chapter") or "<unknown>")
        for finding in remaining
    ]

    for index, finding in enumerate(aligned, start=1):
        finding["finding_id"] = f"F{index:03d}"

    return aligned, missing, extra


# ================================================================
# 上下文构建 — 分批辅助
# ================================================================

def _render_sections(sections: list[Section], max_chars: int) -> str:
    """将章节列表渲染为文本，超出 max_chars 则截断并注明剩余节数。"""
    parts: list[str] = []
    total = 0
    for i, sec in enumerate(sections):
        chunk = f"[{sec.heading}]\n{sec.content}\n\n"
        if total + len(chunk) > max_chars:
            remaining = len(sections) - i
            parts.append(f"...（余 {remaining} 节超出上下文限制，已自动分批处理）\n")
            break
        parts.append(chunk)
        total += len(chunk)
    return "".join(parts)


def _batch_req_sections(sections: list[Section], batch_chars: int) -> list[list[Section]]:
    """将审查大纲章节按字符数分批，每批不超过 batch_chars。"""
    batches: list[list[Section]] = []
    current: list[Section] = []
    current_chars = 0
    for sec in sections:
        chunk_len = len(sec.heading) + len(sec.content) + 4  # 4 = "[]\n\n"
        if current and current_chars + chunk_len > batch_chars:
            batches.append(current)
            current = []
            current_chars = 0
        current.append(sec)
        current_chars += chunk_len
    if current:
        batches.append(current)
    return batches or [[]]  # 保证至少一批


def _extract_chapter_prefixes(sections: list[Section]) -> set[str]:
    """从章节 heading 中提取数字章节前缀（如 '6.1'、'6.2'）。"""
    prefixes: set[str] = set()
    for sec in sections:
        m = re.match(r"(\d+(?:\.\d+)?)", sec.heading.strip())
        if m:
            prefixes.add(m.group(1))
    return prefixes


def _match_resp_sections(
    req_batch: list[Section],
    all_resp: list[Section],
    max_chars: int,
) -> list[Section]:
    """为当前批次审查大纲选取相关的应答文件章节。

    策略：
    1. 按章节编号前缀匹配优先（精准相关）
    2. 补充其余章节直至达到 max_chars
    """
    prefixes = _extract_chapter_prefixes(req_batch)
    matched: list[Section] = []
    others: list[Section] = []
    for sec in all_resp:
        heading_start = sec.heading.strip()
        if any(heading_start.startswith(p) for p in prefixes):
            matched.append(sec)
        else:
            others.append(sec)

    # 组合：精准匹配优先，其余按顺序补足
    combined = matched + others
    result: list[Section] = []
    total = 0
    for sec in combined:
        chunk_len = len(sec.heading) + len(sec.content) + 4
        if total + chunk_len > max_chars:
            break
        result.append(sec)
        total += chunk_len
    return result


def _build_batch_context(req_batch: list[Section], resp_batch: list[Section]) -> str:
    """将当前批次双文件章节拼装为 LLM 用户消息。"""
    req_text = _render_sections(req_batch, _BATCH_REQ_CHARS)
    resp_text = _render_sections(resp_batch, _BATCH_RESP_CHARS)
    return (
        "## 【审查大纲】内容\n\n"
        + req_text
        + "\n---\n\n"
        + "## 【应答文件】内容\n\n"
        + resp_text
    )


def _build_comparison_context(req_sections: list[Section], resp_sections: list[Section]) -> str:
    """兼容旧接口：直接构建全量上下文（单批）。"""
    return _build_batch_context(req_sections, resp_sections)


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
        logger.warning(
            "comparison.parse_findings: no JSON array found in LLM response len=%d head=%r tail=%r",
            len(raw),
            cleaned[:240],
            cleaned[-240:],
        )
        return []
    try:
        data = json.loads(cleaned[start : end + 1])
        if isinstance(data, list):
            return data
        return []
    except json.JSONDecodeError as exc:
        logger.warning(
            "comparison.parse_findings: JSON decode error=%s head=%r tail=%r",
            exc,
            cleaned[start : min(start + 240, len(cleaned))],
            cleaned[max(end - 240, 0) : end + 1],
        )
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
    validation_missing = sum(1 for f in findings if f.get("_validation_missing"))

    lines = [
        "# 符合性审查报告",
        "",
        f"- **要求文件**：{req_filename}",
        f"- **应答文件**：{resp_filename}",
        f"- **要求项总数**：{total}",
        f"- **自动补齐项**：{validation_missing}",
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
    """文档比对审查引擎：双文件章节 → LLM 逐条审查 → 结构化 findings。

    支持两种调用模式：
    - analyze()：阻塞式，等待全部批次完成后返回（向后兼容）
    - analyze_streaming()：生成器，每批完成后 yield SSE 事件 dict
    """

    def __init__(self, llm: HarneticsLLM | None = None) -> None:
        self._llm = llm or HarneticsLLM()

    # ------------------------------------------------------------------
    # 流式生成器（核心实现）
    # ------------------------------------------------------------------

    def analyze_streaming(
        self,
        session_id: str,
        req_sections: list[Section],
        resp_sections: list[Section],
        req_filename: str,
        resp_filename: str,
    ):
        """分批审查生成器，yield SSE 事件 dict。

        事件类型:
          started        — 开始前，包含 total_batches
          batch_progress — 每批完成，包含 batch_findings
          completed      — 全部完成，包含 analysis_md
          error          — 单批异常（继续处理后续批次）
        """
        batches = _batch_req_sections(req_sections, _BATCH_REQ_CHARS)
        total_batches = len(batches)
        all_findings: list[dict] = []

        logger.info(
            "comparison.streaming.start session_id=%s req_sections=%d resp_sections=%d batches=%d",
            session_id, len(req_sections), len(resp_sections), total_batches,
        )

        yield {"type": "started", "session_id": session_id, "total_batches": total_batches}

        for i, req_batch in enumerate(batches, start=1):
            resp_batch = _match_resp_sections(req_batch, resp_sections, _BATCH_RESP_CHARS)
            context = _build_batch_context(req_batch, resp_batch)
            expected_sections = _expected_requirement_sections(req_batch)
            expected_count = len(expected_sections)
            output_max_tokens = _estimate_output_tokens(expected_count)
            prefixes = sorted(_extract_chapter_prefixes(req_batch))

            logger.info(
                "comparison.streaming.batch session_id=%s batch=%d/%d req_secs=%d expected=%d "
                "resp_secs=%d context_chars=%d output_max_tokens=%d prefixes=%s",
                session_id, i, total_batches,
                len(req_batch), expected_count,
                len(resp_batch), len(context), output_max_tokens,
                prefixes[:12],
            )

            try:
                raw_findings: list[dict] = []
                missing: list[str] = []
                extra: list[str] = []

                for attempt in (1, 2):
                    raw = self._llm.generate_draft(
                        system_prompt=_COMPARISON_SYSTEM_PROMPT,
                        context=context,
                        user_request=_build_review_request(expected_sections, attempt),
                        max_tokens=output_max_tokens,
                    )
                    parsed = _parse_findings(raw)
                    _, missing_probe, extra_probe = _validate_findings_against_requirements(
                        expected_sections,
                        parsed,
                        fill_missing=False,
                    )

                    logger.info(
                        "comparison.streaming.validation session_id=%s batch=%d attempt=%d expected=%d parsed=%d missing=%d extra=%d",
                        session_id,
                        i,
                        attempt,
                        expected_count,
                        len(parsed),
                        len(missing_probe),
                        len(extra_probe),
                    )
                    if missing_probe:
                        logger.warning(
                            "comparison.streaming.validation_missing session_id=%s batch=%d attempt=%d sample=%s",
                            session_id,
                            i,
                            attempt,
                            missing_probe[:10],
                        )
                    if extra_probe:
                        logger.warning(
                            "comparison.streaming.validation_extra session_id=%s batch=%d attempt=%d sample=%s",
                            session_id,
                            i,
                            attempt,
                            extra_probe[:10],
                        )

                    raw_findings = parsed
                    missing = missing_probe
                    extra = extra_probe
                    if not missing or attempt == 2:
                        break

                batch_findings, missing, extra = _validate_findings_against_requirements(
                    expected_sections,
                    raw_findings,
                    fill_missing=True,
                )

                all_findings.extend(batch_findings)

                logger.info(
                    "comparison.streaming.batch_done session_id=%s batch=%d expected=%d findings=%d missing_filled=%d extra_ignored=%d total=%d",
                    session_id,
                    i,
                    expected_count,
                    len(batch_findings),
                    len(missing),
                    len(extra),
                    len(all_findings),
                )

                yield {
                    "type": "batch_progress",
                    "batch": i,
                    "total_batches": total_batches,
                    "expected_findings": expected_count,
                    "missing_filled": len(missing),
                    "extra_ignored": len(extra),
                    "batch_findings": batch_findings,
                    "total_findings": len(all_findings),
                }

            except Exception as exc:  # noqa: BLE001
                logger.exception("comparison.streaming.batch_error session_id=%s batch=%d", session_id, i)
                yield {"type": "error", "message": str(exc), "batch": i}

        analysis_md = _build_analysis_md(all_findings, req_filename, resp_filename)
        logger.info(
            "comparison.streaming.completed session_id=%s total_findings=%d",
            session_id, len(all_findings),
        )
        yield {
            "type": "completed",
            "session_id": session_id,
            "total_findings": len(all_findings),
            "analysis_md": analysis_md,
            "findings": all_findings,
        }

    # ------------------------------------------------------------------
    # 阻塞式接口（向后兼容，委托 analyze_streaming）
    # ------------------------------------------------------------------

    def analyze(
        self,
        session_id: str,
        req_sections: list[Section],
        resp_sections: list[Section],
        req_filename: str,
        resp_filename: str,
    ) -> dict:
        """阻塞式比对分析，等待全部批次完成后返回 {findings, analysis_md}。"""
        findings: list[dict] = []
        analysis_md = ""

        for event in self.analyze_streaming(
            session_id=session_id,
            req_sections=req_sections,
            resp_sections=resp_sections,
            req_filename=req_filename,
            resp_filename=resp_filename,
        ):
            if event["type"] == "batch_progress":
                findings = findings  # 已在 streaming 内部追加到 all_findings
            elif event["type"] == "completed":
                findings = event["findings"]
                analysis_md = event["analysis_md"]

        return {"findings": findings, "analysis_md": analysis_md}
