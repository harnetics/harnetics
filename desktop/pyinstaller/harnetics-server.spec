# -*- mode: python ; coding: utf-8 -*-
#
# [INPUT]: 依赖 PyInstaller、src/harnetics 包、frontend/dist 静态资源
# [OUTPUT]: 生成 harnetics-server 后端 sidecar 可执行文件
# [POS]: desktop/pyinstaller 的唯一构建规格，供本地与 CI 桌面打包复用
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path.cwd().resolve()

datas = collect_data_files("harnetics")
frontend_dist = ROOT / "frontend" / "dist"
if frontend_dist.exists():
    datas.append((str(frontend_dist), "frontend/dist"))

hiddenimports = [
    "harnetics.cli.main",
    "uvicorn.logging",
    *collect_submodules("harnetics"),
]

a = Analysis(
    [str(ROOT / "src" / "harnetics" / "cli" / "main.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="harnetics-server",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
