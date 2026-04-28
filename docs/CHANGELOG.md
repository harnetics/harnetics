# 更新日志

本文件记录 Harnetics 项目的所有重要变更。

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [0.1.2] - 2026-04-28

### 新增

- **Evolution 进化视图**：新增 Evolution 页面，展示 GEP signal history、策略徽章与标签分布统计，并补齐前端类型、API 封装与导航入口
- **本地自进化链路**：新增基于 EvoMap / evolver GEP 协议的 self-evolution runner 与 signal pipeline，让评估与运行事件可沉淀为可回看的演化信号
- **Fixture API / CLI**：新增 `fixture` 路由与 `fixture_runner`，支持围绕评估器夹具执行可重复测试场景
- **校验器实验室样例集**：新增 `fixtures/evaluator-test/` 完整示例与说明文档，覆盖多类 EA / EB / ED 场景，便于演示、回归与策略验证
- **Evolution 相关 API**：新增 evolution / fixture 配套后端路由，支持进化历史查询与夹具驱动测试

### 变更

- **评估器收敛**：当前 active evaluators 收敛为 6 个，并补齐对应 fixtures 与回归测试
- **测试覆盖增强**：新增 24 条测试，同时停用 EA1 / ED1，降低噪声并集中维护更稳定、可解释的评估链路
- **README / README_EN 更新**：补充“进化视图”和“校验器实验室”能力说明，便于开源用户快速理解新闭环
- **草稿生成与评估链路调整**：`draft_generator`、citation / AI quality 等模块持续对齐新的演化信号与夹具测试流程

### 修复

- **YAML ingest 修复**：正确解析 root-level metadata 与 `sections` 列表结构
- **LLM 路由修复**：保留 HuggingFace 风格的 `Org/Model` ID，避免模型标识被错误截断
- **服务日志增强**：`harnetics serve` 启动时将 uvicorn 日志写入 `data/logs/<CST-timestamp>.log`，便于排查运行问题

## [0.1.1] - 2026-04-24

### 新增

- **富格式文档导入**：新增 `.docx`（Word）、`.xlsx`（Excel）、`.csv`、`.pdf` 格式解析支持，含专用解析器 `docx_parser`（按 Heading 拆分章节）、`xlsx_parser`（Sheet 为章节 + CSV GBK 回退）、`pdf_parser`（每页为章节）
- **上传自动向量索引**：修复上传端点，上传后立即触发向量索引，无需手动 reindex
- **文档删除按钮**：Documents 页面每行新增 Trash2 删除按钮，含 confirm 确认对话框，删除时同步清除 ChromaDB 向量条目（`EmbeddingStore.delete_by_doc`）
- **浏览器自动打开**：`harnetics serve` 启动后自动打开系统浏览器（macOS 用 `open`，其他平台用 `webbrowser`）；`--no-browser` 可禁用
- **`fixtures/samples/`**：所有样本文件整合为扁平目录，支持一键批量导入（`harnetics ingest fixtures/samples/`）
- **`fixtures/format-test/`**：6 种格式（`.md`/`.yaml`/`.csv`/`.docx`/`.xlsx`/`.pdf`）各一个最小化航天主题样本，用于验证解析器行为
- **Reindex 端点**：新增 `POST /api/documents/{doc_id}/reindex`，支持手动触发单文档重建向量索引
- **可配置 LLM max tokens**：通过环境变量 `HARNETICS_LLM_MAX_TOKENS` 控制

### 变更

- 启动地址显示改为 `http://localhost:PORT`（原为 `0.0.0.0:PORT`）
- README 配置章节重写：使用 `.env` 工作流，修正环境变量名 `OPENAI_API_KEY` → `HARNETICS_LLM_API_KEY`，补充 Embedding 配置说明
- 启动时 LLM/Embedding 未配置提示改为简洁单行 hint，引导查阅 README 或设置页
- CI 工作流升级 Node 24，更新各 actions 至最新版本，修复 Docker 构建中 uv 二进制来源

### 依赖

- 新增：`python-docx>=1.0.0`、`openpyxl>=3.1.0`、`pypdf>=4.0.0`

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

[0.1.2]: https://github.com/harnetics/harnetics/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/harnetics/harnetics/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/harnetics/harnetics/releases/tag/v0.1.0
