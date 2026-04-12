# 005-openai-compatible-llm-client/
> L2 | 父级: ../AGENTS.md

成员清单
AGENTS.md: 当前特性的局部地图，定义 OpenAI-compatible AI 路由收敛的文档边界。
spec.md: 需求规格，定义远端 completion/embedding 调用切换到 OpenAI-compatible 语义后的用户故事、范围与成功标准。
checklists/requirements.md: 规格质量检查单，验证需求完整、清晰、可测。
plan.md: 实施计划，给出技术决策、代码改动面与验证边界。
research.md: 关键技术决策与方案取舍记录。
data-model.md: 当前特性的运行时路由、诊断快照与错误上下文数据模型。
quickstart.md: 本地验证远端网关、本地 fallback 与 targeted pytest 的操作步骤。
tasks.md: 依赖顺序明确的实现任务列表。
contracts/api-contracts.md: 草稿、影响分析、embedding 与状态端点在 OpenAI-compatible 路由下的行为契约。

目录树
- checklists/requirements.md：需求质量检查单
- contracts/api-contracts.md：API 行为契约

法则
- 文档先于代码；新增 plan/tasks/contracts 后立即回写本文件
- 规格只描述外部可观察行为与用户价值，不泄漏代码级实现细节
- 若本特性新增文件，先补齐本文件成员清单

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md