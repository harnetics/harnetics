# exec-plans/
> L2 | 父级: ../AGENTS.md

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

成员清单
AGENTS.md: `exec-plans/` 的局部地图，定义计划生命周期与归档规则。
active/: 正在执行的计划，必须保持最新状态与下一步。
completed/: 已完成计划的归档区，保留决策与验收结果。
tech-debt-tracker.md: 当前技术债清单，记录症状、影响与偿还动作。

法则
- 计划一旦开始执行，先进入 `active/`；验证完成后再移入 `completed/`。
- 技术债只记录还想处理且尚未处理的问题，不写历史抱怨。
