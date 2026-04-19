# Harnetics 开源运营手册 (Open-Source Playbook)

> 写给第一次做开源项目的创始人。从 v0.1.0 发布到社区运营，这份文档覆盖你需要知道的一切。

---

## 0. 开源不是"把代码公开"

开源是一种**协作模式**，不是一个发布动作。代码公开只是第一步，真正的开源意味着：

- 任何人能理解你的项目（README、ARCHITECTURE、设计文档）
- 任何人能运行你的项目（清晰的安装步骤、CI 验证）
- 任何人能贡献你的项目（CONTRIBUTING、Issue/PR 模板、Code Review 文化）
- 任何人能信任你的项目（LICENSE、SECURITY、CHANGELOG、测试覆盖）

本项目已经通过 `008-opensource-readiness` 特性完成了基础设施搭建。以下是后续运营的系统指南。

---

## 1. 发布 v0.1.0

### 1.1 发布前检查清单

```
□ LICENSE 文件存在且正确（Apache 2.0）
□ README 包含项目定位、安装步骤、Quick Start
□ CONTRIBUTING.md 完整且可执行
□ CODE_OF_CONDUCT.md 存在
□ .github/SECURITY.md 存在
□ CHANGELOG.md 记录了 v0.1.0 的所有功能
□ CI 通过（pytest + frontend build）
□ .gitignore 排除了运行时文件（var/、.env、node_modules/）
□ 没有硬编码的 API key、密码或个人路径
□ pyproject.toml 元数据完整（description、license、urls）
```

### 1.2 创建 GitHub Release

```bash
# 打标签
git tag -a v0.1.0 -m "Initial public release"
git push origin v0.1.0

# 在 GitHub 上创建 Release
# 1. 进入 Releases 页面
# 2. 选择 v0.1.0 tag
# 3. 标题：v0.1.0 — Initial Public Release
# 4. 内容：复制 CHANGELOG.md 中 [0.1.0] 的内容
# 5. 勾选 "Set as the latest release"
```

### 1.3 发布公告模板

```markdown
🚀 Harnetics v0.1.0 — 首次公开发布

Harnetics 是一个航天文档对齐工作台，通过文档图谱 + LLM 
将跨部门文档对齐从 2-3 天压缩到半天。

核心功能：
- 文档库：Markdown/YAML 文档入库与章节解析
- 草稿生成：LLM 驱动的带引注对齐草稿
- 影响分析：BFS 变更传播 + AI 向量搜索
- 文档图谱：可视化文档间依赖关系

技术栈：Python 3.12+ / FastAPI / React 18 / SQLite / ChromaDB

👉 GitHub: https://github.com/anthropic-sam/harnetics
📖 文档: https://github.com/anthropic-sam/harnetics/blob/main/docs/
```

---

## 2. 版本管理策略

### 2.1 语义化版本 (SemVer)

```
MAJOR.MINOR.PATCH
  │     │     └─ Bug fixes（向后兼容的 bug 修复）
  │     └─────── New features（向后兼容的新功能）
  └───────────── Breaking changes（不兼容的 API 变更）
```

**Harnetics 版本路线**：

| 版本 | 含义 | 示例 |
|------|------|------|
| 0.1.x | 初始 MVP，API 可能频繁变化 | 0.1.0, 0.1.1, 0.1.2 |
| 0.2.0 | 第二个重要功能里程碑 | 新增 Word/PDF 解析 |
| 0.x.y | Pre-1.0，允许 breaking changes | 每个 minor 可以改 API |
| 1.0.0 | 稳定 API，对外承诺兼容性 | 至少 3 个组织在用 |

**规则**：在 1.0.0 之前，你有权在任何 minor 版本改 API。但每次改动都要在 CHANGELOG 中记录。

### 2.2 CHANGELOG 维护

每次合并到 main 的 PR 都应该在 CHANGELOG 的 `[Unreleased]` 部分追加条目：

```markdown
## [Unreleased]

### Added
- Word document parser (#42)

### Fixed
- Impact analysis cache invalidation on re-import (#38)

### Changed
- Draft API response format (breaking) (#45)
```

发布时，将 `[Unreleased]` 重命名为 `[0.1.1] - 2026-05-01`，再创建新的 `[Unreleased]` 空节。

---

## 3. Issue 与 PR 管理

### 3.1 Issue 标签体系

