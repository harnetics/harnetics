# [INPUT]: 依赖 json、pathlib 与 desktop/src-tauri/tauri.conf.json
# [OUTPUT]: 提供桌面 Tauri 配置契约测试，锁定首次启动窗口可见性与 DMG 布局
# [POS]: tests 的桌面打包配置回归测试，防止安装包视觉与启动竞态配置退化
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESKTOP_PACKAGE = ROOT / "desktop" / "package.json"
DMG_POSTPROCESS = ROOT / "desktop" / "scripts" / "fix-macos-dmg.mjs"
TAURI_CONFIG = ROOT / "desktop" / "src-tauri" / "tauri.conf.json"


def _tauri_config() -> dict:
    return json.loads(TAURI_CONFIG.read_text(encoding="utf-8"))


def test_main_window_stays_hidden_until_backend_is_ready() -> None:
    window = _tauri_config()["app"]["windows"][0]

    assert window["visible"] is False


def test_macos_dmg_uses_fixed_installer_layout() -> None:
    dmg = _tauri_config()["bundle"]["macOS"]["dmg"]

    assert dmg["windowSize"] == {"width": 660, "height": 420}
    assert dmg["appPosition"] == {"x": 180, "y": 190}
    assert dmg["applicationFolderPosition"] == {"x": 480, "y": 190}


def test_desktop_build_postprocesses_macos_dmg_volume_icon() -> None:
    package = json.loads(DESKTOP_PACKAGE.read_text(encoding="utf-8"))

    assert "node scripts/fix-macos-dmg.mjs" in package["scripts"]["build"]

    script = DMG_POSTPROCESS.read_text(encoding="utf-8")
    assert ".VolumeIcon.icns" in script
    assert "SetFile" in script
    assert "chflags" in script
