"""
# [INPUT]: 依赖 pathlib, json, datetime
# [OUTPUT]: 对外提供 write_draft_signal()，将草稿生成结果追加到 memory/signals/ 供 evolver 扫描
# [POS]: evolution 包的信号持久化层；每次草稿生成后调用，形成本地进化记忆
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger("uvicorn.error")

_TZ_CST = timezone(timedelta(hours=8))


def _memory_dir() -> Path:
    """返回 memory/signals/ 路径，相对于进程 cwd（项目根目录）。"""
    return Path("memory") / "signals"


def write_draft_signal(
    *,
    draft_id: str,
    subject: str,
    eval_results: list[dict],
    has_blocking: bool,
    sections_used: int,
    icd_params_used: int,
) -> None:
    """将一次草稿生成结果追加到 memory/signals/draft-signals.jsonl。

    失败时静默忽略，不影响主流程。evolver 扫描此文件时会基于
    tags / outcome 选择对应的 Gene 指导下一次生成。
    """
    try:
        mem_dir = _memory_dir()
        mem_dir.mkdir(parents=True, exist_ok=True)

        status_counts: dict[str, int] = {"Pass": 0, "Warning": 0, "Blocker": 0}
        failed_checks: list[str] = []
        for r in eval_results:
            level = r.get("level", "Pass")
            status_counts[level] = status_counts.get(level, 0) + 1
            if level in ("Warning", "Blocker"):
                detail = str(r.get("detail", ""))[:100]
                failed_checks.append(f"{r.get('evaluator_id', '?')}: {detail}")

        signal = {
            "timestamp": datetime.now(_TZ_CST).isoformat(),
            "type": "draft_generation",
            "draft_id": draft_id,
            "subject": subject,
            "outcome": "blocked" if has_blocking else "pass",
            "eval_summary": status_counts,
            "failed_checks": failed_checks,
            "context_quality": {
                "sections_used": sections_used,
                "icd_params_used": icd_params_used,
            },
            "tags": _derive_tags(has_blocking, failed_checks, sections_used, icd_params_used),
        }

        signal_file = mem_dir / "draft-signals.jsonl"
        with signal_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(signal, ensure_ascii=False) + "\n")

        # 同时写一条人类可读的 log 行，供 evolver 的文本模式扫描
        _append_log(mem_dir.parent / "logs", draft_id, signal)

        logger.debug(
            "evolution.signal.written draft_id=%s outcome=%s tags=%s",
            draft_id, signal["outcome"], signal["tags"],
        )
    except Exception as exc:
        logger.debug("evolution.signal.write_failed error=%s", exc)


# ---- helpers ----

def _derive_tags(
    has_blocking: bool,
    failed: list[str],
    sections_used: int,
    icd_params_used: int,
) -> list[str]:
    tags: list[str] = []
    if has_blocking:
        tags.append("repair")
    if sections_used == 0:
        tags.append("missing-context")
    elif sections_used < 3:
        tags.append("thin-context")
    if icd_params_used == 0:
        tags.append("no-icd")
    if any("citation" in f.lower() for f in failed):
        tags.append("citation-quality")
    if any("icd" in f.lower() or "consistency" in f.lower() for f in failed):
        tags.append("icd-consistency")
    if not has_blocking and not failed:
        tags.append("innovate")
    return tags


def _append_log(log_dir: Path, draft_id: str, signal: dict) -> None:
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        ts = signal["timestamp"]
        outcome = signal["outcome"]
        tags = ",".join(signal.get("tags", []))
        checks = "; ".join(signal.get("failed_checks", [])) or "all-pass"
        line = f"[{ts}] {draft_id} outcome={outcome} tags=[{tags}] checks={checks}\n"
        with (log_dir / "draft-history.log").open("a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
