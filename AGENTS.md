# harnetics - 商业航天文档对齐产品工作台
Markdown + YAML + docs-first

<directory>
docs/ - 项目文档真相源，承载设计、规格、执行计划、生成物、技能流程产物与外部参考 (7 子目录: daily, design-docs, exec-plans, generated, product-specs, references, superpowers)
fixtures/ - 航天领域样本文档语料，模拟跨部门、跨层级、跨版本对齐场景，作为未来解析、检索、评测与演示输入
frontend/ - React 18 + TypeScript 5.7 + Vite 6 SPA 前端 (shadcn/ui amethyst-haze 主题)
specs/ - Spec Kit 特性目录，保存每个顺序特性的 spec/plan/tasks/checklists/contracts 闭环产物
src/ - Python 应用源码，含 legacy repository 栈与 graph/API 主工作流
tests/ - pytest 回归、契约与端到端场景集合
var/ - 本地运行时产物目录（SQLite、上传文件、导出、向量索引）
</directory>

<config>
AGENTS.md - 项目宪法、全局地图、目录协议入口
ARCHITECTURE.md - 当前系统结构、数据流、边界与演进方向
README.md - 项目运行入口，提供安装、启动、冒烟与文档导航
</config>

目录树
- docs/：当前有效文档与治理页面
- fixtures/：样本需求、设计、ICD、质量、模板与测试大纲
- frontend/：React SPA 前端 (开发: `npm run dev` / 生产: `npm run build` → FastAPI 托管)
- specs/：Spec Kit 特性闭环产物（spec/plan/tasks/checklists/contracts）
- src/：Python 后端与图谱/LLM/导入/评估引擎
- tests/：契约、回归与 E2E 测试
- var/：本地运行时数据库与索引目录

架构法则
- 根目录只保留全局入口；产品规格、设计叙事、执行计划统一进入 `docs/`
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

## Active Technologies
- Python 3.11+ + FastAPI (web framework), Jinja2 (templates), HTMX (frontend interactivity), litellm (LLM client), chromadb (vector store), sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (embeddings), PyYAML (parsing), typer+rich (CLI), uvicorn (ASGI server), python-multipart (file upload) (001-aerospace-doc-alignment)
- SQLite (relational store, single-file) + chromadb (vector embeddings, section-level) (001-aerospace-doc-alignment)
- TypeScript 5.7 (frontend) + Python 3.11+ (backend, 已有) + React 18, Vite 6, react-router-dom 6, shadcn/ui, Tailwind CSS v4, lucide-react, FastAPI (backend) (002-react-frontend-replacement)
- SQLite (backend, 已有) — 前端无本地持久化 (002-react-frontend-replacement)
- Python 3.13 (backend) + TypeScript 5.7 (existing frontend untouched) + FastAPI, httpx, openai SDK, python-dotenv, pytest (005-openai-compatible-llm-client)
- SQLite (graph DB) + ChromaDB + sentence-transformers + OpenAI-compatible embeddings (005-openai-compatible-llm-client)
- Python 3.13 (backend) + TypeScript 5.7 (frontend) + FastAPI, React 18, Vite 6, shadcn/ui, react-markdown + remark-gfm (新增) (006-draft-workbench-enhancement)
- SQLite (var/harnetics-graph.db) (006-draft-workbench-enhancement)

## Recent Changes
- 001-aerospace-doc-alignment: Added Python 3.11+ + FastAPI (web framework), Jinja2 (templates), HTMX (frontend interactivity), litellm (LLM client), chromadb (vector store), sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (embeddings), PyYAML (parsing), typer+rich (CLI), uvicorn (ASGI server), python-multipart (file upload)
- 002-react-frontend-replacement: Replaced Jinja2/HTMX frontend with React 18 SPA. Added frontend/ directory with TypeScript, Vite, shadcn/ui, Tailwind v4. Removed web_router from api/app.py, added SPA fallback. Added GET /api/graph/edges, GET /api/impact (list), and GET /api/dashboard/stats while保留 /api/status 兼容别名。
- 005-openai-compatible-llm-client: Replaced remote LiteLLM completion/embedding routing with OpenAI-compatible SDK calls, kept explicit Ollama fallback, and hardened status/env-routing diagnostics.
- 006-draft-workbench-enhancement: Markdown rendering (react-markdown+remark-gfm), auto-evaluation with Pass/Warning/Blocker mapping, citation quote backfill from graph store, export download, draft history list page with eval_summary, @tailwindcss/typography plugin.
