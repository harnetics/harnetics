# [INPUT]: 依赖 httpx 与 Settings 中的本地 LLM 配置
# [OUTPUT]: 对外提供 OpenAI-compatible 本地模型客户端
# [POS]: harnetics 与本地 LLM 服务之间的最小适配层
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

import httpx


class LocalLlmClient:
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
