from __future__ import annotations

import sys
from pathlib import Path

from harnetics.api.app import _resolve_spa_dist_dir


def test_resolve_spa_dist_dir_prefers_explicit_env(monkeypatch, tmp_path):
    explicit = tmp_path / "frontend" / "dist"
    explicit.mkdir(parents=True)
    monkeypatch.setenv("HARNETICS_SPA_DIST_DIR", str(explicit))

    assert _resolve_spa_dist_dir() == explicit


def test_resolve_spa_dist_dir_supports_pyinstaller_meipass(monkeypatch, tmp_path):
    bundled = tmp_path / "frontend" / "dist"
    bundled.mkdir(parents=True)
    monkeypatch.delenv("HARNETICS_SPA_DIST_DIR", raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    assert _resolve_spa_dist_dir() == bundled


def test_resolve_spa_dist_dir_ignores_missing_meipass_and_uses_source_fallback(monkeypatch, tmp_path):
    monkeypatch.delenv("HARNETICS_SPA_DIST_DIR", raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    result = _resolve_spa_dist_dir()

    assert result is not None
    assert result.name == "dist"
    assert result.parent.name == "frontend"
