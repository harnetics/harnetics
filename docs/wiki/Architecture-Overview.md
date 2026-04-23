# Architecture Overview

## 当前形态

Harnetics 当前采用 FastAPI 后端 + React/Vite SPA 前端：

- `src/harnetics/`：图谱、草稿、影响分析与 API
- `frontend/`：React 18 + TypeScript + shadcn/ui
- `fixtures/`：航天领域受控样本
- `var/harnetics-graph.db`：SQLite 图谱存储

## 核心数据流

1. `DocumentIndexer` 解析 Markdown/YAML 或上传文档
2. 提取章节、引用关系与 ICD 参数写入 SQLite graph store
3. `DraftGenerator` 基于图谱上下文与 LLM 生成带引注草稿
4. `EvaluatorBus` 运行质量门评估器
5. `ImpactAnalyzer` 沿引用图做 BFS 影响分析
6. `api/` 把数据提供给 SPA
