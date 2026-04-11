# harnetics/llm/
> L2 | 父级: src/harnetics/AGENTS.md

成员清单
__init__.py: 包入口，导出 LocalLlmClient（向后兼容旧 llm.py 路径）。
client.py: LLM 适配层；旧版 LocalLlmClient 兼容 OpenAI-style HTTP，HarneticsLLM 负责 LiteLLM + Ollama/OpenAI-compatible 调用、裸模型名归一化、模型存在性探测、可控 debug 与错误上下文包装。
prompts.py: 草稿生成系统提示词与上下文拼装模板。

法则: provider 差异收口在这里，上层只感知“给上下文，拿草稿”。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
