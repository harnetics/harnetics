# [INPUT]: 依赖 os、httpx、config.get_settings 与 openai SDK
# [OUTPUT]: 对外提供 HarneticsLLM 与旧版 LocalLlmClient 后向/兼容；HarneticsLLM 支持 explainable availability status、有限超时与 OpenAI-compatible 原生调用
# [POS]: llm 包的模型调用适配层，统一本地显式路径与 OpenAI-compatible 提供方接入
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

import logging
import os
import re

import httpx
from openai import OpenAI


DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
_API_KEY_RE = re.compile(r"sk-[A-Za-z0-9_-]+")
logger = logging.getLogger("uvicorn.error")


class LocalLlmClient:
    """旧版草稿服务兼容层，统一走 OpenAI-compatible 会话接口。"""

    def __init__(self, base_url: str, model: str, api_key: str | None = None) -> None:
        self.configured_model = model.strip()
        self.requested_model = _request_model_name(self.configured_model)
        self.model = _normalize_model(self.requested_model, base_url)
        self.api_base = _normalize_api_base(self.model, base_url)
        self.request_api_base = _request_api_base(self.model, self.api_base)
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

    def generate_markdown(self, *, prompt: str) -> str:
        try:
            return _create_chat_completion(
                request_model=self.requested_model,
                request_api_base=self.request_api_base,
                api_key=_request_api_key(self.api_key, self.model),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=8192,  # LocalLlmClient 兼容层，固定值
            )
        except Exception as exc:
            raise RuntimeError(
                _format_generation_error(
                    effective_model=self.model,
                    effective_base_url=self.api_base,
                    api_key=self.api_key,
                    exc=exc,
                )
            ) from exc


class HarneticsLLM:
    """主 LLM 客户端，用于草稿生成与影响分析 AI 判定。"""

    def __init__(
        self,
        model: str | None = None,
        api_base: str | None = None,
        api_key: str | None = None,
    ) -> None:
        resolved_model = model
        resolved_api_base = api_base
        resolved_api_key = api_key

        if resolved_model is None:
            from harnetics.config import get_settings

            settings = get_settings()
            resolved_model = settings.llm_model
            if resolved_api_base is None:
                resolved_api_base = settings.llm_base_url
            if resolved_api_key is None and settings.llm_api_key:
                resolved_api_key = settings.llm_api_key

        configured_model = (resolved_model or "").strip()
        requested_model = _request_model_name(configured_model)
        raw_api_base = resolved_api_base or _default_api_base(configured_model)

        self.configured_model = configured_model
        self.requested_model = requested_model
        self.model = _normalize_model(requested_model, raw_api_base)
        self.api_base = _normalize_api_base(
            self.model,
            raw_api_base,
        )
        self.request_api_base = _request_api_base(self.model, self.api_base)
        self.api_key = resolved_api_key or os.environ.get("OPENAI_API_KEY")

    def _max_tokens(self) -> int:
        try:
            from harnetics.config import get_settings
            return get_settings().llm_max_tokens
        except Exception:
            return 16384

    def generate_draft(
        self,
        system_prompt: str,
        context: str,
        user_request: str,
        *,
        max_tokens: int | None = None,
    ) -> str:
        """调用 OpenAI-compatible 会话接口生成草稿 Markdown。"""
        if not _is_ollama_model(self.model) and not self.api_key:
            logger.warning(
                "llm.generate.missing_api_key effective_model=%s api_base=%s configured_model=%s",
                self.model,
                self.api_base or "<default>",
                self.configured_model or "<empty>",
            )
            raise RuntimeError(
                f"LLM generation failed for model={self.model} api_base={self.api_base or '<default>'}: missing api key"
            )
        try:
            return _create_chat_completion(
                request_model=self.requested_model,
                request_api_base=self.request_api_base,
                api_key=_request_api_key(self.api_key, self.model),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"## 参考文档\n\n{context}\n\n## 任务\n\n{user_request}"},
                ],
                temperature=0.3,
                max_tokens=max_tokens or self._max_tokens(),
            )
        except Exception as exc:
            raise RuntimeError(
                _format_generation_error(
                    effective_model=self.model,
                    effective_base_url=self.api_base,
                    api_key=self.api_key,
                    exc=exc,
                )
            ) from exc

    def check_availability(self) -> bool:
        """返回当前 LLM 是否可用或已完成最小配置。"""
        return self.availability_status()[0]

    def availability_status(self) -> tuple[bool, str]:
        """返回可用性与失败原因，供状态端点展示。"""
        try:
            if _is_ollama_model(self.model):
                base_url = _normalize_api_base(self.model, self.api_base) or DEFAULT_OLLAMA_BASE_URL
                resp = httpx.get(f"{base_url}/api/tags", timeout=2.0)
                if resp.status_code != 200:
                    return False, f"ollama probe returned {resp.status_code}"
                try:
                    if _ollama_model_available(resp.json(), self.model):
                        return True, ""
                    return False, f"ollama model not found: {self.model.removeprefix('ollama/')}"
                except Exception as exc:
                    return False, f"invalid ollama payload: {type(exc).__name__}"

            if not self.api_key:
                return False, "missing api key"

            probe_base = self.api_base or _default_cloud_probe_base(self.model)
            if not probe_base:
                return True, ""

            resp = httpx.get(
                f"{probe_base.rstrip('/')}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=2.0,
            )
            if resp.status_code == 200:
                return True, ""
            return False, f"provider probe returned {resp.status_code}"
        except Exception as exc:
            return False, f"{type(exc).__name__}: {exc}"


