# tests/
> L2 | 父级: /AGENTS.md

成员清单
conftest.py: pytest 共享 fixture，提供 graph_db_path、graph_conn、fixture_root 与 fixture_doc_paths。
test_app.py: API 冒烟测试——healthcheck、settings .env 解析回退语义、dashboard 缓存。
test_llm_client.py: LLM 配置契约测试，锁定 Ollama 裸模型名归一化、默认构造复用当前 settings、原始模型透传、目标模型存在性判断与错误脱敏语义。
test_graph_store.py: 图谱存储与索引回归测试，锁定 graph schema、legacy schema 拒绝、section 入库、边去重/折叠、bare OpenAI embedding 模型路由判定。
test_impact_analyzer.py: 影响分析器单元测试，锁定 AI 精判按文档批量调用 LLM，而不是按候选章节重复外呼。
test_e2e_mvp_scenario.py: 图谱栈端到端场景测试，覆盖上传、草稿、评估、影响分析、图谱与仪表盘契约。
test_env_routing.py: 环境配置回归测试，使用本地 fake OpenAI-compatible provider 验证 bare LLM/Embedding 模型名经 .env + base_url 路由后可完成 completion 和 embedding。
test_desktop_runtime.py: 桌面运行时路径契约测试，锁定 app data 下的 DB/Chroma/上传/导出/日志/.env 与 sidecar 环境变量。
test_spa_assets.py: SPA 静态资源定位测试，锁定显式环境变量、PyInstaller `_MEIPASS` 与缺失场景的解析语义。
test_developer_logs.py: 开发者日志 API 契约测试，锁定显式日志文件、日志目录最新文件与空日志响应。

法则: 测试只锁定可观察行为，优先覆盖真实工作流而非内部步骤。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
