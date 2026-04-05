<!--
[INPUT]: 依赖根目录模块边界、docs/ 真相源、fixtures/ 样本文档库
[OUTPUT]: 对外提供当前系统结构、数据流与演进方向说明
[POS]: 项目根目录的架构总图，被 AGENTS.md 与 docs/design-docs/index.md 引用
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->

# Harnetics 架构总图

## 当前形态

仓库现在已经有一个最小可运行闭环：

- `fixtures/`：机器相原始语料，提供受控需求、设计、模板与测试样本。
- `src/harnetics/`：运行时主干，负责导入、检索、生成、校验与 Web 工作台。
- `docs/`：语义相项目记忆，记录规格、计划、生成工件与治理约束。

## 核心数据流

1. `ImportService` 从 `fixtures/` 或上传文件读入受控 Markdown/YAML，并把文档树持久化到 SQLite。
2. `RetrievalPlanner` 从 `documents`/`templates` 中选出模板和候选来源，形成草稿计划。
3. `DraftService` 拼装 prompt，经 `LocalLlmClient` 生成 Markdown，再将 `drafts`、`citations`、`generation_runs` 落库。
4. `DraftValidator` 基于引注、模板必填章节和已知过期样本写入 `validation_issues`。
5. `web/routes.py` 暴露 `/documents/*` 与 `/drafts/*`，形成导入、浏览、生成、编辑和导出闭环。
6. `docs/` 继续沉淀规格、执行计划和 schema 说明，保持语义相与机器相同构。

## 模块边界

| 模块 | 当前职责 | 演进方向 |
| --- | --- | --- |
| `src/harnetics/importer.py` | 受控导入与模板持久化 | 支持更多输入格式与追溯抽取 |
| `src/harnetics/retrieval.py` | 候选来源与模板排序 | 接入更细粒度 section-ranking |
| `src/harnetics/drafts.py` | prompt 组装、生成落库与状态更新 | 引入更强约束与多轮生成 |
| `src/harnetics/validation.py` | 阻断/警告规则 | 扩展版本比对与参数一致性检查 |
| `src/harnetics/web/` | catalog 与草稿工作台 HTTP 入口 | 增加更细的编辑/审阅交互 |
| `fixtures/` | 航天领域受控样本库 | 持续补充评测和回归语料 |
| `docs/` | 项目决策、计划与生成工件 | 长期保持为人类与 Agent 的导航层 |

## 运行时原则

- `Repository` 仍是唯一 SQLite 边界，服务层不直接写 SQL。
- 检索、生成、校验分层明确，Web 层只做请求编排与模板渲染。
- 当前实现优先最小闭环：导入文档 -> 选择候选 -> 生成带引注草稿 -> 标记告警 -> Web 编辑与导出。
- 后续演进应继续消除特殊分支，而不是把复杂性堆进路由或模板。
