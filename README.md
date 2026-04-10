# Harnetics

商业航天文档对齐产品工作台。基于 FastAPI + SQLite + ChromaDB + Ollama，实现文档库管理、AI 草稿生成、评估闭环、变更影响分析与文档关系图谱。

> 注：仓库中仍保留旧版 `Repository` 工作流，其默认数据库为 `var/harnetics.db`；本次 spec 对应的新图谱栈默认使用独立的 `var/harnetics-graph.db`，两者不要混用同一文件。

## 核心功能

| 功能模块 | 说明 |
|---------|------|
| 📂 文档库（US1） | 上传/浏览 Markdown 与 YAML 文档，解析章节与 ICD 参数 |
| ✍️ 草稿生成（US2） | AI 三步生成带📎引注草稿，冲突自动标记 |
| ⚡ 变更影响分析（US3） | BFS 遍历下游依赖图，评定 Critical/Major/Minor 危险等级 |
| 🔗 文档图谱（US4） | vis-network 可视化关系网络，节点点击查看详情 |
| 📊 仪表盘（US5） | 统计看板：文档数、草稿数、陈旧引用、LLM 状态 |
| ✅ Evaluator（US6） | 8 项评估规则：引注完整性、ICD 一致性、AI 防幻觉 |

## 技术栈

- **Web**: Python 3.12 + FastAPI + Jinja2 + HTMX + DaisyUI/Tailwind
- **存储**: SQLite（图谱结构）+ ChromaDB（向量索引）
- **LLM**: Ollama（gemma4:26b，via litellm）
- **Embeddings**: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

## 快速启动

### 前置依赖

- Python `>=3.12` + `uv`
- [Ollama](https://ollama.ai) 并拉取模型：`ollama pull gemma4:26b-it-a4b-q4_K_M`

### 安装 & 启动

```bash
# 安装依赖
uv sync --dev

# 初始化数据库
uv run python -m harnetics.cli.main init

# 批量导入样本文档
uv run python -m harnetics.cli.main ingest fixtures/

# 如需同时构建 Chroma 向量索引（首次运行可能较慢）
uv run python -m harnetics.cli.main ingest fixtures/ --with-embeddings

# 启动 Web 服务
uv run python -m harnetics.cli.main serve --reload
```

默认访问 `http://localhost:8000`（首页自动跳转仪表盘）

### 或使用 Docker Compose

```bash
docker compose up -d
# 初始化并导入样本
docker compose exec harnetics python -m harnetics.cli.main init
docker compose exec harnetics python -m harnetics.cli.main ingest fixtures/
```

## curl 冒烟测试

```bash
# 上传文档
curl -F file=@fixtures/requirements/DOC-SYS-001.md http://localhost:8000/api/documents/upload
curl -F file=@fixtures/icd/DOC-ICD-001.yaml http://localhost:8000/api/documents/upload

# 查看文档列表
curl http://localhost:8000/api/documents | python -m json.tool

# 系统状态
curl http://localhost:8000/api/status | python -m json.tool

# 生成草稿（需 Ollama 运行）
curl -X POST http://localhost:8000/api/draft/generate \
  -H 'Content-Type: application/json' \
  -d '{"subject":"推进与结构接口草稿","related_doc_ids":["DOC-SYS-001","DOC-ICD-001"]}'

# 影响分析
curl -X POST http://localhost:8000/api/impact/analyze \
  -H 'Content-Type: application/json' \
  -d '{"doc_id":"DOC-SYS-001","old_version":"v1.0","new_version":"v2.0"}'
```

## 测试

```bash
# 单元测试（不需要 Ollama）
uv run pytest tests/ -q --ignore=tests/test_e2e_mvp_scenario.py

# 全量测试（含 E2E，需要 fixtures 目录）
uv run pytest tests/ -q
```

## 页面导航

| URL | 说明 |
|-----|------|
| `/dashboard` | 系统概览仪表盘 |
| `/documents` | 文档库列表 |
| `/documents/upload` | 上传文档 |
| `/documents/{doc_id}` | 文档详情 + 章节 + 关系 |
| `/drafts/workspace` | 草稿生成工作台（三步向导）|
| `/drafts/{draft_id}` | 草稿详情 + 评估结果 |
| `/impact` | 变更影响分析 |
| `/graph` | 文档关系图谱 |

## 运行时目录

```
var/
├── harnetics.db         # 旧版 Repository 工作流数据库（兼容保留）
├── harnetics-graph.db   # 新版 spec 图谱数据库
└── chroma/        # ChromaDB 向量索引
```

## 测试
```

这次我实际跑通了下面这条链路：

- 启动 FastAPI 应用
- `GET /health`
- 导入 `fixtures/` 下 4 份样本文档
- `GET /documents`
- `POST /drafts/plan`
- `POST /drafts`
- `GET /drafts/1`
- `GET /drafts/1/export`

其中草稿生成阶段使用了一个临时本地 mock OpenAI-compatible 服务来占位默认 LLM 端口，目的是验证应用链路本身，而不是验证某个具体模型。

## 目录入口

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [docs/PRODUCT_SENSE.md](docs/PRODUCT_SENSE.md)
- [docs/RELIABILITY.md](docs/RELIABILITY.md)
- [docs/SECURITY.md](docs/SECURITY.md)
- [docs/product-specs/mvp-prd.md](docs/product-specs/mvp-prd.md)
