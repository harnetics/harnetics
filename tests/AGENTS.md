# tests/
> L2 | 父级: /AGENTS.md

成员清单
conftest.py: pytest 共享 fixture，提供临时数据库路径、catalog/draft app 夹具、假 LLM 与导入场景。
test_importer.py: 导入服务契约测试，锁定受控 Markdown/YAML 与元数据校验。
test_app.py: 健康检查冒烟测试，锁定最小可运行骨架。
test_repository.py: SQLite 仓储回归测试，锁定记录与持久化边界。
test_catalog_routes.py: 文档目录路由测试，锁定上传、列表筛选与详情渲染。
test_retrieval.py: 检索规划测试，锁定模板选择与候选来源排序。
test_drafts.py: 草稿工作流测试，锁定生成、告警、编辑与导出闭环。

法则: 测试只锁定可观察行为，优先覆盖真实工作流而非内部步骤。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
