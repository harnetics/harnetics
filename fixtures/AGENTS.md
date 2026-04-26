# fixtures/
> L2 | 父级: ../AGENTS.md

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

成员清单
AGENTS.md: `fixtures/` 的局部地图，定义样本文档语料的整体分层。
requirements/: 系统级需求样本，提供顶层需求与追溯起点。
design/: 总体与分系统设计样本，提供设计约束与方案上下文。
icd/: 接口控制样本，提供跨部门参数真相源。
quality/: 质量计划与 FMEA 样本，提供风险与治理视角。
templates/: 文档模板样本，提供生成草稿的结构骨架。
test_plans/: 测试大纲样本，提供生成与影响分析的目标文档形态。
samples/: 所有样本文件的扁平副本（10 份，无子目录），供用户一键批量导入 或 `harnetics ingest fixtures/samples/`。
format-test/: 所有支持格式的最小化样本（.md/.yaml/.csv/.docx/.xlsx/.pdf），用于验证各格式解析器效果。
evaluator-test/: 六个在线校验器的专属测试语料（EA2/EA3/EA4/EA5/EB1/ED3），含 PASS/WARN/FAIL 三种预期结果的文档对，配套 README.md 测试指南。

法则
- 这里存的是样本语料，不是产品说明文档。
- 新样本必须保留稳定 `doc_id`、版本、部门与类型信息。
