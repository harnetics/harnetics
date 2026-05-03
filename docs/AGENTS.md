# docs/
> L2 | 父级: ../AGENTS.md

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

成员清单
AGENTS.md: `docs/` 总导航，定义公开文档与本地记忆材料的边界与阅读路径。
ARCHITECTURE.md: 对外公开的系统总图，说明运行时主链、模块边界与演进方向。
CHANGELOG.md: 对外公开的版本变更记录。
CODE_OF_CONDUCT.md: 对外公开的社区行为准则。
CONTRIBUTING.md: 对外公开的贡献指南。
MEMORY.md: 跨会话核心记忆，收敛当前项目阶段、活跃约束与已验证 workflow。
DESIGN.md: 设计入口页，连接设计原则、架构叙事与深入文档。
FRONTEND.md: 前端与浏览器交互面的现状、边界与未来实现假设。
daily/: 开发记忆日志目录，按日期沉淀当次会话中的决策、经验与后续 retain 项。
PLANS.md: 执行计划入口，区分 active、completed 与技术债。
PRODUCT_SENSE.md: 用户价值、产品边界与关键场景说明。
QUALITY_SCORE.md: 当前质量状态的定性打分与短板记录。
RELIABILITY.md: 运行可靠性、校验点与恢复路径说明。
SECURITY.md: 本地部署、安全边界与数据处理约束。
design-docs/: 设计原则、领域调研、架构叙事与长期稳定判断。
exec-plans/: 执行中的计划、已完成计划与技术债跟踪。
generated/: 生成物与结构化工件的落点。
product-specs/: 产品规格、用户流程与 PRD。
references/: 外部参考、工具说明与 LLM 辅助材料。
superpowers/: 通过技能流程产出的工作文档与阶段性设计 spec。

法则
- `docs/` 只保留当前有效文档；历史材料若仍需存在，必须明确标注归档属性。
- 规格、设计、计划三类文档分层放置，不允许再次回流到根目录竞争入口。
- `daily/` 只记录高价值决策摘要，不贴完整对话，不复制大段代码。
- `docs/` 根层承载公开文档；`bank/` 与 `daily/` 保持本地记忆属性并由 `.gitignore` 控制。

变更日志
- 2026-04-11: 新增 `daily/` 目录，开始按日沉淀开发记忆
- 2026-04-19: 新增 `ARCHITECTURE.md`、`CHANGELOG.md`、`CODE_OF_CONDUCT.md`、`CONTRIBUTING.md` 到 `docs/` 根层，公开文档与本地记忆材料分层
- 2026-04-30: 新增 `MEMORY.md`，把四步比对审查与前后端双模式状态机沉淀为跨会话入口记忆