推荐的标签集（在 GitHub Settings → Labels 中创建）：

| 标签 | 颜色 | 用途 |
|------|------|------|
| `bug` | #d73a4a | 确认的 bug |
| `enhancement` | #a2eeef | 新功能请求 |
| `documentation` | #0075ca | 文档改进 |
| `good first issue` | #7057ff | 适合新贡献者的简单任务 |
| `help wanted` | #008672 | 需要社区帮助 |
| `triage` | #e4e669 | 待分类 |
| `wontfix` | #ffffff | 不会修复 |
| `duplicate` | #cfd3d7 | 重复 issue |
| `priority: high` | #b60205 | 高优先级 |
| `priority: low` | #c5def5 | 低优先级 |
| `area: backend` | #f9d0c4 | 后端相关 |
| `area: frontend` | #bfdadc | 前端相关 |
| `area: docs` | #d4c5f9 | 文档相关 |

### 3.2 Good First Issues

**这是吸引贡献者的第一把钥匙**。始终保持 3-5 个 `good first issue`：

好的 first issue 特征：
- 范围小、明确（一个文件、一个函数）
- 不需要理解整体架构
- 有清晰的验收标准
- 标注了需要修改的文件路径

示例：
```markdown
Title: Add validation for empty document title on upload

Area: Backend (src/harnetics/parsers/)
File: src/harnetics/parsers/markdown_parser.py

Description: When uploading a Markdown document without a title (no # heading),
the parser silently creates a document with empty title. Should raise a 
ValidationError with message "Document must have a title (# heading)".

Acceptance: 
- [ ] Raise ValidationError when title is empty
- [ ] Add test in tests/test_importer.py
- [ ] Update AGENTS.md if needed
```

### 3.3 PR Review 流程

**作为唯一维护者的策略**：

1. **72 小时内回应所有 PR**——即使只是 "Thanks, I'll review this weekend"
2. **CI 必须绿灯**才开始人工 review
3. **Review 聚焦三件事**：
   - 是否解决了 issue 描述的问题？
   - 是否有测试覆盖？
   - 是否遵循了 CONTRIBUTING 中的编码规范？
4. **Squash merge**——保持 main 的 commit 历史干净

---

## 4. 社区建设

### 4.1 沟通渠道（推荐优先级）

| 渠道 | 用途 | 何时启用 |
|------|------|---------|
| GitHub Issues | Bug 报告、功能请求 | Day 0 |
| GitHub Discussions | 问答、想法讨论、展示 | Day 0（启用 Discussions 功能） |
| Discord/Slack | 实时聊天 | 有 10+ 活跃贡献者时 |
| 邮件列表 | 重大公告 | 有 50+ star 时 |

**Day 0 行动**：在 GitHub repo 的 Settings → Features 中启用 Discussions。创建以下分类：
- 📣 Announcements（维护者公告）
- 💡 Ideas（功能建议讨论）
- 🙋 Q&A（使用问题）
- 🎉 Show and Tell（用户展示自己的使用场景）

### 4.2 README 中的社区入口

确保 README 底部有清晰的社区入口：

```markdown
## Community

- 💬 [Discussions](https://github.com/anthropic-sam/harnetics/discussions) — Ask questions, share ideas
- 🐛 [Issues](https://github.com/anthropic-sam/harnetics/issues) — Report bugs, request features
- 📖 [Contributing Guide](CONTRIBUTING.md) — How to contribute
```

### 4.3 贡献者激励

