<!--
[INPUT]: 依赖根目录模块边界、docs/ 真相源、fixtures/ 样本文档库
[OUTPUT]: 对外提供当前系统结构、数据流与演进方向说明
[POS]: 项目根目录的架构总图，被 AGENTS.md 与 docs/design-docs/index.md 引用
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->

# Harnetics 架构总图

## 当前形态

仓库当前还是一个文档驱动的产品孵化体，而不是可运行应用。
真正存在的系统只有两层：

- `fixtures/`：机器相的原始语料，包含需求、设计、ICD、质量与测试样本。
- `docs/`：语义相的项目记忆，承载产品定义、设计原则、执行计划与治理约束。

## 核心数据流

1. 领域样本文档从 `fixtures/` 进入。
2. 产品与架构判断在 `docs/product-specs/` 和 `docs/design-docs/` 沉淀。
3. 后续实现计划进入 `docs/exec-plans/active/`，完成后转入 `docs/exec-plans/completed/`。
4. 一旦未来出现解析器、索引器、图谱或生成服务，其结构应从这两类真相源直接长出，而不是反向改写需求。

## 模块边界

| 模块 | 当前职责 | 未来演进 |
| --- | --- | --- |
| `fixtures/requirements` | 系统级需求样本 | 需求解析、追溯抽取输入 |
| `fixtures/design` | 总体与分系统设计样本 | 设计依赖图、引用解析输入 |
| `fixtures/icd` | 接口参数权威样本 | 参数一致性与影响分析输入 |
| `fixtures/quality` | 质量/FMEA 样本 | 风险识别与评估输入 |
| `fixtures/templates` | 模板样本 | 草稿生成骨架输入 |
| `fixtures/test_plans` | 测试大纲样本 | 检索、对齐、生成与评测输入 |
| `docs/` | 项目决策与运行规则 | 长期保持为人类与 Agent 的导航层 |

## 现阶段判断

- 现在最缺的不是更多目录，而是第一份真实执行计划。
- 当前没有代码运行面，因此 `docs/generated/db-schema.md` 记录的是目标数据模型，不是假装存在的数据库。
- 所有未来代码目录都应服务于一个核心闭环：导入文档 -> 建立追溯关系 -> 生成带引注草稿 -> 发现版本冲突。
