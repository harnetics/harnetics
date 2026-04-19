# Harnetics

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 20+](https://img.shields.io/badge/node-20+-green.svg)](https://nodejs.org/)

**商业航天文档对齐工作台** —— 基于文档图谱与大语言模型（LLM），实现跨部门可追溯性、对齐草稿生成与变更影响分析。

航天工程师每天花 40–60% 的时间在文档编写和评审上。最耗时的不是"写"，而是"对齐"——确保一份文档与多部门、多层级的其他文档保持一致。Harnetics 通过文档图谱 + LLM 将这个过程从 2–3 天压缩到半天。

> English documentation: [README.md](README.md)

---

## 核心功能

| 模块 | 说明 |
|------|------|
| **文档库** | 上传并浏览 Markdown/YAML 文档，自动解析章节与 ICD 参数 |
| **草稿生成** | LLM 驱动的对齐草稿，含引注回填、冲突检测与质量门评估 |
| **影响分析** | BFS 下游变更传播，双模式（AI 向量检索 + 启发式分析） |
| **文档图谱** | 可视化文档间引用、派生、约束关系 |
| **仪表盘** | 文档数量、草稿状态、陈旧引用、LLM 状态概览 |

## 系统架构

```
文档入库 (Markdown/YAML)
  → 解析 & 图谱索引 (SQLite + ChromaDB)
    → LLM 草稿生成 (OpenAI-compatible)
      → 质量门评估 (EA/EB/ED)
        → 影响分析 (BFS + 向量检索)
          → API / React SPA
```

- **后端**：Python 3.12+ · FastAPI · SQLite · ChromaDB · OpenAI SDK
- **前端**：React 18 · TypeScript 5.7 · Vite 6 · Tailwind CSS v4 · shadcn/ui
- **LLM**：OpenAI-compatible 路由，显式支持本地 Ollama 回退
- **设计理念**：本地优先——所有数据默认留存在本机

## 快速开始

### 环境要求

| 工具 | 版本 | 安装方式 |
|------|------|---------|
| Python | ≥ 3.12 | [python.org](https://www.python.org/downloads/) |
| uv | 最新版 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js | ≥ 20 | [nodejs.org](https://nodejs.org/) |

### 安装

```bash
git clone https://github.com/anthropic-sam/harnetics.git
cd harnetics
uv sync --dev
cd frontend && npm install && cd ..
```

### 配置 LLM

**方案 A：本地 Ollama**（离线，无需 API Key）

```bash
export HARNETICS_LLM_MODEL="gemma3:12b"
export HARNETICS_LLM_BASE_URL="http://localhost:11434"
ollama pull gemma3:12b && ollama serve
```

**方案 B：云端 OpenAI-compatible**（任意服务商）

```bash
export HARNETICS_LLM_MODEL="gpt-4o"
export OPENAI_API_KEY="sk-..."
# 可选：自定义第三方网关地址
# export HARNETICS_LLM_BASE_URL="https://your-gateway/v1"
```

完整配置项见 [.env.example](.env.example)。

### 初始化并启动

```bash
# 导入样本航天文档，初始化图谱数据库
uv run python -m harnetics.cli.main init --reset
uv run python -m harnetics.cli.main ingest fixtures/

# 启动服务器
uv run python -m harnetics.cli.main serve --reload
```

打开 `http://localhost:8000`，即可看到加载了样本文档的仪表盘。

前端热更新开发模式：

```bash
cd frontend && npm run dev    # → http://localhost:5173
```

### 冒烟测试

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/dashboard/stats
curl http://localhost:8000/api/documents
```

## API 路由

| 路由 | 说明 |
|------|------|
| `GET /health` | 健康检查 |
| `GET /api/dashboard/stats` | 仪表盘统计数据 |
| `GET /api/documents` | 文档列表 |
| `GET /api/documents/{doc_id}` | 文档详情（含章节） |
| `POST /api/draft/generate` | 生成对齐草稿 |
| `GET /api/draft/{draft_id}` | 查看草稿与引注 |
| `POST /api/impact/analyze` | 触发影响分析 |
| `GET /api/impact` | 影响分析报告列表 |
| `GET /api/impact/{report_id}` | 影响分析报告详情 |
| `GET /api/graph/edges` | 原始图谱边数据 |
| `GET /api/status` | LLM/Embedding 配置状态 |

## 测试

```bash
# 后端测试
uv run pytest tests/ -q

# 前端构建验证
cd frontend && npm run build
```

## Docker

```bash
docker compose up
# → http://localhost:8000
```

`docker-compose.yml` 包含带 GPU 直通的可选 Ollama 服务。

## 项目结构

```
harnetics/
├── src/harnetics/         # Python 后端
│   ├── api/               #   FastAPI 应用工厂 + 路由 + SPA 托管
│   │   └── routes/        #     documents / draft / impact / graph / status / evaluate
│   ├── cli/               #   typer CLI（init / ingest / serve）
│   ├── engine/            #   草稿生成、冲突检测、影响分析核心引擎
│   ├── evaluators/        #   质量门评估器（EA/EB/ED）
│   ├── graph/             #   SQLite 图谱存储 + ChromaDB 向量索引
│   ├── llm/               #   OpenAI-compatible 客户端、路由归一化、诊断
│   ├── models/            #   领域 dataclass（document / icd / draft / impact）
│   ├── parsers/           #   Markdown / YAML / ICD 解析器
│   └── config.py          #   Settings + .env 加载器
├── frontend/              # React 18 SPA
│   └── src/
│       ├── pages/         #   路由页面
│       ├── components/    #   共享 UI 组件
│       ├── lib/           #   API 客户端 + 工具函数
│       └── types/         #   TypeScript 领域类型
├── fixtures/              # 航天领域样本文档
├── tests/                 # pytest 测试套件
├── docs/                  # 设计文档、规格、参考资料
├── specs/                 # 特性规格存档（Spec Kit）
└── var/                   # 运行时数据（SQLite、ChromaDB）— 已 gitignore
```

## 文档导航

| 文档 | 说明 |
|------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 系统结构、数据流、模块边界 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献指南 |
| [CHANGELOG.md](CHANGELOG.md) | 版本发布历史 |
| [docs/design-docs/aerospace-mvp-v3.md](docs/design-docs/aerospace-mvp-v3.md) | 核心设计叙事——Harnetics 的"为什么" |
| [docs/design-docs/core-beliefs.md](docs/design-docs/core-beliefs.md) | 设计原则 |
| [docs/PRODUCT_SENSE.md](docs/PRODUCT_SENSE.md) | 用户画像与价值主张 |
| [docs/opensource-playbook.md](docs/opensource-playbook.md) | 开源运营手册（首次开源创始人参考指南） |
| [docs/SECURITY.md](docs/SECURITY.md) | 安全设计说明 |

## 贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解：

- 开发环境搭建
- 分支命名与 commit 规范
- Pull Request 流程
- 编码规范

## 许可证

本项目采用 Apache License 2.0 授权——详见 [LICENSE](LICENSE)。
