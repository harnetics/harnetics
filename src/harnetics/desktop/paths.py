"""
# [INPUT]: 依赖 os.environ 与 pathlib.Path 组织桌面用户数据目录
# [OUTPUT]: 对外提供 DesktopRuntimePaths 数据对象与 build_sidecar_environment() 环境变量生成函数
# [POS]: desktop 包的运行时路径真相源，被 Tauri sidecar 启动契约与测试共同约束
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DesktopRuntimePaths:
    """桌面版所有可写路径必须收敛到用户 app data 根目录。"""

    root: Path
    graph_db_path: Path
    chroma_dir: Path
    uploads_dir: Path
    exports_dir: Path
    logs_dir: Path
    env_file: Path

    @classmethod
    def from_root(cls, root: str | Path) -> "DesktopRuntimePaths":
        app_root = Path(root).expanduser().resolve()
        var_dir = app_root / "var"
        return cls(
            root=app_root,
            graph_db_path=var_dir / "harnetics-graph.db",
            chroma_dir=var_dir / "chroma",
            uploads_dir=var_dir / "uploads",
            exports_dir=var_dir / "exports",
            logs_dir=app_root / "logs",
            env_file=app_root / ".env",
        )

    def ensure(self) -> None:
        for path in (self.root, self.graph_db_path.parent, self.chroma_dir, self.uploads_dir, self.exports_dir, self.logs_dir):
            path.mkdir(parents=True, exist_ok=True)
        self.env_file.touch(exist_ok=True)


def build_sidecar_environment(paths: DesktopRuntimePaths, port: int, base: dict[str, str] | None = None) -> dict[str, str]:
    """生成 sidecar 环境变量；调用方可传入现有环境作为基线。"""

    env = dict(os.environ if base is None else base)
    env.update({
        "HARNETICS_ENV_FILE": str(paths.env_file),
        "HARNETICS_GRAPH_DB_PATH": str(paths.graph_db_path),
        "HARNETICS_CHROMA_DIR": str(paths.chroma_dir),
        "HARNETICS_RAW_UPLOAD_DIR": str(paths.uploads_dir),
        "HARNETICS_EXPORT_DIR": str(paths.exports_dir),
        "HARNETICS_LOG_DIR": str(paths.logs_dir),
        "HARNETICS_SERVER_PORT": str(port),
    })
    return env
