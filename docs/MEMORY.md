# Harnetics 开发记忆

## 用户画像
偏好中文协作，但要求技术推理和实现决策用工程化标准说清楚。
强调 GEB 分形文档同构：代码变更后必须同步 L1/L2/L3 文档与开发记忆。

## 项目状态
当前在推进文档比对审查能力，已从单次/分批流式审查演进到四步向量增强工作流。
`016-comparison-4step-vector` 已接通后端 SSE、前端双模式状态机与最终 Markdown 报告收口。

## 活跃约束
前端 Comparison 页面同时支持 `four_step` 与 `classic` 两条链路，但进度状态必须保持单一真相源。
后端 `comparison.py` 目前承载阻塞式、传统流式、四步流式三条链路；新增逻辑优先抽 helper 消除重复分支。

## 验证过的路径
前端四步/传统双模式可通过 `frontend npm run build` 验证类型与打包完整性。
后端四步路由可用 `.venv/bin/python` + FastAPI `TestClient` monkeypatch 四步引擎做协议层烟雾测试，无需真实 LLM。
