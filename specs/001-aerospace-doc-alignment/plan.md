# Implementation Plan: Aerospace Document Alignment Product

**Branch**: `001-aerospace-doc-alignment` | **Date**: 2026-04-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-aerospace-doc-alignment/spec.md`

## Summary

航天文档对齐产品——导入 Markdown/YAML 航天技术文档，自动解析章节、提取 ICD 参数、建立文档间引用关系图谱；调用本地 LLM（Gemma 4 26B via Ollama）生成带 [📎 DOC-XXX-XXX §X.X] 引注标记的对齐草稿；运行 8 项 Evaluator 质量检查（阻断/告警分级）；执行变更影响分析（Critical/Major/Minor）；通过 FastAPI+Jinja2+HTMX WebUI 提供 7 页面交互体验。

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI (web framework), Jinja2 (templates), HTMX (frontend interactivity), litellm (LLM client), chromadb (vector store), sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (embeddings), PyYAML (parsing), typer+rich (CLI), uvicorn (ASGI server), python-multipart (file upload)
**Storage**: SQLite (relational store, single-file) + chromadb (vector embeddings, section-level)
**Testing**: pytest + pytest-asyncio + httpx (API testing) + ruff (lint)
**Target Platform**: Linux / macOS / Windows (WSL2), local deployment, Docker Compose option
**Project Type**: web-service with CLI (`harnetics init|ingest|serve`)
**Performance Goals**: Draft generation <3min for 10-doc context, document import <5s each, impact analysis <30s
**Constraints**: Single-machine deployment, GPU-required (RTX 4090 24GB / Apple M series), offline-only (aerospace security requirement), Chinese UI, no auth/permissions in MVP
**Scale/Scope**: 10 fixture documents, 7 WebUI pages, 8 evaluators (EA.1-5, EB.1, ED.1, ED.3), ~20 API endpoints, 1 project (天行一号)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**N/A** — Constitution file (`.specify/memory/constitution.md`) is a blank template. No project-specific principles have been defined. Gate passes trivially.

## Project Structure

### Documentation (this feature)

```text
specs/001-aerospace-doc-alignment/
├── plan.md              # This file
├── research.md          # Phase 0: technology decisions
├── data-model.md        # Phase 1: entity definitions + SQLite schema
├── quickstart.md        # Phase 1: install, run, smoke test
├── contracts/           # Phase 1: API contracts per domain
│   ├── documents-api.md
│   ├── graph-api.md
│   ├── draft-api.md
│   ├── impact-api.md
│   ├── evaluate-api.md
│   └── status-api.md
└── tasks.md             # Phase 2 output (NOT created by plan)
```

### Source Code (repository root)

```text
src/harnetics/
├── __init__.py
├── config.py                 # 全局配置（DB 路径、LLM 参数、嵌入模型）
├── models/
│   ├── __init__.py
│   ├── document.py           # DocumentNode, Section, DocumentEdge
│   ├── icd.py                # ICDParameter
│   ├── draft.py              # DraftRequest, AlignedDraft, Citation, Conflict
│   └── impact.py             # ImpactReport, ImpactedDoc, SectionDiff
├── parsers/
│   ├── __init__.py
│   ├── markdown_parser.py    # MD → Section tree
│   ├── yaml_parser.py        # Generic YAML → dict
│   └── icd_parser.py         # ICD YAML → ICDParameter list
├── graph/
│   ├── __init__.py
│   ├── store.py              # SQLite CRUD
│   ├── schema.sql            # DDL 建表脚本
│   ├── indexer.py             # 文档入库 + 规则关系抽取
│   ├── query.py               # DocumentGraph 查询 API
│   └── embeddings.py          # chromadb section embeddings
├── engine/
│   ├── __init__.py
│   ├── draft_generator.py     # 检索→组装→LLM→引注解析
│   ├── impact_analyzer.py     # diff→下游查询→影响评估
│   └── conflict_detector.py   # 跨文档参数冲突检测
├── evaluators/
│   ├── __init__.py
│   ├── base.py                # BaseEvaluator + EvaluatorBus
│   ├── citation.py            # EA.1–EA.5
│   ├── icd.py                 # EB.1
│   └── ai_quality.py          # ED.1, ED.3
├── llm/
│   ├── __init__.py
│   ├── client.py              # litellm wrapping Ollama
│   └── prompts.py             # System prompt templates
├── api/
│   ├── __init__.py
│   ├── app.py                 # FastAPI app factory
│   ├── deps.py                # 依赖注入（DB session, graph, LLM client）
│   └── routes/
│       ├── documents.py       # /api/documents/*
│       ├── graph.py           # /api/graph/*
│       ├── draft.py           # /api/draft/*
│       ├── impact.py          # /api/impact/*
│       ├── evaluate.py        # /api/evaluate/*
│       └── status.py          # /api/status
├── web/
│   ├── __init__.py
│   ├── routes.py              # 页面路由（7 pages）
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── documents/
│   │   │   ├── list.html
│   │   │   ├── upload.html
│   │   │   └── detail.html
│   │   ├── draft/
│   │   │   ├── workspace.html
│   │   │   ├── progress.html
│   │   │   └── result.html
│   │   ├── impact/
│   │   │   ├── analyze.html
│   │   │   └── report.html
│   │   └── graph/
│   │       └── view.html
│   └── static/
│       ├── css/app.css
│       └── js/
│           ├── htmx.min.js
│           └── graph.js
└── cli/
    ├── __init__.py
    └── main.py                # typer CLI: init / ingest / serve

tests/
├── conftest.py
├── test_parsers/
│   ├── test_markdown_parser.py
│   ├── test_yaml_parser.py
│   └── test_icd_parser.py
├── test_graph/
│   ├── test_store.py
│   ├── test_indexer.py
│   └── test_query.py
├── test_engine/
│   ├── test_draft_generator.py
│   └── test_impact_analyzer.py
├── test_evaluators/
│   ├── test_citation.py
│   ├── test_icd.py
│   └── test_ai_quality.py
├── test_api/
│   └── test_routes.py
└── test_e2e/
    └── test_mvp_scenario.py

fixtures/                      # 10 aerospace fixture documents (已存在)
```

**Structure Decision**: Single-project web-service layout under `src/harnetics/`. 模块按 domain 垂直切分（parsers → graph → engine → evaluators → llm → api → web → cli），每层依赖下层，单向数据流。API 层和 Web 层并行挂载到同一 FastAPI 实例。

## Complexity Tracking

> No constitution violations to justify — gate is N/A.
