<!--
[INPUT]: 依赖 DOC-EA4-A 的需求约束
[OUTPUT]: 注册 DOC-EA4-B，作为线性链中间节点；EA4 PASS 场景
[POS]: EA4 线性链中间节点，引用 DOC-EA4-C
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->

---
doc_id: DOC-EA4-B
title: 分系统设计文档（EA4 线性链中间节点）
version: v1.0
status: Approved
department: 动力系统部
doc_type: Design
system_level: Subsystem
engineering_phase: Design
references:
  - doc_id: DOC-EA4-A
    relation: derived_from
  - doc_id: DOC-EA4-C
    relation: derived_to
---

# 分系统设计文档

本文档为 EA4 线性链中间节点（B），上游引用 DOC-EA4-A，下游引用 DOC-EA4-C。

## 2. 发动机额定推力

额定推力 650 kN，测试大纲见 DOC-EA4-C §3。