def _default_api_base(model: str) -> str | None:
    custom_base = os.environ.get("HARNETICS_LLM_BASE_URL")
    if custom_base:
        return custom_base.rstrip("/")

    openai_base = os.environ.get("OPENAI_BASE_URL")
    if openai_base:
        return openai_base.rstrip("/")

    normalized_model = _normalize_model(model, None)
    if _is_ollama_model(normalized_model):
        return DEFAULT_OLLAMA_BASE_URL
    default_cloud = _default_cloud_probe_base(normalized_model)
    if default_cloud:
        return default_cloud
    return None


def _default_cloud_probe_base(model: str) -> str | None:
    if model.startswith("openai/"):
        return "https://api.openai.com/v1"
    if model.startswith("deepseek/"):
        return "https://api.deepseek.com/v1"
    return None


def _create_chat_completion(
    *,
    request_model: str,
    request_api_base: str | None,
    api_key: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> str:
    if not request_api_base:
        raise RuntimeError("missing api_base")
    from harnetics.config import get_settings

    timeout_seconds = get_settings().llm_timeout_seconds

    logger.info(
        "llm.chat.start model=%s api_base=%s messages=%d max_tokens=%d temperature=%.2f",
        request_model,
        request_api_base,
        len(messages),
        max_tokens,
        temperature,
    )

    client = OpenAI(
        base_url=request_api_base,
        api_key=api_key,
        timeout=timeout_seconds,
    )
    try:
        response = client.chat.completions.create(
            model=request_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as exc:
        logger.error(
            "llm.chat.failed model=%s api_base=%s error_type=%s error=%s",
            request_model,
            request_api_base,
            type(exc).__name__,
            _sanitize_error_message(str(exc), api_key),
        )
        raise

    content = response.choices[0].message.content
    logger.info(
        "llm.chat.success model=%s finish_reason=%s content_chars=%d",
        request_model,
        getattr(response.choices[0], "finish_reason", ""),
        len(content or ""),
    )
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    return str(content)


def _format_generation_error(
    *,
    effective_model: str,
    effective_base_url: str | None,
    api_key: str | None,
    exc: Exception,
) -> str:
    return (
        "LLM generation failed for "
        f"model={effective_model} api_base={effective_base_url or '<default>'}: "
        f"{type(exc).__name__}: {_sanitize_error_message(str(exc), api_key)}"
    )


def _sanitize_error_message(message: str, api_key: str | None) -> str:
    sanitized = message
    if api_key:
        sanitized = sanitized.replace(api_key, "[REDACTED]")
    return _API_KEY_RE.sub("[REDACTED]", sanitized)


def _request_api_key(api_key: str | None, effective_model: str) -> str:
    if api_key:
        return api_key
    if _is_ollama_model(effective_model):
        return "ollama"
    raise RuntimeError("missing api key")


# openai/、ollama/ 等路由前缀应被剥离；HuggingFace 风格的 Org/Model（如 Qwen/Qwen3-...）应原样传递
_PROVIDER_PREFIXES = frozenset(("openai", "ollama", "anthropic", "deepseek", "azure"))


def _request_model_name(model: str) -> str:
    normalized = model.strip()
    if not normalized:
        return normalized
    if "/" in normalized:
        provider, rest = normalized.split("/", 1)
        if provider.lower() in _PROVIDER_PREFIXES:
            return rest
    return normalized


def _request_api_base(model: str, api_base: str | None) -> str | None:
    normalized = _normalize_api_base(model, api_base)
    if not normalized:
        return None
    if _is_ollama_model(model) and not normalized.endswith("/v1"):
        return f"{normalized}/v1"
    return normalized


def _normalize_model(model: str, api_base: str | None) -> str:
    normalized = model.strip()
    if not normalized:
        return normalized
    if "/" in normalized:
        return normalized
    if _looks_like_ollama_base(api_base) or ":" in normalized:
        return f"ollama/{normalized}"
    if _looks_like_openai_compatible_base(api_base):
        return f"openai/{normalized}"
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


def _looks_like_openai_compatible_base(api_base: str | None) -> bool:
    if not api_base:
        return False
    return not _looks_like_ollama_base(api_base)


def _ollama_model_available(payload: dict[str, Any], model: str) -> bool:
    requested = model.removeprefix("ollama/")
    names = [str(item.get("name", "")).strip() for item in payload.get("models", [])]
    if not requested:
        return bool(names)
    if ":" in requested:
        return any(name == requested or name.startswith(f"{requested}-") for name in names)
    return any(name == requested or name.startswith(f"{requested}:") or name.startswith(f"{requested}-") for name in names)
