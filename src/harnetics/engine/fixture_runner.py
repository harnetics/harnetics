"""
# [INPUT]: 依赖 pathlib, yaml, re, uuid, datetime; evaluators.build_default_bus; engine.evolution.signals.write_draft_signal
# [OUTPUT]: 对外提供 list_scenarios()、run_scenario()、import_fixture_dir()；无 LLM 调用，直接评估夹具草稿
# [POS]: engine 包的夹具场景引擎；读取 fixtures/evaluator-test/ 下的 DRAFT 文档 → 评估 → 写进化信号
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""
from __future__ import annotations

import re
import uuid
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml

logger = logging.getLogger("uvicorn.error")

# ---- 场景元数据 ---------------------------------------------------------

@dataclass
class FixtureScenario:
    scenario_id: str        # e.g. "EA2-PASS"
    evaluator: str          # e.g. "EA2"
    label: str              # 人类可读标签
    expected_outcome: str   # "pass" | "warn" | "fail"
    fixture_path: str       # 相对路径


@dataclass
class FixtureRunResult:
    scenario_id: str
    draft_id: str
    outcome: str            # "pass" | "blocked"
    expected_outcome: str
    match: bool             # outcome 与 expected 是否吻合
    eval_results: list[dict] = field(default_factory=list)
    error: str = ""


# ---- 场景目录扫描 -------------------------------------------------------

# 文件名中的预期结果关键词
_EXPECTED_PATTERN = re.compile(r"-(PASS|FAIL|WARN|HIGH-COV|LOW-COV|MIXED|CYC)", re.IGNORECASE)

_OUTCOME_MAP = {
    "PASS":     "pass",
    "HIGH-COV": "pass",
    "FAIL":     "fail",
    "WARN":     "warn",
    "LOW-COV":  "warn",
    "MIXED":    "warn",    # EA3 混合场景：含 WARN，视为 warn
    "CYC":      "fail",   # EA4 循环文档本身不作为 DRAFT 场景
}

# 跳过这些不是草稿的文件（源文档 / ICD / 循环测试节点）
_SKIP_STEMS = {
    "DOC-EA2-REAL",
    "DOC-EA3-CURRENT",
    "DOC-EA3-OLD",
    "DOC-EA4-A",
    "DOC-EA4-B",
    "DOC-EA4-C",
    "DOC-EA4-CYC-X",
    "DOC-EA4-CYC-Y",
    "DOC-EB1-ICD",
}

# EA5 无引注的 DRAFT → evaluator bus 运行，EA5 报 warn
_EVALUATOR_LABELS = {
    "EA2": "引注现实性",
    "EA3": "引注版本新鲜度",
    "EA4": "无循环引用",
    "EA5": "技术段落覆盖率",
    "EB1": "接口参数 ICD 一致性",
    "ED3": "冲突明确标记",
}


def _extract_frontmatter(text: str) -> tuple[dict, str]:
    """拆分 YAML frontmatter 和 body，返回 (meta_dict, body_str)。"""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_raw = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")
    try:
        meta = yaml.safe_load(fm_raw) or {}
    except yaml.YAMLError:
        meta = {}
    return meta, body


def list_scenarios(base_dir: str | Path | None = None) -> list[FixtureScenario]:
    """扫描 fixtures/evaluator-test/ 返回所有 DRAFT 场景的元数据列表。"""
    root = Path(base_dir) if base_dir else Path("fixtures") / "evaluator-test"
    if not root.is_dir():
        return []

    scenarios: list[FixtureScenario] = []
    for md_file in sorted(root.rglob("*.md")):
        stem = md_file.stem
        # 跳过 README 和已知非草稿文件
        if stem in _SKIP_STEMS or stem.upper() in {"README", "AGENTS"}:
            continue
        # 从文件名推断所属校验器
        parts = stem.split("-")
        evaluator = parts[1] if len(parts) >= 2 else "???"
        # 从文件名推断预期结果
        m = _EXPECTED_PATTERN.search(stem)
        keyword = m.group(1).upper() if m else "PASS"
        expected = _OUTCOME_MAP.get(keyword, "pass")
        label = _EVALUATOR_LABELS.get(evaluator, evaluator)

        scenarios.append(FixtureScenario(
            scenario_id=stem,
            evaluator=evaluator,
            label=f"{label} — {stem}",
            expected_outcome=expected,
            fixture_path=str(md_file.relative_to(Path.cwd()) if md_file.is_absolute() else md_file),
        ))
    return scenarios


# ---- 夹具导入 -----------------------------------------------------------

def import_fixture_dir(base_dir: str | Path) -> list[str]:
    """将 base_dir 下所有非草稿源文档导入图谱（幂等）。返回导入的 doc_id 列表。"""
    from harnetics.graph.indexer import DocumentIndexer

    root = Path(base_dir)
    if not root.is_dir():
        raise ValueError(f"路径不存在或不是目录: {base_dir}")

    indexer = DocumentIndexer(embedding_store=None)
    imported: list[str] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name in {"README.md", "AGENTS.md"}:
            continue
        if path.suffix.lower() not in (".md", ".yaml", ".yml"):
            continue
        # 跳过草稿文件（文件名含 DRAFT）
        if "DRAFT" in path.stem.upper():
            continue
        try:
            doc = indexer.ingest_document(str(path))
            imported.append(doc.doc_id)
            logger.info("fixture.import.ok doc_id=%s path=%s", doc.doc_id, path)
        except Exception as exc:
            logger.warning("fixture.import.skip path=%s error=%s", path, exc)

    return imported


# ---- 场景运行 -----------------------------------------------------------

# ED3 场景的模拟冲突列表（正常情况下由冲突检测器注入）
_ED3_MOCK_CONFLICTS = [
    {"doc_a_id": "DOC-EB1-ICD", "doc_b_id": "DOC-EA2-REAL",
     "description": "燃烧室压力定义存在歧义", "severity": "warning"},
    {"doc_a_id": "DOC-EA3-CURRENT", "doc_b_id": "DOC-EA3-OLD",
     "description": "制导精度指标版本冲突", "severity": "warning"},
]


def run_scenario(scenario_id: str, base_dir: str | Path | None = None) -> FixtureRunResult:
    """
    读取夹具 DRAFT 文件 → 构造 draft_dict → 评估 → 写进化信号。
    绕过 LLM，不依赖 EmbeddingStore。
    """
    root = Path(base_dir) if base_dir else Path("fixtures") / "evaluator-test"

    # 定位文件
    candidates = list(root.rglob(f"{scenario_id}.md"))
    if not candidates:
        raise ValueError(f"未找到场景文件: {scenario_id}.md in {root}")
    fixture_path = candidates[0]

    text = fixture_path.read_text(encoding="utf-8")

    # 跳过 HTML 注释块（L3 文件头部注释）
    if text.startswith("<!--"):
        end_comment = text.find("-->")
        if end_comment != -1:
            text = text[end_comment + 3:].lstrip("\n")

    meta, body = _extract_frontmatter(text)

    draft_id = (
        f"FIXTURE-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        f"-{uuid.uuid4().hex[:4].upper()}"
    )
    subject = meta.get("title", scenario_id)

    # 推断所属校验器
    parts = scenario_id.split("-")
    evaluator = parts[1] if len(parts) >= 2 else "???"

    # ED3 场景需要注入模拟冲突
    conflicts: list[dict] = []
    if evaluator == "ED3":
        conflicts = _ED3_MOCK_CONFLICTS

    draft_dict: dict = {
        "draft_id": draft_id,
        "content_md": body,
        "citations": [],
        "conflicts": conflicts,
        "request": {"subject": subject},
    }

    # ---- 评估 ----
    from harnetics.evaluators import build_default_bus
    bus = build_default_bus()
    raw_results = bus.run_all(draft_dict)
    has_blocking = bus.has_blocking_failures(raw_results)

    def _level(r) -> str:
        from harnetics.evaluators.base import EvalStatus, EvalLevel
        if r.status in (EvalStatus.PASS, EvalStatus.SKIP):
            return "Pass"
        return "Blocker" if r.level == EvalLevel.BLOCK else "Warning"

    eval_results = [
        {
            "evaluator_id": r.evaluator_id,
            "name": r.name,
            "status": r.status.value,
            "level": _level(r),
            "detail": r.detail,
            "locations": r.locations,
        }
        for r in raw_results
    ]

    outcome = "blocked" if has_blocking else "pass"

    # ---- 写进化信号 ----
    try:
        from harnetics.engine.evolution.signals import write_draft_signal
        write_draft_signal(
            draft_id=draft_id,
            subject=f"[fixture:{scenario_id}] {subject}",
            eval_results=eval_results,
            has_blocking=has_blocking,
            sections_used=0,
            icd_params_used=0,
        )
    except Exception as exc:
        logger.debug("fixture.signal.write_failed scenario_id=%s error=%s", scenario_id, exc)

    # 推断预期结果
    m = _EXPECTED_PATTERN.search(scenario_id)
    keyword = m.group(1).upper() if m else "PASS"
    expected = _OUTCOME_MAP.get(keyword, "pass")
    # warn 场景：has_blocking=False 且有 Warning → outcome="pass"，按约定 pass == warn 通过
    expected_blocked = expected == "fail"
    match = (has_blocking == expected_blocked) or (expected == "warn" and not has_blocking)

    logger.info(
        "fixture.run scenario_id=%s outcome=%s expected=%s match=%s",
        scenario_id, outcome, expected, match,
    )

    return FixtureRunResult(
        scenario_id=scenario_id,
        draft_id=draft_id,
        outcome=outcome,
        expected_outcome=expected,
        match=match,
        eval_results=eval_results,
    )
