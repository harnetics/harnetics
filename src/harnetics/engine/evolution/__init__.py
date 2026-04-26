"""
# [INPUT]: 依赖 engine/evolution/signals 与 engine/evolution/runner
# [OUTPUT]: 对外提供 write_draft_signal() 与 get_evolution_context()
# [POS]: engine 包的自进化子模块入口，封装 GEP 信号写入与 evolver CLI 调用
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""
from .runner import get_evolution_context
from .signals import write_draft_signal

__all__ = ["get_evolution_context", "write_draft_signal"]
