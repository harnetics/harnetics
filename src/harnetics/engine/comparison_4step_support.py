"""
# [INPUT]: 依赖 models.document.Section、comparison_analyzer 的 Markdown 报告构建器
# [OUTPUT]: 对外提供 comparison_4step 所需的 prompt 常量、文本归一化、需求校验、结果对齐与报告拼装辅助
# [POS]: engine/comparison_4step 的支撑模块，只承载纯函数与静态提示词，不参与四步流程编排
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""

from __future__ import annotations

import json
import logging
import re

from harnetics.models.document import Section

logger = logging.getLogger("harnetics.comparison_4step")

_VECTOR_TOP_K = 3
_LOCAL_EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
_ALLOWED_FINDING_STATUSES = frozenset({"covered", "partial", "missing", "unclear"})

_STEP1_SYSTEM_PROMPT = """\
你是一名专业的需求分析师，负责从审查大纲中提取所有实质性需求条款。

## 任务
仔细阅读【审查大纲】，提取其中每一条独立的审查要求（requirement）。

## 输出规则
- 必须输出 JSON 数组，不含任何其他文字，不含 markdown 代码块标记
- 每个元素包含：
  - "id": 序号字符串，如 "R001"
  - "heading": 该需求条款的标题或关键词（来自大纲原文）
  - "content": 该需求条款的核心内容描述（不超过200字）
  - "section_ref": 所在章节编号或位置标识
- 不要遗漏任何实质性审查要素，包括子条款
- 不要合并多个独立需求为一条
- 不要输出纯目录性标题（如「第6章」）
"""

_STEP1_USER_REQUEST = "请从以下【审查大纲】中提取所有实质性需求条款，输出 JSON 数组："

_STEP3_SYSTEM_PROMPT = """\
你是一名资深核安全审查专家，负责判断应答文件对每条需求的覆盖程度。

## 任务
对每条需求（requirement），结合其候选应答章节（candidate sections），判断覆盖状态。

## 状态定义
- covered: 应答文件明确、完整地回应了该需求
- partial: 应答文件部分回应，存在遗漏或不充分
- missing: 应答文件未涵盖该需求
- unclear: 无法判断（内容模糊或候选章节不相关）

## 输出规则
- 必须输出 JSON 数组，不含任何其他文字，不含 markdown 代码块标记
- 数组长度 = 本批需求条数，逐一对应，不得省略
- 每个元素必须包含：
  - "requirement_id"
  - "chapter"
  - "requirement_heading"
  - "requirement_content"
  - "status"
  - "detail"
  - "requirement_ref"
  - "response_ref"
- 若候选章节不足以判断，仍要输出该 requirement_id 对应的一条记录，状态填 `unclear`
"""

_STEP4_SYSTEM_PROMPT = """\
你是一名核安全审查主审专家，负责对比对审查结果做全局一致性校验。

## 任务
基于所有审查意见的摘要，完成全局评估：
1. 识别是否存在跨条款的系统性缺失
2. 对整体符合性给出百分比评分（covered=100%，partial=50%，missing/unclear=0%）
3. 给出2~3条最重要的改进建议

