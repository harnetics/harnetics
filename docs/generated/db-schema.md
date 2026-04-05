<!--
[INPUT]: 依赖当前 docs-first 仓库结构与 PRD 中的未来数据需求
[OUTPUT]: 对外提供当前存储面说明与目标数据模型草图
[POS]: generated/ 的结构化工件入口，承接未来真实 schema
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->

# DB Schema

当前还没有真正的数据库，现有存储面只有文件系统：
- `fixtures/`：领域样本文档
- `docs/`：产品、设计与治理文档

未来最小数据模型应至少包含：
- `Document`：文档元数据、版本、部门、类型、层级、阶段
- `Section`：结构化切片，用于检索和引用
- `Citation`：草稿内容到源 section 的引用关系
- `VersionEdge`：同一文档不同版本之间的演化关系
- `ImpactEdge`：上游变更影响到下游文档的边

这里先记录目标形状，等真实实现出现后再替换成生成版 schema。
