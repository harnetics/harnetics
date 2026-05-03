from __future__ import annotations

from harnetics.desktop.paths import DesktopRuntimePaths, build_sidecar_environment


def test_desktop_runtime_paths_stay_under_app_data(tmp_path):
    paths = DesktopRuntimePaths.from_root(tmp_path / "Harnetics")

    assert paths.root == tmp_path / "Harnetics"
    assert paths.graph_db_path == tmp_path / "Harnetics" / "var" / "harnetics-graph.db"
    assert paths.chroma_dir == tmp_path / "Harnetics" / "var" / "chroma"
    assert paths.uploads_dir == tmp_path / "Harnetics" / "var" / "uploads"
    assert paths.exports_dir == tmp_path / "Harnetics" / "var" / "exports"
    assert paths.logs_dir == tmp_path / "Harnetics" / "logs"
    assert paths.env_file == tmp_path / "Harnetics" / ".env"


def test_ensure_creates_runtime_directories(tmp_path):
    paths = DesktopRuntimePaths.from_root(tmp_path / "Harnetics")

    paths.ensure()

    assert paths.root.is_dir()
    assert paths.graph_db_path.parent.is_dir()
    assert paths.chroma_dir.is_dir()
    assert paths.uploads_dir.is_dir()
    assert paths.exports_dir.is_dir()
    assert paths.logs_dir.is_dir()
    assert paths.env_file.exists()


def test_build_sidecar_environment_exports_runtime_paths(tmp_path):
    paths = DesktopRuntimePaths.from_root(tmp_path / "Harnetics")

    env = build_sidecar_environment(paths, port=49152)

    assert env["HARNETICS_ENV_FILE"] == str(paths.env_file)
    assert env["HARNETICS_GRAPH_DB_PATH"] == str(paths.graph_db_path)
    assert env["HARNETICS_CHROMA_DIR"] == str(paths.chroma_dir)
    assert env["HARNETICS_RAW_UPLOAD_DIR"] == str(paths.uploads_dir)
    assert env["HARNETICS_EXPORT_DIR"] == str(paths.exports_dir)
    assert env["HARNETICS_LOG_DIR"] == str(paths.logs_dir)
    assert env["HARNETICS_SERVER_PORT"] == "49152"
