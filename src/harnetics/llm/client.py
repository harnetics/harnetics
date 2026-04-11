# [INPUT]: 依赖 os、litellm、httpx
# [OUTPUT]: 对外提供 HarneticsLLM 与旧版 LocalLlmClient 后向/兼容
# [POS]: llm 包的模型调用适配层，统一本地 Ollama 与 OpenAI-compatible 提供方接入
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

import os
from typing import Any

import httpx


DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"


class LocalLlmClient:
    """旧版客户端，保留后向兼容。"""
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate_markdown(self, *, prompt: str) -> str:
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"]


class HarneticsLLM:
    """litellm 封装的主 LLM 客户端，用于草稿生成。"""

    def __init__(
        self,
        model: str = "gemma4:26b",
        api_base: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.model = _normalize_model(model, api_base)
        self.api_base = _normalize_api_base(
            self.model,
            api_base or _default_api_base(self.model),
        )
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

    def generate_draft(self, system_prompt: str, context: str, user_request: str) -> str:
        """调用 LLM 生成草稿 Markdown。"""
        import litellm  # 延迟导入，避免冷启动时加载

        request_kwargs: dict[str, Any] = {}
        if self.api_base:
            request_kwargs["api_base"] = self.api_base
        if self.api_key:
            request_kwargs["api_key"] = self.api_key

        try:
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"## 参考文档\n\n{context}\n\n## 任务\n\n{user_request}"},
                ],
                temperature=0.3,
                max_tokens=8192,
                top_p=0.9,
                timeout=60.0,
                **request_kwargs,
            )
        except Exception as exc:
            raise RuntimeError(
                "LLM generation failed for "
                f"model={self.model} api_base={self.api_base or '<default>'}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc
        return response.choices[0].message.content  # type: ignore[union-attr]

    def check_availability(self) -> bool:
        """返回当前 LLM 是否可用或已完成最小配置。"""
        try:
            if _is_ollama_model(self.model):
                base_url = _normalize_api_base(self.model, self.api_base) or DEFAULT_OLLAMA_BASE_URL
                resp = httpx.get(f"{base_url}/api/tags", timeout=2.0)
                if resp.status_code != 200:
                    return False
                try:
                    return _ollama_model_available(resp.json(), self.model)
                except Exception:
                    return False
            # 云端 / OpenAI-compatible: 这里不强依赖外网探活，凭证存在即可视为可调用。
            return bool(self.api_key)
        except Exception:
            return False


def _default_api_base(model: str) -> str | None:
    custom_base = os.environ.get("HARNETICS_LLM_BASE_URL")
    if custom_base:
        return custom_base.rstrip("/")

    openai_base = os.environ.get("OPENAI_BASE_URL")
    if openai_base:
        return openai_base.rstrip("/")

    if _is_ollama_model(_normalize_model(model, None)):
        return DEFAULT_OLLAMA_BASE_URL
    return None


def _normalize_model(model: str, api_base: str | None) -> str:
    normalized = model.strip()
    if not normalized:
        return normalized
    if "/" in normalized:
        return normalized
    if _looks_like_ollama_base(api_base) or ":" in normalized:
        return f"ollama/{normalized}"
    return normalized


def _normalize_api_base(model: str, api_base: str | None) -> str | None:
    if not api_base:
        return None
    normalized = api_base.rstrip("/")
    if _is_ollama_model(model) and normalized.endswith("/v1"):
        normalized = normalized[:-3].rstrip("/")
    return normalized


def _is_ollama_model(model: str) -> bool:
    return model.startswith("ollama/")


def _looks_like_ollama_base(api_base: str | None) -> bool:
    if not api_base:
        return False
    normalized = api_base.rstrip("/")
    if normalized.endswith("/v1"):
        normalized = normalized[:-3].rstrip("/")
    return normalized.endswith(":11434") or ":11434/" in normalized


def _ollama_model_available(payload: dict[str, Any], model: str) -> bool:
    requested = model.removeprefix("ollama/")
    names = [str(item.get("name", "")).strip() for item in payload.get("models", [])]
    if not requested:
        return bool(names)
    if ":" in requested:
        return any(name == requested or name.startswith(f"{requested}-") for name in names)
    return any(name == requested or name.startswith(f"{requested}:") or name.startswith(f"{requested}-") for name in names)

