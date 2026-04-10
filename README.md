# Harnetics

商业航天文档对齐工作台。当前主线是 FastAPI 图谱后端 + React/Vite SPA 前端，用于文档入库、草稿生成、评估闭环、变更影响分析与文档关系图谱。

> 注：仓库仍保留旧版 `Repository` 工作流，其默认数据库为 `var/harnetics.db`；当前 React 前端与图谱 API 默认使用独立的 `var/harnetics-graph.db`。两者不要混用同一 SQLite 文件。

## 技术栈

- 后端：Python 3.11+、FastAPI、SQLite、ChromaDB
- 前端：React 18、TypeScript 5.7、Vite 6、Tailwind CSS v4、shadcn/ui
- LLM：LiteLLM 统一接入，本地默认 Ollama，也支持 OpenAI-compatible 云端模型
- Embeddings：sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

## 核心功能

| 模块 | 说明 |
|------|------|
| 文档库 | 上传/浏览 Markdown 与 YAML 文档，解析章节与 ICD 参数 |
| 草稿生成 | 基于来源文档生成带引注草稿，并输出冲突与评估结果 |
| 影响分析 | 沿依赖链分析文档变更会波及哪些下游文档 |
| 文档图谱 | 可视化文档间引用/派生/约束关系 |
| 仪表盘 | 文档数、草稿数、陈旧引用、LLM 状态等总览 |

## 前置依赖

- Python `>=3.11`
- `uv`
- Node.js `>=20`
- `npm`

## 安装

```bash
uv sync --dev
cd frontend
npm install
cd ..
```

## 配置 LLM

### 方案 A：本地 Ollama（默认）

适合离线开发和本地联调。当前默认模型就是 Ollama。

PowerShell:

```powershell
$env:HARNETICS_LLM_MODEL = "ollama/gemma4:26b-it-a4b-q4_K_M"
$env:HARNETICS_LLM_BASE_URL = "http://localhost:11434"
ollama pull gemma4:26b-it-a4b-q4_K_M
ollama serve
```

Bash:

```bash
export HARNETICS_LLM_MODEL="ollama/gemma4:26b-it-a4b-q4_K_M"
export HARNETICS_LLM_BASE_URL="http://localhost:11434"
ollama pull gemma4:26b-it-a4b-q4_K_M
ollama serve
```

校验：

```bash
curl http://localhost:11434/api/tags
```

### 方案 B：云端 OpenAI / OpenAI-compatible

适合直接调用云端模型，或接公司内网网关 / LiteLLM Proxy / vLLM / 其他 OpenAI-compatible 端点。

PowerShell:

```powershell
$env:HARNETICS_LLM_MODEL = "openai/gpt-4o-mini"
$env:OPENAI_API_KEY = "<your-api-key>"
$env:HARNETICS_LLM_BASE_URL = "https://api.openai.com/v1"
```

Bash:

```bash
export HARNETICS_LLM_MODEL="openai/gpt-4o-mini"
export OPENAI_API_KEY="<your-api-key>"
export HARNETICS_LLM_BASE_URL="https://api.openai.com/v1"
```

如果你接的是自建或第三方 OpenAI-compatible 网关，把 `HARNETICS_LLM_BASE_URL` 换成对应的 `/v1` 根地址即可，例如：

```bash
export HARNETICS_LLM_MODEL="openai/your-model-name"
export OPENAI_API_KEY="dummy-or-real-key"
export HARNETICS_LLM_BASE_URL="http://your-gateway:8000/v1"
```

说明：

- 草稿生成走 LiteLLM；`HARNETICS_LLM_MODEL` 决定 provider/model。
- `HARNETICS_LLM_BASE_URL` 用来覆盖 provider 的 API base；对本地 OpenAI-compatible 网关也生效。
- 官方 OpenAI 也可直接使用 `OPENAI_BASE_URL`；当前项目优先推荐统一配置 `HARNETICS_LLM_BASE_URL`。
- 仪表盘中的 `llm_available`：Ollama 会主动探测；云端 / OpenAI-compatible 目前按密钥是否已配置判断。

## 初始化数据

```bash
uv run python -m harnetics.cli.main init --reset
uv run python -m harnetics.cli.main ingest fixtures/

# 如需同时建立向量索引（首次会慢一些）
uv run python -m harnetics.cli.main ingest fixtures/ --with-embeddings
```

## 启动

### 开发模式

后端：

```bash
uv run python -m harnetics.cli.main serve --reload
```

前端：

```bash
cd frontend
npm run dev
```

访问：

- 前端开发地址：`http://localhost:5173`
- 后端 API：`http://localhost:8000`

### 生产构建 / 单端口托管

```bash
cd frontend
npm run build
cd ..
uv run python -m harnetics.cli.main serve
```

构建后，FastAPI 会自动托管 `frontend/dist/`，直接访问 `http://localhost:8000`。

## API / UI 冒烟测试

```bash
# 健康检查
curl http://localhost:8000/health

# 仪表盘统计
curl http://localhost:8000/api/dashboard/stats

# 文档列表
curl http://localhost:8000/api/documents

# 图谱原始边
curl http://localhost:8000/api/graph/edges

# 影响分析报告列表
curl http://localhost:8000/api/impact

# 触发一次影响分析
curl -X POST http://localhost:8000/api/impact/analyze \
  -H 'Content-Type: application/json' \
  -d '{"doc_id":"DOC-SYS-001","old_version":"v1.0","new_version":"v2.0"}'
```

手工 UI 校验建议顺序：

1. 打开 `/`，确认仪表盘能加载统计。
2. 打开 `/documents`，确认样本文档可见。
3. 进入某份 Requirement 文档后，在 `/impact` 里以它为触发文档发起影响分析。
4. 打开 `/graph`，确认图谱节点和边存在。

## 路由

| 路径 | 说明 |
|------|------|
| `/` | 仪表盘首页 |
| `/documents` | 文档列表 |
| `/documents/{doc_id}` | 文档详情 |
| `/draft` | 草稿工作台 |
| `/draft/{draft_id}` | 草稿详情 |
| `/impact` | 影响分析首页 |
| `/impact/{report_id}` | 影响分析详情 |
| `/graph` | 文档图谱 |
| `/design-system` | 设计系统演示页 |

## 测试

```bash
# 后端测试
uv run pytest tests/ -q

# 前端构建校验
cd frontend
npm run build
```

## 运行时目录

```text
var/
├── harnetics.db         # 旧版 Repository 工作流数据库（兼容保留）
├── harnetics-graph.db   # 图谱 / React SPA 主工作流数据库
└── chroma/              # ChromaDB 向量索引
```

## 文档入口

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [docs/PRODUCT_SENSE.md](docs/PRODUCT_SENSE.md)
- [docs/RELIABILITY.md](docs/RELIABILITY.md)
- [docs/SECURITY.md](docs/SECURITY.md)
- [docs/product-specs/mvp-prd.md](docs/product-specs/mvp-prd.md)
