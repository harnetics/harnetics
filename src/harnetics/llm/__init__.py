# [INPUT]: 聚合 llm 子模块的公共接口
# [OUTPUT]: 对外提供 LocalLlmClient（保持与旧 llm.py 相同的导入路径）
# [POS]: llm 包入口，向后兼容 `from harnetics.llm import LocalLlmClient`
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from .client import LocalLlmClient

__all__ = ["LocalLlmClient"]
