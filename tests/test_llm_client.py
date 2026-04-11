# [INPUT]: 依赖 pytest、unittest.mock 与 harnetics.llm.client.HarneticsLLM
# [OUTPUT]: 提供模型归一化、Ollama availability 判定与 LiteLLM debug 开关的回归测试
# [POS]: tests 目录中的 LLM 配置契约测试，锁定本地 Ollama 裸模型名、模型存在性判断与可控 debug 行为
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

from harnetics.llm.client import HarneticsLLM


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


def test_generate_draft_enables_litellm_debug_once_when_requested(monkeypatch) -> None:
    class FakeLiteLLM:
        def __init__(self) -> None:
            self.debug_calls = 0
            self._harnetics_debug_enabled = False

        def _turn_on_debug(self) -> None:
            self.debug_calls += 1

        def completion(self, **_: object):
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))]
            )

    fake_litellm = FakeLiteLLM()
    monkeypatch.setenv("HARNETICS_LITELLM_DEBUG", "1")
    monkeypatch.setitem(sys.modules, "litellm", fake_litellm)

    llm = HarneticsLLM(
        model="openai/gpt-4.1-mini",
        api_base="https://example.com/v1",
        api_key="sk-test",
    )

    assert llm.generate_draft("system", "", "request") == "ok"
    assert llm.generate_draft("system", "", "request") == "ok"
    assert fake_litellm.debug_calls == 1