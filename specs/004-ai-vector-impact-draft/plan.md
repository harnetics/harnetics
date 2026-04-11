# Implementation Plan: AI 向量驱动的影响分析与草稿联动

**Branch**: `004-ai-vector-impact-draft` | **Date**: 2026-04-11 | **Spec**: [spec.md](spec.md)

## Summary

将影响分析从纯规则遍历升级为 AI 向量语义分析：向量粗筛 + LLM 精判，精准定位受影响章节（从≈100% 降至≤30%）。同时实现影响报告→草稿台自动预填联动、草稿台候选文档向量检索、`.env` 统一配置本地/云端 LLM 与 embedding 模型。

## Technical Context

**Language/Version**: Python 3.11+ (backend) + TypeScript 5.7 (frontend)
**Primary Dependencies**: FastAPI, litellm (LLM+embedding routing), chromadb, python-dotenv (新增)
**Storage**: SQLite (graph DB) + ChromaDB (vector embeddings)
**Testing**: pytest
**Target Platform**: Linux server / Windows dev
**Project Type**: web-service (FastAPI + React SPA)
**Constraints**: LLM 单次调用 <30s, 全流程 <120s, API key 不泄露

## Project Structure

### Documentation (this feature)

```text
specs/004-ai-vector-impact-draft/
├── spec.md
├── plan.md              # This file
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── api-contracts.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (changes to existing)

```text
src/harnetics/
├── config.py                          # 扩展 Settings，新增 embedding 配置 + dotenv
├── graph/
│   └── embeddings.py                  # EmbeddingStore 支持云端 embedding 提供商
├── engine/
│   └── impact_analyzer.py             # 新增 AI 向量分析路径
├── llm/
│   └── client.py                      # 复用，无重大改动
├── api/routes/
│   ├── impact.py                      # 响应增加 analysis_mode + reason
│   ├── draft.py                       # 支持预填参数、向量文档检索
│   └── documents.py                   # 新增 GET /api/documents/search
└── models/
    └── impact.py                      # AffectedSection 结构扩展

frontend/src/
├── pages/
│   ├── ImpactReport.tsx               # "生成对齐草稿"按钮传参
│   └── DraftNew.tsx                   # 向量检索 + 预填逻辑
├── lib/api.ts                         # 新增 searchDocuments、API 签名更新
└── types/index.ts                     # TypeScript 类型同步
```
