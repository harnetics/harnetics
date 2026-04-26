"""
# [INPUT]: 依赖 pathlib, json, shutil；读取 memory/signals/draft-signals.jsonl
# [OUTPUT]: 对外提供 router: GET /api/evolution/stats
# [POS]: api/routes 的进化统计端点，为前端 Evolution 页面提供信号历史与策略状态
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""
from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/api/evolution", tags=["evolution"])

_SIGNAL_FILE = Path("memory") / "signals" / "draft-signals.jsonl"
_STRATEGY_LABELS = {
    "innovate": "探索创新",
    "balanced": "均衡演化",
    "harden": "稳固优先",
    "repair-only": "紧急修复",
}


def _load_signals() -> list[dict]:
    if not _SIGNAL_FILE.exists():
        return []
    try:
        lines = _SIGNAL_FILE.read_text(encoding="utf-8").splitlines()
        result: list[dict] = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return result
    except Exception:
        return []


def _derive_strategy(signals: list[dict]) -> str:
    recent = signals[-20:]
    if not recent:
        return "balanced"
    blocked = sum(1 for s in recent if s.get("outcome") == "blocked")
    ratio = blocked / len(recent)
    if ratio >= 0.6:
        return "repair-only"
    if ratio >= 0.3:
        return "harden"
    if ratio == 0.0:
        return "innovate"
    return "balanced"


@router.get("/stats")
def evolution_stats() -> dict:
    """返回本地进化记忆的统计摘要，供前端进化视图渲染。"""
    signals = _load_signals()
    total = len(signals)
    recent_20 = signals[-20:]

    # 策略
    current_strategy = _derive_strategy(signals)
    blocked_in_recent = sum(1 for s in recent_20 if s.get("outcome") == "blocked")
    blocked_ratio = round(blocked_in_recent / len(recent_20), 3) if recent_20 else 0.0

    # 标签分布（全量）
    tag_counter: Counter[str] = Counter()
    for s in signals:
        for t in s.get("tags", []):
            tag_counter[t] += 1

    # 失败检查器分布（全量）
    check_counter: Counter[str] = Counter()
    for s in signals:
        for fc in s.get("failed_checks", []):
            # "evaluator_id: detail..." → 只取前缀
            key = fc.split(":")[0].strip() if ":" in fc else fc[:40]
            check_counter[key] += 1

    # 近 20 条简化列表（前端时间轴）
    recent_items = []
    for s in reversed(recent_20):
        recent_items.append(
            {
                "timestamp": s.get("timestamp", ""),
                "draft_id": s.get("draft_id", ""),
                "subject": s.get("subject", ""),
                "outcome": s.get("outcome", "pass"),
                "tags": s.get("tags", []),
                "eval_summary": s.get("eval_summary", {}),
                "context_quality": s.get("context_quality", {}),
                "failed_checks": s.get("failed_checks", []),
            }
        )

    return {
        "total_signals": total,
        "current_strategy": current_strategy,
        "strategy_label": _STRATEGY_LABELS.get(current_strategy, current_strategy),
        "blocked_ratio": blocked_ratio,
        "evolver_installed": shutil.which("evolver") is not None,
        "recent": recent_items,
        "tag_counts": dict(tag_counter.most_common()),
        "check_failure_counts": dict(check_counter.most_common(10)),
    }
