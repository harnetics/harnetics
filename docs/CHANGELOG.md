# 更新日志

本文件记录 Harnetics 项目的所有重要变更。

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [0.1.0] - 2026-04-20

### 新增

- **文档库**：支持上传与浏览 Markdown/YAML 文档，自动解析章节与 ICD 参数；上传按钮已接入 `POST /api/documents/upload`
- **文档图谱**：基于 SQLite 持久化文档关系有向图（`traces_to`、`references`、`derived_from`、`constrained_by`、`supersedes`、`impacts`）
- **草稿生成**：基于 LLM 的对齐草稿生成，支持从图谱回填引注、检测冲突，并通过评估器质量门
- **影响分析**：基于 BFS 的下游变更影响分析，支持双模式（AI 向量检索 + 启发式分析）、批量 LLM 判断与按请求缓存
- **Evaluator Bus**：可插拔质量门框架，包含 EA（引注完整性）、EB（ICD 一致性）与 ED（AI 质量）评估器族
- **React SPA 前端**：9 页 React 18 + TypeScript 5.7 应用，使用 shadcn/ui 的 amethyst-haze 主题，包含 Dashboard、Documents、Draft Workbench、Impact Analysis 与 Graph Visualization
- **设置页面**：支持在 Web 设置页编辑运行时 LLM / Embedding 配置（API Key、模型名、Base URL），并通过 `write_dotenv_values()` 持久化到 `.env`
- **OpenAI-Compatible LLM Client**：基于 OpenAI SDK 的厂商无关 LLM 路由，显式支持 Ollama 回退与状态诊断
- **Embedding Search**：基于 ChromaDB 的章节级语义检索，支持 sentence-transformers 与 OpenAI-compatible embedding
- **CLI**：通过 typer 提供 `harnetics init`、`harnetics ingest`、`harnetics serve` 命令
- **Docker 支持**：多阶段 Dockerfile（Node 22 前端构建 + Python 3.12 运行时）；`docker-compose.yml` 用于云端/API Key 部署；`docker-compose-local.yml` 用于本地 Ollama GPU 部署；前端 `dist` 已打包进运行时镜像，因此 `docker compose up` 即可同时提供完整 SPA + API
- **样例语料**：10+ 航天领域样本文档（需求、ICD、设计、测试计划、质量、模板），用于开发与演示

### 变更

- Dockerfile 依赖安装从 pip 切换到 **uv**（使用本地 `.docker/uv` 二进制，不在构建时联网拉取）
- 将 `docker-compose.yml` 与 `docker-compose-local.yml` 拆分为云端部署与本地模型部署两套入口
- README 改写为以 Docker 为主的快速体验路径，并新增 Qwen 3.5 模型兼容表（含 4-bit VRAM 需求）

### 架构

- 单一工作流闭环：导入 → 解析与图谱索引 → LLM 草稿生成 → Evaluator 质量门 → 影响分析 → API / Web UI
- 后端：Python 3.12+ / FastAPI / SQLite（graph store）/ ChromaDB（vector embeddings）
- 前端：React 18 / TypeScript 5.7 / Vite 6 / Tailwind CSS v4 / shadcn/ui
- 本地优先设计：默认所有数据保留在用户机器上；`.env` 是运行时配置的单一真相源

[0.1.0]: https://github.com/harnetics/harnetics/releases/tag/v0.1.0