- **在 CHANGELOG 中 @ 贡献者**：`- Fix impact cache (#38) by @username`
- **维护 All Contributors 表格**：使用 [all-contributors](https://allcontributors.org/) bot
- **及时回应**：速度比完美更重要。一句 "Good catch, I'll look into this" 比沉默三天强 100 倍

---

## 5. 项目推广策略

### 5.1 发布渠道

| 渠道 | 适合时机 | 注意事项 |
|------|---------|---------|
| Hacker News (Show HN) | v0.1.0 首发 | 标题用英文，突出"aerospace"+"document alignment" |
| Reddit r/Python | 每个 minor 版本 | 展示技术实现细节 |
| Reddit r/aerospace | v0.1.0 + 重大功能 | 聚焦领域价值，不是技术栈 |
| Dev.to / Hashnode | 技术博文 | 写"如何用 X 解决 Y"类文章 |
| Twitter/X | 持续更新 | 短视频 demo 效果最好 |
| 微信公众号/知乎 | 中文社区传播 | 航天行业精准用户在这里 |
| Product Hunt | 有 Web demo 时 | 需要可公开访问的在线版本 |

### 5.2 Show HN 帖子模板

```
Show HN: Harnetics – Open-source aerospace document alignment workbench

Aerospace engineers spend 40-60% of their time writing and reviewing documents. 
The hardest part isn't writing — it's alignment: ensuring each document is 
consistent with documents from other departments and system levels.

Harnetics uses a document graph + LLM to compress this from 2-3 days to half a day.

Core features:
- Document graph with traceability edges (traces_to, references, derived_from...)
- LLM-powered draft generation with citation backfill
- BFS-based change impact analysis
- React SPA with document visualization

Tech: Python/FastAPI + React/TypeScript + SQLite + ChromaDB + OpenAI-compatible LLM

Local-first: all data stays on your machine. Works offline with Ollama.

GitHub: https://github.com/anthropic-sam/harnetics
```

### 5.3 技术博文选题建议

1. **"Why Document Alignment is the Real Pain in Aerospace Engineering"** — 领域洞察，吸引行业注意
2. **"Building a Document Graph with SQLite: No Neo4j Needed"** — 技术实现，吸引开发者
3. **"LLM-Powered Draft Generation with Citation Backfill"** — AI 应用，吸引 LLM 社区
4. **"From Interview to MVP: How We Validated an Aerospace SaaS in 2 Weeks"** — 创业故事，吸引产品人

---

## 6. 维护节奏

### 6.1 作为 Solo Maintainer 的可持续节奏

| 活动 | 频率 | 时间投入 |
|------|------|---------|
| 回复 Issues/PR | 每 1-2 天 | 15-30 min |
| Review PR | 每周 | 1-2 hr |
| Bug fix 发布 | 每 1-2 周 | 2-4 hr |
| Feature 发布 | 每 1-2 月 | 集中 1-2 天 |
| 写博文/推广 | 每月 1 篇 | 2-4 hr |
| 整理 Good First Issues | 每 2 周 | 30 min |

**关键原则：可持续性 > 速度**。宁可每周稳定投入 5 小时，也不要一周 40 小时然后消失三个月。

### 6.2 倦怠预防

- **设定清晰的边界**：README 写明维护者时区和回复 SLA（如 "维护者在 UTC+8，一般 48 小时内回复"）
- **说 No 的权利**：不是所有 feature request 都要接受。礼貌地说 "Thanks for the suggestion. This is out of scope for now, but feel free to implement it as a plugin" 是完全正当的
- **寻找 co-maintainer**：当项目有 5+ 活跃贡献者时，邀请最活跃的人成为 collaborator

---

## 7. 安全与法律

### 7.1 许可证合规

Apache 2.0 意味着：
- ✅ 任何人可以商业使用
- ✅ 任何人可以修改和分发
- ✅ 提供专利授权
- ⚠️ 修改后的文件必须标注已修改
- ⚠️ 必须保留原始版权声明

**检查依赖许可证**：
```bash
# Python 依赖
pip-licenses --format=table

# Node.js 依赖
npx license-checker --summary
```

确保所有依赖的许可证与 Apache 2.0 兼容（MIT、BSD、ISC、Apache 2.0 都兼容；GPL 不兼容）。

### 7.2 安全响应流程

收到安全报告后：
1. **48 小时内确认收到**
2. **7 天内给出修复计划**
3. **修复后发布 patch 版本**
4. **在 CHANGELOG 和 Release Notes 中标注安全修复**
5. **可选：申请 CVE 编号（如果影响范围大）**

### 7.3 敏感数据检查

发布前务必检查：
```bash
# 搜索可能的硬编码密钥
grep -rn "sk-\|api_key\|password\|secret" --include="*.py" --include="*.ts" --include="*.yml"

# 检查 .env 是否被 gitignore
git check-ignore .env
```

---

## 8. 成长路径

### 8.1 里程碑规划

| 里程碑 | 指标 | 解锁的能力 |
|--------|------|-----------|
| **v0.1.0** | 首次发布 | 公开可用、可贡献 |
| **10 Stars** | 早期关注 | 值得写第一篇博文 |
| **First External PR** | 首个外部贡献 | 证明项目可贡献 |
| **50 Stars** | 稳定关注 | 可以申请 awesome-list 收录 |
| **5 Contributors** | 社区形成 | 考虑邀请 co-maintainer |
| **v0.5.0** | 功能成熟 | 可以对外 demo |
| **100 Stars** | 行业关注 | 可以在会议上 talk |
| **v1.0.0** | API 稳定 | 可以对外承诺兼容性 |

### 8.2 推荐学习资源

| 资源 | 类型 | 为什么推荐 |
|------|------|-----------|
| [Open Source Guides](https://opensource.guide/) | 官方指南 | GitHub 出品，覆盖最全 |
| [The Architecture of Open Source Applications](https://aosabook.org/) | 书 | 理解大型开源项目的架构决策 |
| [Producing Open Source Software](https://producingoss.com/) | 书（免费在线） | Karl Fogel 的经典，社区管理圣经 |
| [Maintainer Month](https://github.blog/open-source/maintainers/) | 博客 | GitHub 对维护者的支持和建议 |
| [Conventional Commits](https://www.conventionalcommits.org/) | 规范 | commit 信息标准化 |
| [Keep a Changelog](https://keepachangelog.com/) | 规范 | CHANGELOG 格式标准 |
| [Choose a License](https://choosealicense.com/) | 工具 | 快速理解不同许可证 |

### 8.3 进阶工具

| 工具 | 用途 | 何时引入 |
|------|------|---------|
| [Codecov](https://codecov.io/) | 测试覆盖率报告 | 有 10+ tests 时 |
| [Renovate](https://docs.renovatebot.com/) / Dependabot | 自动依赖更新 | Day 0 可开 |
| [All Contributors](https://allcontributors.org/) | 贡献者表格 | 有第一个外部贡献时 |
| [Release Please](https://github.com/googleapis/release-please) | 自动化版本发布 | 每月有 2+ releases 时 |
| [ReadTheDocs](https://readthedocs.org/) | 文档托管 | 文档超过 10 页时 |
| [GitHub Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects) | 项目看板 | 有 20+ open issues 时 |

---

## 9. 常见陷阱

### ❌ 陷阱 1：追求完美再发布
**现实**：v0.1.0 不需要完美。有人用的半成品比无人用的完成品有价值 1000 倍。发布后根据真实反馈迭代。

### ❌ 陷阱 2：忽略第一个贡献者
**现实**：第一个外部 PR 是项目最重要的里程碑之一。即使代码质量一般，也要花时间指导和合并。这个人可能成为你的 co-maintainer。

### ❌ 陷阱 3：不回复 Issue
**现实**：沉默是开源项目的死刑。一句 "I see this, will look into it this week" 比完美的技术分析更有价值。回复速度决定社区温度。

### ❌ 陷阱 4：把所有请求都接下来
**现实**：学会说 "This is a great idea, but it's out of scope for this project"。聚焦比发散重要。

### ❌ 陷阱 5：没有 CI 就接受 PR
**现实**：没有自动化测试验证的 PR merge 是定时炸弹。CI 是你唯一可以信任的审查员。

### ❌ 陷阱 6：不写 CHANGELOG
**现实**：用户不会读你的 git log。CHANGELOG 是用户理解"升级会发生什么"的唯一途径。

---

## 10. 第一周行动清单

```
Day 1: 发布 v0.1.0
  □ 检查所有文件就位（LICENSE, README, CONTRIBUTING, etc.）
  □ 创建 v0.1.0 tag 和 GitHub Release
  □ 启用 GitHub Discussions
  □ 设置 Issue 标签体系
  □ 创建 3-5 个 good first issue

Day 2-3: 推广
  □ 发布 Show HN 帖子
  □ 发布到 Reddit r/Python 和 r/aerospace
  □ 发布中文社区帖子（知乎/微信）
  □ 在 Twitter/X 上公告

Day 4-7: 响应
  □ 回复所有 Issue 和 Discussion
  □ Review 收到的 PR（如果有）
  □ 根据反馈更新 README 中不清晰的部分
  □ 写第一篇技术博文（趁热度还在）
```

---

> **最后一条忠告**：开源是一场马拉松，不是冲刺。保持稳定的节奏，珍惜每一个贡献者，享受构建过程。你在解决的是一个真实的问题——这是最好的起点。
