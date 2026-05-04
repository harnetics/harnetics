# [INPUT]: 依赖 pytest、unittest.mock 与 harnetics.llm.client.HarneticsLLM/LocalLlmClient
# [OUTPUT]: 提供模型归一化、Ollama availability 判定、OpenAI-compatible 原生调用与请求超时的回归测试
# [POS]: tests 目录中的 LLM 配置契约测试，锁定本地 Ollama 裸模型名、原始模型透传、模型存在性判断与错误脱敏行为
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from unittest.mock import Mock, patch
from pathlib import Path

from harnetics.llm.client import HarneticsLLM, LocalLlmClient


def _isolate_settings(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("harnetics.config._PROJECT_ROOT", tmp_path)
    monkeypatch.delenv("HARNETICS_ENV_FILE", raising=False)
    monkeypatch.delenv("HARNETICS_LLM_TIMEOUT_SECONDS", raising=False)


def test_chat_completion_uses_configured_timeout(monkeypatch) -> None:
    monkeypatch.setenv("HARNETICS_LLM_TIMEOUT_SECONDS", "42.5")
    llm = HarneticsLLM(
        model="claude-sonnet-4-6-think",
        api_base="https://aihubmix.com/v1",
        api_key="sk-test",
    )

    with patch("harnetics.llm.client.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.return_value.choices = [
            Mock(message=Mock(content="ok"))
        ]

        assert llm.generate_draft("system", "context", "request") == "ok"

    assert MockOpenAI.call_args.kwargs["timeout"] == 42.5


def test_ollama_model_name_is_normalized_from_bare_tag() -> None:
    llm = HarneticsLLM(model="gemma4:26b", api_base="http://localhost:11434/v1")

    assert llm.model == "ollama/gemma4:26b"
    assert llm.api_base == "http://localhost:11434"


def test_check_availability_requires_requested_ollama_model() -> None:
    with patch("harnetics.llm.client.httpx.get") as mock_get:
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "models": [
                {"name": "gemma4:26b"},
                {"name": "qwen2.5:7b"},
            ]
        }
        mock_get.return_value = response

        assert HarneticsLLM(model="gemma4:26b", api_base="http://localhost:11434").check_availability() is True
        assert HarneticsLLM(model="llama3:8b", api_base="http://localhost:11434").check_availability() is False


def test_cloud_availability_reports_missing_api_key() -> None:
    ok, error = HarneticsLLM(
        model="deepseek/deepseek-chat",
        api_base="https://api.deepseek.com/v1",
        api_key="",
    ).availability_status()

    assert ok is False
    assert error == "missing api key"


def test_cloud_availability_reports_provider_probe_failure() -> None:
    with patch("harnetics.llm.client.httpx.get") as mock_get:
        response = Mock()
        response.status_code = 401
        mock_get.return_value = response

        ok, error = HarneticsLLM(
            model="openai/gpt-4.1-mini",
            api_key="sk-test",
        ).availability_status()

    assert ok is False
    assert "401" in error


def test_bare_remote_model_is_normalized_for_openai_compatible_gateway() -> None:
    llm = HarneticsLLM(
        model="claude-sonnet-4-6",
        api_base="https://aihubmix.com/v1",
        api_key="sk-test",
    )

    assert llm.model == "openai/claude-sonnet-4-6"
    assert llm.api_base == "https://aihubmix.com/v1"


def test_default_constructor_uses_current_settings_for_remote_gateway(monkeypatch) -> None:
    monkeypatch.setenv("HARNETICS_LLM_MODEL", "claude-sonnet-4-6")
    monkeypatch.setenv("HARNETICS_LLM_BASE_URL", "https://aihubmix.com/v1")
    monkeypatch.setenv("HARNETICS_LLM_API_KEY", "sk-harnetics")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    llm = HarneticsLLM()

    assert llm.requested_model == "claude-sonnet-4-6"
    assert llm.model == "openai/claude-sonnet-4-6"
    assert llm.api_base == "https://aihubmix.com/v1"
    assert llm.api_key == "sk-harnetics"


def test_generate_draft_uses_openai_client_with_raw_model_name(tmp_path: Path, monkeypatch) -> None:
    _isolate_settings(tmp_path, monkeypatch)
    llm = HarneticsLLM(
        model="claude-sonnet-4-6-think",
        api_base="https://aihubmix.com/v1",
        api_key="sk-test",
    )

    with patch("harnetics.llm.client.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.return_value.choices = [
            Mock(message=Mock(content="ok"))
        ]

        assert llm.generate_draft("system", "context", "request") == "ok"

    MockOpenAI.assert_called_once_with(
        base_url="https://aihubmix.com/v1",
        api_key="sk-test",
        timeout=180.0,
    )
    MockOpenAI.return_value.chat.completions.create.assert_called_once()
    kwargs = MockOpenAI.return_value.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "claude-sonnet-4-6-think"
    assert kwargs["messages"][0]["role"] == "system"
    assert "top_p" not in kwargs
    assert "enable_thinking" not in kwargs


def test_generate_draft_sends_enable_thinking_when_model_supports_it(tmp_path: Path, monkeypatch) -> None:
    _isolate_settings(tmp_path, monkeypatch)
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "HARNETICS_LLM_THINKING_SUPPORTED=true",
                "HARNETICS_LLM_ENABLE_THINKING=false",
            ]
        ),
        encoding="utf-8",
    )
    llm = HarneticsLLM(
        model="deepseek-ai/DeepSeek-V3.2",
        api_base="https://api.siliconflow.cn/v1",
        api_key="sk-test",
    )

    with patch("harnetics.llm.client.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.return_value.choices = [
            Mock(message=Mock(content="ok"))
        ]

        assert llm.generate_draft("system", "context", "request") == "ok"

    kwargs = MockOpenAI.return_value.chat.completions.create.call_args.kwargs
    assert "enable_thinking" not in kwargs
    assert kwargs["extra_body"] == {"enable_thinking": False}


def test_generate_draft_error_masks_api_key() -> None:
    llm = HarneticsLLM(
        model="claude-sonnet-4-6",
        api_base="https://aihubmix.com/v1",
        api_key="sk-secret-123",
    )

    with patch("harnetics.llm.client.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.side_effect = RuntimeError(
            "bad request for sk-secret-123"
        )

        with patch("builtins.print"):
            try:
                llm.generate_draft("system", "context", "request")
            except RuntimeError as exc:
                message = str(exc)
            else:
                raise AssertionError("expected RuntimeError")

    assert "sk-secret-123" not in message
    assert "[REDACTED]" in message
    assert "openai/claude-sonnet-4-6" in message


def test_local_client_uses_ollama_openai_compatible_endpoint(tmp_path: Path, monkeypatch) -> None:
    _isolate_settings(tmp_path, monkeypatch)
    client = LocalLlmClient(
        base_url="http://localhost:11434",
        model="gemma4:26b",
    )

    with patch("harnetics.llm.client.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.chat.completions.create.return_value.choices = [
            Mock(message=Mock(content="ok"))
        ]

        assert client.generate_markdown(prompt="hello") == "ok"

    MockOpenAI.assert_called_once_with(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        timeout=180.0,
    )
    kwargs = MockOpenAI.return_value.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "gemma4:26b"
