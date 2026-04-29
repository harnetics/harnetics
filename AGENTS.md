# harnetics - 商业航天文档对齐产品工作台
Markdown + YAML + public docs + local planning workspace

<directory>
docs/ - 文档树：根层承载公开架构/协作文档，子目录承载设计、规格、执行计划、生成物与本地记忆材料 (7 子目录: bank, daily, design-docs, exec-plans, generated, product-specs, references)
fixtures/ - 航天领域样本文档语料，模拟跨部门、跨层级、跨版本对齐场景，作为未来解析、检索、评测与演示输入
frontend/ - React 18 + TypeScript 5.7 + Vite 6 SPA 前端 (shadcn/ui amethyst-haze 主题)
scripts/ - 本地自动化脚本与工作流入口（默认按本地私有工作区处理）
specs/ - 本地 Spec Kit 特性目录（默认不进入 Git 发布），保存每个顺序特性的 spec/plan/tasks/checklists/contracts 闭环产物
src/ - Python 应用源码，含 graph store/API/engine/evaluators/LLM/CLI 全栈
tests/ - pytest 回归、契约与端到端场景集合
var/ - 本地运行时产物目录（SQLite、上传文件、导出、向量索引）
</directory>

<config>
AGENTS.md - 项目宪法、全局地图、目录协议入口
README.md - 面向开源社区的项目入口（中文优先），含 badges、Quick Start、API 路由
LICENSE - Apache License 2.0
Dockerfile - 容器镜像构建入口，封装 Python 运行时、依赖安装与 CLI 启动命令
.dockerignore - 容器构建上下文裁剪规则，排除本地缓存、运行时产物与私有工作区材料
docker-compose-local.yml - 本地模型 Docker Compose 配置（harnetics + Ollama + Qwen 预配置）
docs/ARCHITECTURE.md - 当前系统结构、数据流、边界与演进方向
docs/CONTRIBUTING.md - 贡献者指南（开发环境、分支策略、PR 流程、编码规范）
docs/CODE_OF_CONDUCT.md - Contributor Covenant v2.1 社区行为准则
docs/CHANGELOG.md - 版本发布历史（Keep a Changelog 格式）
.github/ - GitHub 特定配置（SECURITY.md、CI workflow、Issue/PR 模板）
</config>

目录树
- docs/：本地规划与治理页面（gitignored）
- fixtures/：样本需求、设计、ICD、质量、模板与测试大纲
- frontend/：React SPA 前端 (开发: `npm run dev` / 生产: `npm run build` → FastAPI 托管)
- scripts/：本地自动化脚本（默认按本地私有工作区处理）
- specs/：本地 Spec Kit 闭环产物（gitignored）
- src/：Python 后端与图谱/LLM/导入/评估引擎
- tests/：契约、回归与 E2E 测试
- var/：本地运行时数据库与索引目录

架构法则
- 根目录保留最小公开入口；公开协作文档集中到 `docs/` 根层，`docs/bank/`、`docs/daily/` 与 `specs/` 保持本地工作区属性
- `fixtures/` 只放可解析的领域样本，不混入规划性说明文档
- 目录职责变化、文件迁移、模块新增时，先更新对应目录 `AGENTS.md`，再回写本文件

