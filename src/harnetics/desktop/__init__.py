"""
# [INPUT]: 依赖 harnetics.desktop.paths 的桌面运行时路径模型
# [OUTPUT]: 对外提供 DesktopRuntimePaths 与 build_sidecar_environment
# [POS]: desktop 包入口，暴露桌面 sidecar 启动前的 Python 运行时路径契约
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""

from harnetics.desktop.paths import DesktopRuntimePaths, build_sidecar_environment

__all__ = ["DesktopRuntimePaths", "build_sidecar_environment"]
