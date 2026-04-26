"""
# [INPUT]: 依赖 subprocess, json, pathlib, memory/signals/draft-signals.jsonl
# [OUTPUT]: 对外提供 get_evolution_context() -> str，返回 evolver GEP 演化提示词
# [POS]: evolution 包的 evolver CLI 调用层；草稿生成前调用，注入演化经验
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""
from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("uvicorn.error")

# evolver 全局安装后的命令名（npm install -g @evomap/evolver）
_EVOLVER_CMD = "evolver"
# 单次 GEP 提示词最大字符数，避免消耗过多 LLM token
_MAX_GEP_CHARS = 1500


def get_evolution_context() -> str:
    """调用 evolver CLI 获取 GEP 演化上下文提示词。

    - evolver 未安装时静默返回空字符串（主流程不受影响）
    - 根据最近 20 条信号自动选择 EVOLVE_STRATEGY
    - evolver stdout 包含 GEP 协议 prompt，截取后注入草稿 system prompt
    """
    strategy = _select_strategy()
    try:
        result = subprocess.run(
            [_EVOLVER_CMD],
            capture_output=True,
            text=True,
            timeout=20,
            cwd=str(Path.cwd()),
            env={**_base_env(), "EVOLVE_STRATEGY": strategy},
        )
        stdout = (result.stdout or "").strip()
        if not stdout:
            return ""
        context = _extract_gep_block(stdout)
        if context:
            logger.info(
                "evolution.context.loaded strategy=%s chars=%d", strategy, len(context)
            )
        return context
    except FileNotFoundError:
        logger.debug(
            "evolution.runner.not_found -- 安装: npm install -g @evomap/evolver"
        )
        return ""
    except subprocess.TimeoutExpired:
        logger.debug("evolution.runner.timeout")
        return ""
    except Exception as exc:
        logger.debug("evolution.runner.failed error=%s", exc)
        return ""


# ---- helpers ----

def _select_strategy() -> str:
    """根据最近信号中的 blocked 比率选择 evolver 策略。"""
    signals = _load_recent_signals(20)
    if not signals:
        return "balanced"
    blocked = sum(1 for s in signals if s.get("outcome") == "blocked")
    ratio = blocked / len(signals)
    if ratio >= 0.6:
        return "repair-only"
    if ratio >= 0.3:
        return "harden"
    if ratio == 0:
        return "innovate"
    return "balanced"


def _load_recent_signals(n: int) -> list[dict]:
    signal_file = Path("memory") / "signals" / "draft-signals.jsonl"
    if not signal_file.exists():
        return []
    try:
        lines = signal_file.read_text(encoding="utf-8").splitlines()
        results: list[dict] = []
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(results) >= n:
                break
        return results
    except Exception:
        return []


def _extract_gep_block(stdout: str) -> str:
    """从 evolver stdout 中提取 GEP 协议内容，丢弃 banner 和状态行。"""
    lines = stdout.splitlines()
    # evolver 输出结构：banner 行（带 🧬 或 ===）+ GEP protocol block
    # GEP block 通常从 "GEP"、"Gene"、"Evolution" 或 "---" 开始
    keywords = ("GEP", "Gene", "Capsule", "Evolution", "---", "##", "EVOLVE")
    start = 0
    for i, line in enumerate(lines):
        if any(kw in line for kw in keywords):
            start = i
            break
    content = "\n".join(lines[start:]).strip()
    return content[:_MAX_GEP_CHARS] if content else ""


def _base_env() -> dict[str, str]:
    """返回当前进程环境，确保 PATH 可以找到全局 npm 安装的命令。"""
    import os
    return dict(os.environ)
