# 贡献指南

感谢你关注 Harnetics！本文档说明如何为项目提交改进、修复问题与参与协作。

## 目录

- [行为准则](#行为准则)
- [快速开始](#快速开始)
- [开发环境](#开发环境)
- [如何修改](#如何修改)
- [Pull Request 流程](#pull-request-流程)
- [编码规范](#编码规范)
- [问题反馈](#问题反馈)
- [如何讨论](#如何讨论)

## 行为准则

本项目遵循 [Contributor Covenant 行为准则](CODE_OF_CONDUCT.md)。参与本项目即表示你同意遵守该准则。

## 快速开始

1. 在 GitHub 上 **Fork** 本仓库
2. 将你的 Fork **克隆**到本地：
   ```bash
   git clone https://github.com/<your-username>/harnetics.git
   cd harnetics
   ```
3. 添加官方仓库为 **upstream**：
   ```bash
   git remote add upstream https://github.com/harnetics/harnetics.git
   ```

## 开发环境

### 前置要求

| 工具 | 版本 | 用途 |
|------|------|------|
| Python | ≥ 3.12 | 后端运行时 |
| uv | 最新版 | Python 包管理器 |
| Node.js | ≥ 20 | 前端构建 |
| npm | 最新版 | 前端包管理器 |

### 后端依赖

```bash
uv sync --dev
```

### 前端依赖

```bash
cd frontend
npm install
cd ..
```

### 运行应用

```bash
# 启动后端（同时托管 API 与 SPA）
uv run uvicorn harnetics:create_app --factory --reload --port 8000

# 启动前端开发服务器（另开一个终端，用于热更新）
cd frontend && npm run dev
```

### 运行测试

```bash
# 后端测试
uv run pytest -q

# 前端构建检查
cd frontend && npm run build
```

### 仅后端 / 仅前端开发

- **仅后端**：可以跳过 `npm install`。API 可直接通过 `http://localhost:8000/api/` 访问。
- **仅前端**：在 `frontend/` 下运行 `npm run dev`。Vite 会代理 API 请求到后端，请确保后端运行在 8000 端口。

## 如何修改

### 分支命名

从 `main` 创建功能分支：

```bash
git checkout main
git pull upstream main
git checkout -b <type>/<short-description>
```

分支类型建议：
- `feat/` —— 新功能或增强
- `fix/` —— Bug 修复
- `docs/` —— 文档变更
- `refactor/` —— 重构（不改变行为）
- `test/` —— 新增或修改测试
- `ci/` —— CI/CD 相关修改

示例：`feat/yaml-icd-parser`、`fix/impact-analysis-cache`、`docs/api-reference`

### Commit 信息

请遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

```text
<type>(<scope>): <short summary>

<optional body>
```

可用类型：`feat`、`fix`、`docs`、`refactor`、`test`、`ci`、`chore`

示例：
```text
feat(engine): add batch LLM judgement for impact analysis
fix(graph): prevent duplicate edges on re-import
docs(readme): add architecture diagram
```

## Pull Request 流程

1. **同步最新 `main`**：
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```
2. **确保测试通过**：
   ```bash
   uv run pytest -q
   cd frontend && npm run build
   ```
3. **创建 PR** 到 `main`
4. **填写 PR 模板**，说明改了什么、为什么改、如何验证
5. **等待 CI** 完成，所有检查通过后再进入评审
6. **处理评审反馈**，必要时继续 push，最终在合并时 squash

### 什么样的 PR 更容易被接受

- **小而聚焦**：一个 PR 只做一类逻辑变更
- **测试齐全**：如果行为发生变化，应补充或更新测试
- **文档同步**：新增功能或修改使用方式时，请同步更新相关文档
- **AGENTS.md 同步**：如果新增 / 删除 / 移动文件，请同步更新最近的 AGENTS.md

## 编码规范

### Python（后端）

- **风格**：遵循现有代码风格，避免过度抽象
- **函数**：尽量控制在 20 行以内；仅在真正复用时再提取
- **文件**：尽量控制在 800 行以内
- **目录**：单层目录尽量不超过 8 个文件
- **注释**：使用中文 + ASCII 风格分块注释，与现有代码库保持一致
- **类型**：函数签名尽量补齐 Python 类型标注
- **测试**：使用 pytest；测试文件放在 `tests/` 下，并尽量镜像 `src/` 结构

### TypeScript（前端）

- **组件**：优先使用 shadcn/ui + Tailwind CSS v4
- **样式**：不新增自定义 CSS，统一通过 Tailwind utility 完成
- **状态管理**：优先 React hooks；除非有充分理由，不引入全局状态库
- **类型**：保持严格 TypeScript，避免使用 `any` 逃逸

### 分形文档协议（GEB）

本项目使用分形文档协议：
- **L1**（`/AGENTS.md`）：项目级目录地图
- **L2**（`/{module}/AGENTS.md`）：模块级成员与接口说明
- **L3**（文件头注释）：`[INPUT] / [OUTPUT] / [POS] / [PROTOCOL]` 契约

当你新增、删除或移动文件时，请同步更新对应的 AGENTS.md。详情见 [AGENTS.md](../AGENTS.md)。

## 问题反馈

请使用 [Bug Report](https://github.com/harnetics/harnetics/issues/new?template=bug_report.yml) 模板，并尽量提供：

- 复现步骤
- 预期行为与实际行为
- 环境信息（OS、Python 版本、Node 版本）
- 相关日志或截图

## 如何讨论

- 功能方向、产品想法、使用疑问：优先去 [Discussions](https://github.com/harnetics/harnetics/discussions)
- 明确缺陷或功能请求：请提交到 [Issues](https://github.com/harnetics/harnetics/issues)

---

感谢你一起把航天文档对齐这件事做得更好。🚀
