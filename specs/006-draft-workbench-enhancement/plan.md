# Implementation Plan: 草稿工作台增强

**Branch**: `006-draft-workbench-enhancement` | **Date**: 2026-04-12 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/006-draft-workbench-enhancement/spec.md`

## Summary

增强草稿工作台的六个维度：Markdown 渲染预览、评估结果结构化适配（自动触发 + Pass/Warning/Blocker 三级映射）、引用来源章节内容回填、导出按钮下载修复、历史草稿列表页。涉及前端 3 个页面组件变更 + 1 个新页面、后端 2 个路由扩展 + 生成器引用回填。

## Technical Context

**Language/Version**: Python 3.13 (backend) + TypeScript 5.7 (frontend)
**Primary Dependencies**: FastAPI, React 18, Vite 6, shadcn/ui, react-markdown + remark-gfm (新增)
**Storage**: SQLite (var/harnetics-graph.db)
**Testing**: pytest (backend) + 手动验证 (frontend, 无 vitest 配置)
**Target Platform**: Web SPA + FastAPI server
**Project Type**: web-service (full-stack)
**Performance Goals**: 草稿列表 <500ms, Markdown 渲染客户端 <100ms
**Constraints**: 不新增外部服务依赖，所有变更仅 SQLite + 现有 LLM 链路
**Scale/Scope**: 单用户工作台，草稿量 <1000

## Constitution Check

*Constitution template未填写，跳过 gate。*

## Project Structure

### Documentation (this feature)

```text
specs/006-draft-workbench-enhancement/
├── spec.md
├── plan.md              # 本文件
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
frontend/
├── src/
│   ├── pages/
│   │   ├── DraftShow.tsx      # 修改：Markdown 渲染 + 评估适配 + 导出修复
│   │   ├── DraftNew.tsx       # 修改：评估自动触发后跳转逻辑
│   │   └── DraftHistory.tsx   # 新增：历史草稿列表页
│   ├── components/
│   │   └── MarkdownRenderer.tsx  # 新增：通用 Markdown 渲染器
│   ├── lib/
│   │   └── api.ts             # 修改：扩展 fetchDrafts 返回字段
│   └── types/
│       └── index.ts           # 修改：扩展 DraftSummary 类型
├── package.json               # 修改：新增 react-markdown + remark-gfm

src/harnetics/
├── api/routes/
│   ├── draft.py               # 修改：生成后自动评估、列表返回 subject、引用回填
│   └── evaluate.py            # 不变
├── engine/
│   └── draft_generator.py     # 修改：引用 quote 回填章节内容
├── models/
│   └── draft.py               # 不变
└── evaluators/
    └── base.py                # 不变

tests/
└── (回归验证)
```

**Structure Decision**: 采用已有 frontend/ + src/ 双目录结构，新增 1 个页面组件 + 1 个 Markdown 组件，扩展 2 个后端路由。
