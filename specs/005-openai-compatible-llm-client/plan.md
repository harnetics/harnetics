# Implementation Plan: OpenAI-compatible LLM 调用收敛

**Branch**: `005-openai-compatible-llm-client` | **Date**: 2026-04-12 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-openai-compatible-llm-client/spec.md`

## Summary

将远端 AI 调用从 LiteLLM 的 provider/model 专属语义收敛到 OpenAI-compatible 原生接口：对 OpenAI-compatible 网关直接传递原始 completion/embedding 模型名和 `base_url`，草稿生成、影响分析与向量检索复用同源配置；保留显式本地配置路径，并强化状态端点对 effective route 的可观测性。

## Technical Context

**Language/Version**: Python 3.13 (backend) + TypeScript 5.7 (existing frontend untouched)  
**Primary Dependencies**: FastAPI, httpx, openai SDK (新增), python-dotenv, pytest  
**Storage**: SQLite (graph DB) + ChromaDB（向量库继续保留，但云端 embedding 路由切换为 OpenAI-compatible SDK）  
**Testing**: pytest  
**Target Platform**: Linux server / Windows + WSL 开发环境  
**Project Type**: web-service (FastAPI + React SPA)  
**Performance Goals**: 单次 LLM 调用保持 60s 内超时控制；状态端点诊断字段不显著增加响应时延  
**Constraints**: 不泄漏 API key；远端 OpenAI-compatible 网关与本地显式配置都必须可用；影响分析的 section-aware 行为不能因新向量路径退化  
**Scale/Scope**: 覆盖草稿生成、影响分析 AI 判定、云端 embedding 路由与状态诊断 4 条后端 AI 入口；前端仅复用现有状态展示能力

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- 文档同构：PASS。新 feature 目录、`specs/AGENTS.md` 与本地 `AGENTS.md` 已同步建立。
- 最小改动：PASS。当前特性聚焦共享 AI 路由语义与运行时诊断；embedding 调整仅限远端 OpenAI-compatible 路径，不改本地向量能力。
- 可回归：PASS。计划为 `HarneticsLLM`、状态端点与关键 API 工作流增加针对性 pytest 回归。
- 可诊断：PASS。实现必须保留 effective model/base 与配置来源的可观测性，并禁止泄漏 API key。

## Project Structure

### Documentation (this feature)

```text
specs/005-openai-compatible-llm-client/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── api-contracts.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
pyproject.toml                           # 新增 OpenAI SDK 依赖
README.md                               # 更新 OpenAI-compatible 配置说明
.env.example                            # 示例配置切换为 OpenAI-compatible 原始模型名写法
src/harnetics/
├── config.py                           # 稳定 .env 解析与默认 LLM 配置语义
├── graph/
│   └── embeddings.py                   # 云端 embedding 路由切换到 OpenAI-compatible SDK
├── llm/
│   └── client.py                       # 远端调用切换到 OpenAI-compatible 客户端，保留本地显式配置路径
├── api/routes/
│   ├── draft.py                        # 复用 HarneticsLLM，无需新增接口
│   ├── impact.py                       # 复用 HarneticsLLM，无需新增接口
│   └── status.py                       # 暴露 effective route 与配置来源
└── engine/
    ├── draft_generator.py              # 继续记录真实 effective model
    └── impact_analyzer.py              # 继续复用统一 LLM 调用边界

tests/
├── test_graph_store.py                 # 云端 embedding 路由与本地 sentence-transformers 边界回归
├── test_env_routing.py                 # fake provider 端到端 completion/embedding 路由回归
├── test_llm_client.py                  # OpenAI-compatible 客户端、错误脱敏、本地 fallback 回归
├── test_app.py                         # .env 解析与服务装配回归
└── test_e2e_mvp_scenario.py            # 状态端点与关键工作流回归
```

**Structure Decision**: 保持单仓单后端结构；仅修改现有 LLM 适配层、配置层、状态端点与对应测试，不新建服务或新前端模块。

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 新增 OpenAI SDK 依赖 | 直接采用 OpenAI-compatible 原生语义并减少 provider 适配噪音 | 继续使用 litellm 无法消除 provider/model 归一化分叉与误路由困惑 |
