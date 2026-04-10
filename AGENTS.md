# harnetics - 商业航天文档对齐产品工作台
Markdown + YAML + docs-first

<directory>
docs/ - 项目文档真相源，承载设计、规格、执行计划、生成物、技能流程产物与外部参考 (6 子目录: design-docs, exec-plans, generated, product-specs, references, superpowers)
fixtures/ - 航天领域样本文档语料，模拟跨部门、跨层级、跨版本对齐场景，作为未来解析、检索、评测与演示输入
</directory>

<config>
AGENTS.md - 项目宪法、全局地图、目录协议入口
ARCHITECTURE.md - 当前系统结构、数据流、边界与演进方向
README.md - 项目运行入口，提供安装、启动、冒烟与文档导航
</config>

目录树
- docs/：当前有效文档与治理页面
- fixtures/：样本需求、设计、ICD、质量、模板与测试大纲

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

## Active Technologies
- Python 3.11+ + FastAPI (web framework), Jinja2 (templates), HTMX (frontend interactivity), litellm (LLM client), chromadb (vector store), sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (embeddings), PyYAML (parsing), typer+rich (CLI), uvicorn (ASGI server), python-multipart (file upload) (001-aerospace-doc-alignment)
- SQLite (relational store, single-file) + chromadb (vector embeddings, section-level) (001-aerospace-doc-alignment)

## Recent Changes
- 001-aerospace-doc-alignment: Added Python 3.11+ + FastAPI (web framework), Jinja2 (templates), HTMX (frontend interactivity), litellm (LLM client), chromadb (vector store), sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (embeddings), PyYAML (parsing), typer+rich (CLI), uvicorn (ASGI server), python-multipart (file upload)
