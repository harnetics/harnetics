# harnetics/llm/
> L2 | 父级: src/harnetics/AGENTS.md

成员清单
__init__.py: 包入口，导出 LocalLlmClient（向后兼容旧 llm.py 路径）。
client.py: LLM 适配层；旧版 LocalLlmClient 与 HarneticsLLM 统一走 OpenAI-compatible 会话接口，同时保留显式 Ollama 兼容路径、裸模型名归一化、有限请求超时、SiliconFlow thinking body 开关、模型存在性探测与错误脱敏。
prompts.py: 草稿生成系统提示词与上下文拼装模板。

法则: provider 差异收口在这里，上层只感知“给上下文，拿草稿”。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
