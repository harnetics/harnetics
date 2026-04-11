# Implementation Plan: LLM Connectivity and Impact Localization Hardening

**Branch**: `003-llm-impact-hardening` | **Date**: 2026-04-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/003-llm-impact-hardening/spec.md`

## Summary

修复两个根因级问题：一是草稿生成路由没有稳定复用应用级 LLM 配置，且 Ollama 裸模型名无法直接工作；二是图谱入库主要仍停留在文档级边，导致影响分析无法定位到具体章节。实现策略是收敛 LLM 配置解析、让草稿路由显式使用 settings，并在 indexer + impact analyzer 两层同时引入 section-aware 引用定位与兼容旧图的回退逻辑。

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, httpx, litellm, pytest
**Storage**: SQLite graph DB (`var/harnetics-graph.db`)
**Testing**: pytest
**Target Platform**: 本地开发 API 服务（Windows + WSL / Linux shell）
**Project Type**: Web application backend / graph engine
**Performance Goals**: 不增加显著启动时延；单次影响分析保持当前交互级延迟
**Constraints**: 保持现有 API 响应结构；不引入 schema migration；兼容旧文档级边
**Scale/Scope**: 4 个源码文件核心改动 + 2~3 个测试文件 + Speckit 文档闭环

## Constitution Check

*Constitution 尚未配置自定义原则，使用默认通过。*

## Project Structure

### Documentation (this feature)

```text
specs/003-llm-impact-hardening/
├── AGENTS.md
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/
│   └── review.md
├── contracts/
│   └── api-contracts.md
└── tasks.md
```

### Source Code (repository root)

```text
src/harnetics/
├── config.py                   # 可能同步默认 LLM 配置语义
├── llm/
│   └── client.py              # 模型归一化、availability 校验、错误上下文
├── api/
│   └── routes/
│       ├── draft.py           # 路由显式使用 app.state.settings 构造 LLM 客户端
│       └── status.py          # 状态端点复用相同 LLM 配置解析
├── graph/
│   └── indexer.py             # section-aware 引用提取与 target anchor 推断
└── engine/
    └── impact_analyzer.py     # edge-first + heuristic fallback 的章节定位与传播

tests/
├── test_llm_client.py         # LLM 归一化与可用性检查
└── test_e2e_mvp_scenario.py   # 草稿路由配置传递 + 影响定位回归
```

**Structure Decision**: 保持现有单仓库 Python 后端结构不变，只在 llm/api/graph/engine 四个既有模块内修复根因，并用 pytest 锁定行为。

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 无 | - | - |