变更日志
- 2026-04-05: 初始化 canonical 文档目录，建立 `docs/` 真相源
- 2026-04-05: 将历史根目录 PRD 迁入 `docs/product-specs/`，将架构叙事迁入 `docs/design-docs/`
- 2026-04-05: 为 `docs/` 与 `fixtures/` 补齐分形 `AGENTS.md` 导航
- 2026-04-05: 新增 `docs/superpowers/specs/`，存放经 brainstorming 确认的设计 spec
- 2026-04-06: 新增根级 `README.md`，固化项目启动、冒烟与导航入口
- 2026-04-11: 补齐顶级 `specs/` / `src/` / `tests/` / `var/` 地图，纳入 GEB 目录导航
- 2026-04-11: 新增 `003-llm-impact-hardening` 特性闭环，收敛 LLM 连接稳健性与影响分析章节定位
- 2026-04-11: 新增 `docs/daily/` 开发记忆日志目录，开始沉淀当日实现决策
- 2026-04-12: 完成 `005-openai-compatible-llm-client` 主实现，远端 completion/embedding 统一走 OpenAI-compatible SDK，状态别名端点增加短 TTL 探测缓存
- 2026-04-19: `008-opensource-readiness` — 开源项目基础设施：LICENSE (Apache 2.0)、CONTRIBUTING.md、CODE_OF_CONDUCT.md、CHANGELOG.md、.github/ (SECURITY.md + CI workflow + Issue/PR 模板)、README 重写、pyproject.toml 元数据补全、开源运营手册
- 2026-04-19: `specs/`、`.agents/`、`.specify/` 保持本地工作区；`docs/bank/` 与 `docs/daily/` 进入 `.gitignore`，公开协作文档迁入 `docs/` 根层统一承载
- 2026-04-20: Dockerfile 改为纯 Python 轮子安装路径，移除易失败的 apt 构建依赖；新增 `.dockerignore` 缩减镜像构建上下文
- 2026-04-20: Dockerfile 新增 Node 前端构建阶段并将 `frontend/dist` 打入运行时镜像，镜像拉取后可直接启动完整 SPA + API 应用
- 2026-04-20: `009-cloud-deploy-settings` — 前端设置页面 (LLM/Embedding 运行时配置)、文档上传按钮接入后端 API、docker-compose 拆分云端/本地、README Docker 部署首选 + Qwen 模型对照表
- 2026-04-24: `010-rich-doc-import-autoindex` — 富格式文档导入（.docx/.xlsx/.csv/.pdf）+ 上传后自动向量索引修复；新增 docx_parser/xlsx_parser/pdf_parser；pyproject.toml 新增 python-docx/openpyxl/pypdf 依赖
- 2026-04-24: `011-dx-startup-polish` — 启动时 LLM/Embedding 配置检测与友好引导、URL 显示改为 localhost + 自动打开浏览器（--no-browser 可禁用）、fixtures/samples/ 一键导入目录、文档库删除按钮（前端 + 向量库同步清除）
- 2026-04-25: `013-doc-comparison-review` — 文档比对审查工作台：审查大纲 vs 应答文件 LLM 符合性审查（covered/partial/missing/unclear）、双文件上传、结果 Tabs 预览 + 章节溯源跳转、历史会话记录、Markdown 报告导出；新增 comparison_analyzer.py / api/routes/comparison.py / Comparison.tsx / ComparisonSession.tsx
- 2026-04-29: `014-dark-mode` — 前端夜间模式集成：ThemeProvider Context + localStorage 持久化 + 系统偏好自动检测 + FOUC 防止脚本；Header 新增月亮/太阳主题切换按钮

## Active Technologies
- Python 3.11+ + FastAPI (web framework), Jinja2 (templates), HTMX (frontend interactivity), litellm (LLM client), chromadb (vector store), sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (embeddings), PyYAML (parsing), typer+rich (CLI), uvicorn (ASGI server), python-multipart (file upload) (001-aerospace-doc-alignment)
- SQLite (relational store, single-file) + chromadb (vector embeddings, section-level) (001-aerospace-doc-alignment)
- TypeScript 5.7 (frontend) + Python 3.11+ (backend, 已有) + React 18, Vite 6, react-router-dom 6, shadcn/ui, Tailwind CSS v4, lucide-react, FastAPI (backend) (002-react-frontend-replacement)
- SQLite (backend, 已有) — 前端无本地持久化 (002-react-frontend-replacement)
- Python 3.13 (backend) + TypeScript 5.7 (existing frontend untouched) + FastAPI, httpx, openai SDK, python-dotenv, pytest (005-openai-compatible-llm-client)
- SQLite (graph DB) + ChromaDB + sentence-transformers + OpenAI-compatible embeddings (005-openai-compatible-llm-client)
- Python 3.13 (backend) + TypeScript 5.7 (frontend) + FastAPI, React 18, Vite 6, shadcn/ui, react-markdown + remark-gfm (新增) (006-draft-workbench-enhancement)
- SQLite (var/harnetics-graph.db) (006-draft-workbench-enhancement)
- Python 3.13 + TypeScript 5.7 + FastAPI, React 18, Vite 6, shadcn/ui, Tailwind v4; python-docx, openpyxl, pypdf (010-rich-doc-import-autoindex)
- SQLite (`var/harnetics-graph.db`) + ChromaDB (007-remove-legacy-workflow)

## Recent Changes
- 001-aerospace-doc-alignment: Added Python 3.11+ + FastAPI (web framework), Jinja2 (templates), HTMX (frontend interactivity), litellm (LLM client), chromadb (vector store), sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (embeddings), PyYAML (parsing), typer+rich (CLI), uvicorn (ASGI server), python-multipart (file upload)
- 002-react-frontend-replacement: Replaced Jinja2/HTMX frontend with React 18 SPA. Added frontend/ directory with TypeScript, Vite, shadcn/ui, Tailwind v4. Removed web_router from api/app.py, added SPA fallback. Added GET /api/graph/edges, GET /api/impact (list), and GET /api/dashboard/stats while保留 /api/status 兼容别名。
- 005-openai-compatible-llm-client: Replaced remote LiteLLM completion/embedding routing with OpenAI-compatible SDK calls, kept explicit Ollama fallback, and hardened status/env-routing diagnostics.
- 006-draft-workbench-enhancement: Markdown rendering (react-markdown+remark-gfm), auto-evaluation with Pass/Warning/Blocker mapping, citation quote backfill from graph store, export download, draft history list page with eval_summary, @tailwindcss/typography plugin.
