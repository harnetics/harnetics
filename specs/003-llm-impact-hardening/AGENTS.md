# 003-llm-impact-hardening/
> L2 | 父级: ../AGENTS.md

成员清单
AGENTS.md: 当前 bugfix 特性的局部地图，定义文档闭环边界。
spec.md: 需求规格，定义 LLM 连接稳健性与影响章节定位的用户故事、约束与成功标准。
plan.md: 实施计划，给出代码改动面、技术决策与验证边界。
research.md: 关键技术决策与取舍记录。
data-model.md: 本特性的配置解析、引用信号与章节定位数据模型。
quickstart.md: 本地验证流程与复现/回归步骤。
tasks.md: 依赖顺序明确的实现任务列表。
checklists/review.md: 规格质量检查单，验证需求是否完整、清晰、可测。
contracts/api-contracts.md: `/api/draft/generate`、`/api/status`、`/api/impact/analyze` 的行为契约。

目录树
- checklists/review.md：需求质量检查单
- contracts/api-contracts.md：API 行为契约

法则
- 文档先于代码；实现完成后必须回写 `tasks.md` 状态
- 契约只描述外部可观察行为，不复制实现细节
- 若本特性新增文件，先补齐本文件成员清单

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md