## 输出规则
- 必须输出 JSON 对象，不含任何其他文字，不含 markdown 代码块标记
"""


def parse_json_array(raw: str) -> list[dict]:
    cleaned = re.sub(r"```(?:json)?\s*", "", raw.strip())
    cleaned = re.sub(r"```\s*$", "", cleaned.strip())
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start == -1 or end == -1 or end <= start:
        logger.warning("4step.parse_json_array: no array found, len=%d head=%r", len(raw), cleaned[:200])
        return []
    try:
        data = json.loads(cleaned[start : end + 1])
        return data if isinstance(data, list) else []
    except json.JSONDecodeError as exc:
        logger.warning("4step.parse_json_array: decode error=%s", exc)
        return []


def parse_json_object(raw: str) -> dict:
    cleaned = re.sub(r"```(?:json)?\s*", "", raw.strip())
    cleaned = re.sub(r"```\s*$", "", cleaned.strip())
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        logger.warning("4step.parse_json_object: no object found, len=%d", len(raw))
        return {}
    try:
        data = json.loads(cleaned[start : end + 1])
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError as exc:
        logger.warning("4step.parse_json_object: decode error=%s", exc)
        return {}


def render_sections(sections: list[Section], max_chars: int = 60_000) -> str:
    parts: list[str] = []
    total = 0
    for i, sec in enumerate(sections):
        chunk = f"[{sec.heading}]\n{sec.content}\n\n"
        if total + len(chunk) > max_chars:
            parts.append(f"...（余 {len(sections) - i} 节超出上下文限制）\n")
            break
        parts.append(chunk)
        total += len(chunk)
    return "".join(parts)


def text(value: object) -> str:
    return "" if value is None else str(value).strip()


def fallback_requirements(req_sections: list[Section]) -> list[dict]:
    requirements: list[dict] = []
    for sec in req_sections:
        heading = sec.heading.strip()
        if not heading or heading == "全文":
            continue
        requirements.append({
            "id": f"R{len(requirements) + 1:03d}",
            "heading": heading,
            "content": sec.content[:200],
            "section_ref": heading,
        })
    return requirements


def keyword_fallback_match(requirement: dict, resp_sections: list[Section]) -> list[dict]:
    m = re.match(r"(\d+(?:\.\d+)?)", text(requirement.get("section_ref")))
    prefix = m.group(1) if m else None
    results: list[dict] = []
    for sec in resp_sections:
        if prefix and sec.heading.strip().startswith(prefix):
            results.append({"section_id": sec.section_id, "heading": sec.heading, "text": sec.content[:500], "distance": 0.0})
        if len(results) >= _VECTOR_TOP_K:
            break
    if not results:
        for sec in resp_sections[:_VECTOR_TOP_K]:
            results.append({"section_id": sec.section_id, "heading": sec.heading, "text": sec.content[:500], "distance": 1.0})
    return results


def looks_like_directory_heading(text_value: str) -> bool:
    text_value = text_value.strip()
    return not text_value or text_value in {"目录", "目次"} or bool(re.fullmatch(r"第?\d+章", text_value))


def normalize_requirement(req: object, index: int) -> dict | None:
    if not isinstance(req, dict):
        return None
    heading = text(req.get("heading"))
    content = text(req.get("content"))
    section_ref = text(req.get("section_ref")) or heading
    if looks_like_directory_heading(heading) or (not heading and not content):
        return None
    return {
        "id": text(req.get("id")) or f"R{index:03d}",
        "heading": heading or section_ref or f"Requirement {index}",
        "content": content[:200],
        "section_ref": section_ref or heading or f"Requirement {index}",
    }


def validate_scanned_requirements(requirements: list[dict], req_sections: list[Section]) -> list[dict]:
    deduped: list[dict] = []
    seen: set[str] = set()
    seen_ids: set[str] = set()
    for raw_req in requirements:
        req = normalize_requirement(raw_req, len(deduped) + 1)
        if req is None:
            continue
        key = re.sub(r"\s+", "", f"{text(req.get('section_ref'))}|{text(req.get('heading'))}").lower()
        if key in seen:
            continue
        requirement_id = text(req.get("id")) or f"R{len(deduped) + 1:03d}"
        if requirement_id in seen_ids:
            requirement_id = f"R{len(deduped) + 1:03d}"
        seen.add(key)
        seen_ids.add(requirement_id)
        req["id"] = requirement_id
        deduped.append(req)
    meaningful_sections = [s for s in req_sections if s.heading.strip() and s.heading.strip() != "全文"]
    return deduped if len(deduped) >= max(1, int(len(meaningful_sections) * 0.3)) else []


def align_batch_findings(
    batch_reqs: list[dict],
    findings: list[dict],
    placeholder_factory,
) -> tuple[list[dict], int, int]:
    remaining = [finding for finding in findings if isinstance(finding, dict)]
    aligned: list[dict] = []
    missing = 0
    for req in batch_reqs:
        rid = text(req.get("id")).lower()
        heading = text(req.get("heading")).lower()
        section_ref = text(req.get("section_ref")).lower()
        match_index = next(
            (
                idx for idx, finding in enumerate(remaining)
                if text(finding.get("requirement_id")).lower() == rid
                or text(finding.get("requirement_heading")).lower() == heading
                or text(finding.get("requirement_ref")).lower() == section_ref
            ),
            None,
        )
        if match_index is None:
            aligned.append(placeholder_factory(req))
            missing += 1
            continue
        finding = remaining.pop(match_index)
        status = text(finding.get("status")).lower()
        finding["requirement_id"] = text(finding.get("requirement_id")) or text(req.get("id"))
        finding["chapter"] = text(finding.get("chapter")) or text(req.get("section_ref")) or text(req.get("heading"))
        finding["requirement_heading"] = text(finding.get("requirement_heading")) or text(req.get("heading"))
        finding["requirement_content"] = (text(finding.get("requirement_content")) or text(req.get("content")))[:100]
        finding["status"] = status if status in _ALLOWED_FINDING_STATUSES else "unclear"
        finding["detail"] = text(finding.get("detail")) or "模型未返回明确审查意见，此条需人工复核。"
        finding["requirement_ref"] = text(finding.get("requirement_ref")) or text(req.get("section_ref"))
        finding["response_ref"] = text(finding.get("response_ref")) or "未找到对应内容"
        aligned.append(finding)
    return aligned, missing, len(remaining)


def build_step3_request(batch_reqs: list[dict], attempt: int) -> str:
    """构造对数量敏感的 Step3 请求，强制模型逐条返回。"""
    items = "\n".join(
        f"- {text(req.get('id'))}: {text(req.get('heading'))} @ {text(req.get('section_ref'))}"
        for req in batch_reqs
    )
    retry_notice = ""
    if attempt > 1:
        retry_notice = (
            "上一次返回结果数量不足或格式错误。"
            "这一次必须补齐全部 requirement_id，并且每个 requirement_id 恰好返回一条记录。\n\n"
        )
    return (
        f"{retry_notice}"
        f"本批共有 {len(batch_reqs)} 条需求，必须输出严格 {len(batch_reqs)} 个 JSON 对象，"
        "并与下面的 requirement_id 一一对应，不得遗漏、不得合并、不得输出解释性文字。\n\n"
        "需求清单：\n"
        f"{items}\n\n"
        "输出格式示例：\n"
        "[\n"
        '  {"requirement_id":"R001","chapter":"6.1.1","requirement_heading":"需求标题","requirement_content":"需求内容前100字","status":"covered","detail":"具体判断","requirement_ref":"6.1.1","response_ref":"6.1.2"}\n'
        "]"
    )


def build_4step_analysis_md(
    findings: list[dict],
    req_filename: str,
    resp_filename: str,
    compliance_rate: float,
    summary: str,
    corrections: list[dict],
) -> str:
    from harnetics.engine.comparison_analyzer import _build_analysis_md  # noqa: PLC0415

    lines = [
        _build_analysis_md(findings, req_filename, resp_filename),
        "",
        "---",
        "",
        "## 四步全局校验",
        "",
        f"- 整体符合性：{round(compliance_rate * 100, 1)}%",
        f"- 全局结论：{text(summary) or '未生成全局结论'}",
    ]
    normalized = [item for item in corrections if isinstance(item, dict) and text(item.get("description"))]
    if normalized:
        lines.extend(["", "### 重点修正建议", ""])
        for item in normalized:
            lines.append(f"- {text(item.get('type')) or 'suggestion'}: {text(item.get('description'))}")
    return "\n".join(lines)


def coerce_compliance_rate(value: object, findings: list[dict], fallback_factory) -> float:
    fallback = fallback_factory(findings)
    normalized = text(value).removesuffix("%")
    try:
        rate = float(normalized)
    except ValueError:
        return fallback
    if rate > 1.0:
        rate = rate / 100.0 if rate <= 100.0 else fallback
    return round(min(max(rate, 0.0), 1.0), 4)
