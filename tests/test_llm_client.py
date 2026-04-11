# [INPUT]: 依赖 pytest、unittest.mock 与 harnetics.llm.client.HarneticsLLM
# [OUTPUT]: 提供模型归一化与 Ollama availability 判定的回归测试
# [POS]: tests 目录中的 LLM 配置契约测试，锁定本地 Ollama 裸模型名与模型存在性判断
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

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