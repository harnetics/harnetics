# [INPUT]: 依赖 fastapi.testclient、harnetics.api.app.create_api_app 与临时日志目录
# [OUTPUT]: 提供开发者日志 API 契约测试，锁定日志文件发现、tail 行数与空日志语义
# [POS]: tests 的设置/调试域回归测试，保护 Settings 页面开发者模式所消费的 /api/settings/logs
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from pathlib import Path

from fastapi.testclient import TestClient

from harnetics.api.app import create_api_app


def test_settings_logs_returns_tail_from_explicit_log_file(tmp_path: Path, monkeypatch) -> None:
    log_file = tmp_path / "harnetics.log"
    log_file.write_text("line 1\nline 2\nline 3\n", encoding="utf-8")
    monkeypatch.setenv("HARNETICS_LOG_FILE", str(log_file))

    client = TestClient(create_api_app())
    response = client.get("/api/settings/logs?limit=2")

    assert response.status_code == 200
    assert response.json() == {
        "path": str(log_file),
        "lines": ["line 2", "line 3"],
    }


def test_settings_logs_uses_newest_log_in_log_dir(tmp_path: Path, monkeypatch) -> None:
    old_log = tmp_path / "old.log"
    new_log = tmp_path / "new.log"
    old_log.write_text("old\n", encoding="utf-8")
    new_log.write_text("new 1\nnew 2\n", encoding="utf-8")
    monkeypatch.delenv("HARNETICS_LOG_FILE", raising=False)
    monkeypatch.setenv("HARNETICS_LOG_DIR", str(tmp_path))

    client = TestClient(create_api_app())
    response = client.get("/api/settings/logs?limit=20")

    assert response.status_code == 200
    data = response.json()
    assert data["path"] == str(new_log)
    assert data["lines"] == ["new 1", "new 2"]


def test_settings_logs_returns_empty_when_no_log_exists(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("HARNETICS_LOG_FILE", raising=False)
    monkeypatch.setenv("HARNETICS_LOG_DIR", str(tmp_path))

    client = TestClient(create_api_app())
    response = client.get("/api/settings/logs")

    assert response.status_code == 200
    assert response.json() == {"path": "", "lines": []}
