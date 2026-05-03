# [INPUT]: 依赖 fastapi.testclient、harnetics.api.app 的 create_api_app、harnetics.config
# [OUTPUT]: 提供 API app 冒烟测试——healthcheck、settings、dotenv 加载、云端默认模型、可调推理边界、dashboard 缓存
# [POS]: tests 目录中的应用骨架测试，验证 API app factory 行为
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from pathlib import Path

from fastapi.testclient import TestClient

from harnetics.api.app import create_api_app
from harnetics.config import Settings, get_dotenv_path, get_settings


def test_healthcheck_returns_ok() -> None:
    client = TestClient(create_api_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_settings_loads_dotenv(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("HARNETICS_LLM_MODEL", raising=False)
    monkeypatch.delenv("HARNETICS_LLM_API_KEY", raising=False)
    monkeypatch.delenv("HARNETICS_EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("HARNETICS_EMBEDDING_API_KEY", raising=False)
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "HARNETICS_LLM_MODEL=deepseek/deepseek-chat",
                "HARNETICS_LLM_API_KEY=sk-llm",
                "HARNETICS_EMBEDDING_MODEL=text-embedding-3-small",
                "HARNETICS_EMBEDDING_API_KEY=sk-emb",
            ]
        ),
        encoding="utf-8",
    )

    settings = get_settings()

    assert settings.llm_model == "deepseek/deepseek-chat"
    assert settings.llm_api_key == "sk-llm"
    assert settings.embedding_model == "text-embedding-3-small"
    assert settings.embedding_api_key == "sk-emb"


def test_get_settings_defaults_to_cloud_llm_and_embedding(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("harnetics.config._PROJECT_ROOT", tmp_path)
    for name in (
        "HARNETICS_LLM_MODEL",
        "HARNETICS_LLM_BASE_URL",
        "HARNETICS_LLM_API_KEY",
        "HARNETICS_EMBEDDING_MODEL",
        "HARNETICS_EMBEDDING_BASE_URL",
        "HARNETICS_EMBEDDING_API_KEY",
        "HARNETICS_LLM_TIMEOUT_SECONDS",
        "HARNETICS_LLM_MAX_TOKENS",
        "HARNETICS_LLM_THINKING_SUPPORTED",
        "HARNETICS_LLM_ENABLE_THINKING",
        "HARNETICS_COMPARISON_4STEP_BATCH_SIZE",
        "HARNETICS_COMPARISON_STEP1_MAX_TOKENS",
        "HARNETICS_COMPARISON_STEP4_MAX_TOKENS",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = get_settings()

    assert settings.llm_model == "gpt-4o-mini"
    assert settings.llm_base_url == ""
    assert settings.embedding_model == "text-embedding-3-small"
    assert settings.embedding_base_url == ""
    assert settings.llm_timeout_seconds == 180.0
    assert settings.llm_thinking_supported is False
    assert settings.llm_enable_thinking is False
    assert settings.comparison_4step_batch_size == 10
    assert settings.comparison_step1_max_tokens == 500000
    assert settings.comparison_step4_max_tokens == 500000


def test_get_settings_loads_tunable_reasoning_limits(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "HARNETICS_LLM_TIMEOUT_SECONDS=45.5",
                "HARNETICS_COMPARISON_4STEP_BATCH_SIZE=6",
                "HARNETICS_COMPARISON_STEP1_MAX_TOKENS=4096",
                "HARNETICS_COMPARISON_STEP4_MAX_TOKENS=2048",
            ]
        ),
        encoding="utf-8",
    )

    settings = get_settings()

    assert settings.llm_timeout_seconds == 45.5
    assert settings.comparison_4step_batch_size == 6
    assert settings.comparison_step1_max_tokens == 4096
    assert settings.comparison_step4_max_tokens == 2048


def test_settings_api_updates_advanced_runtime_limits(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HARNETICS_ENV_FILE", str(tmp_path / ".env"))
    client = TestClient(create_api_app())

    response = client.put(
        "/api/settings",
        json={
            "llm_timeout_seconds": "90",
            "llm_max_tokens": "32768",
            "comparison_4step_batch_size": "5",
            "comparison_step1_max_tokens": "12000",
            "comparison_step4_max_tokens": "6000",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["llm_timeout_seconds"] == "90"
    assert data["llm_max_tokens"] == "32768"
    assert data["comparison_4step_batch_size"] == "5"
    assert data["comparison_step1_max_tokens"] == "12000"
    assert data["comparison_step4_max_tokens"] == "6000"

    env_text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "HARNETICS_LLM_TIMEOUT_SECONDS='90'" in env_text
    assert "HARNETICS_COMPARISON_4STEP_BATCH_SIZE='5'" in env_text


def test_settings_api_updates_llm_thinking_flags(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HARNETICS_ENV_FILE", str(tmp_path / ".env"))
    client = TestClient(create_api_app())

    response = client.put(
        "/api/settings",
        json={
            "llm_thinking_supported": "true",
            "llm_enable_thinking": "false",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["llm_thinking_supported"] == "true"
    assert data["llm_enable_thinking"] == "false"

    env_text = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "HARNETICS_LLM_THINKING_SUPPORTED='true'" in env_text
    assert "HARNETICS_LLM_ENABLE_THINKING='false'" in env_text


def test_get_settings_falls_back_to_project_root_dotenv(tmp_path: Path, monkeypatch) -> None:
    nested = tmp_path / "frontend"
    nested.mkdir()
    monkeypatch.chdir(nested)
    monkeypatch.setattr("harnetics.config._PROJECT_ROOT", tmp_path)
    monkeypatch.delenv("HARNETICS_LLM_MODEL", raising=False)
    monkeypatch.delenv("HARNETICS_LLM_API_KEY", raising=False)
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "HARNETICS_LLM_MODEL=claude-sonnet-4-6",
                "HARNETICS_LLM_BASE_URL=https://aihubmix.com/v1",
                "HARNETICS_LLM_API_KEY=sk-root",
            ]
        ),
        encoding="utf-8",
    )

    settings = get_settings()

    assert get_dotenv_path() == tmp_path / ".env"
    assert settings.llm_model == "claude-sonnet-4-6"
    assert settings.llm_base_url == "https://aihubmix.com/v1"
    assert settings.llm_api_key == "sk-root"


def test_dashboard_stats_alias_reuses_cached_llm_status(monkeypatch) -> None:
    app = create_api_app()
    client = TestClient(app)
    calls: list[str] = []

    class FakeLLM:
        def __init__(self, model: str, api_base: str, api_key: str | None) -> None:
            self.model = model
            self.api_base = api_base

        def availability_status(self) -> tuple[bool, str]:
            calls.append("availability")
            return True, ""

    monkeypatch.setattr("harnetics.llm.client.HarneticsLLM", FakeLLM)

    status_res = client.get("/api/status")
    stats_res = client.get("/api/dashboard/stats")

    assert status_res.status_code == 200
    assert stats_res.status_code == 200
    assert status_res.json() == stats_res.json()
    assert calls == ["availability"]
