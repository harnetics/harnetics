# tests/
> L2 | 父级: /AGENTS.md

成员清单
conftest.py: pytest 共享 fixture，提供临时数据库路径与仓库根路径。
test_importer.py: 导入服务契约测试，锁定受控 Markdown/YAML 与元数据校验。
test_app.py: 健康检查冒烟测试，锁定最小可运行骨架。
test_repository.py: SQLite 仓储回归测试，锁定记录与持久化边界。

法则: 测试只描述可观察行为，不泄露实现细节。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
