# harnetics/engine/
> L2 | 父级: src/harnetics/AGENTS.md

成员清单
__init__.py: 包入口。
draft_generator.py: 草稿生成主流水线，负责检索上下文、注入 GEP 演化上下文、调用 LLM、解析引注、回填引文内容、自动评估（build_default_bus）、落库，并写入本次进化信号。
conflict_detector.py: 来源文档间冲突检测器，产出 Conflict 列表。
impact_analyzer.py: 影响分析器，支持 AI 向量分析（向量粗筛 + LLM 精判）与 heuristic 降级双模式。
fixture_runner.py: 夹具场景运行器，读取 fixtures/evaluator-test/ 目录中的 DRAFT Markdown 文件、跳过源文档、调用评估器总线、写入进化信号，实现绕过 LLM 的快速评估闭环演示。
evolution/: 本机自进化子模块（基于 EvoMap/evolver GEP 协议）— 见 evolution/AGENTS.md。

法则: engine 只做跨模块编排与领域推理，不直接承担 HTTP 或 UI 逻辑。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
