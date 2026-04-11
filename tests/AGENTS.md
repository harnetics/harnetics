# tests/
> L2 | 父级: /AGENTS.md

成员清单
conftest.py: pytest 共享 fixture，提供临时数据库路径、catalog/draft app 夹具、假 LLM 与导入场景。
test_importer.py: 导入服务契约测试，锁定受控 Markdown/YAML 与元数据校验。
test_app.py: 健康检查冒烟测试，锁定最小可运行骨架，并验证 .env 中的 LLM/Embedding 配置可被 get_settings() 正确加载。
test_llm_client.py: LLM 配置契约测试，锁定 Ollama 裸模型名归一化、目标模型存在性判断、云端 provider availability 错误说明，以及 LiteLLM debug 开关的单次启用语义。
test_repository.py: SQLite 仓储回归测试，锁定记录与持久化边界。
test_catalog_routes.py: 文档目录路由测试，锁定上传、列表筛选与详情渲染。
test_retrieval.py: 检索规划测试，锁定模板选择与候选来源排序。
test_drafts.py: 草稿工作流测试，锁定生成、告警、编辑与导出闭环。
test_graph_store.py: 图谱存储与索引回归测试，锁定 graph schema、section 入库、目录导入边界，以及 bare OpenAI embedding 模型的云端路由判定。
test_e2e_mvp_scenario.py: 图谱栈端到端场景测试，覆盖上传、草稿、评估、影响分析、图谱与仪表盘契约；新增草稿路由 source_report_id 透传、文档搜索关键词降级与 richer status 断言。
test_env_routing.py: 环境配置回归测试，使用本地 fake OpenAI-compatible provider 验证 bare LLM/Embedding 模型名经 .env + base_url 路由后可真实完成 completion 和 embedding，并锁定草稿落库时记录实际模型路由。

法则: 测试只锁定可观察行为，优先覆盖真实工作流而非内部步骤。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
