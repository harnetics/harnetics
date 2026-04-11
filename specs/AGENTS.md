# specs/
> L2 | 父级: /AGENTS.md

成员清单
AGENTS.md: `specs/` 的局部地图，约束每个顺序特性的闭环产物组织。
001-aerospace-doc-alignment/: 图谱后端 MVP 的首个 Spec Kit 特性，含对齐工作台的初始规格与实现计划。
002-react-frontend-replacement/: React/Vite SPA 替换 Jinja2/HTMX 的前端迁移特性。
003-llm-impact-hardening/: LLM 调用稳健性与影响分析章节定位修复特性。

目录树
- 001-aerospace-doc-alignment/：后端 MVP 特性闭环
- 002-react-frontend-replacement/：SPA 前端迁移闭环
- 003-llm-impact-hardening/：LLM + impact bugfix 闭环

法则
- `specs/<feature>/` 必须同时维护 `spec.md`、`plan.md`、`tasks.md` 与设计副产物
- 新增 feature 目录时，先更新本文件，再落 feature 内部 `AGENTS.md`
- `checklists/` 只放需求质量检查项，`contracts/` 只放行为契约，不混写实现细节

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md