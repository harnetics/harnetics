<!--
[INPUT]: 无外部依赖
[OUTPUT]: 注册三个无循环引用的文档 DOC-EA4-A/B/C，EA4 应返回 PASS
[POS]: EA4 PASS 场景：线性引用链 A → B → C
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->

---
doc_id: DOC-EA4-A
title: 总体需求文档（EA4 线性链根节点）
version: v1.0
status: Approved
department: 系统工程部
doc_type: Requirement
system_level: System
engineering_phase: Requirement
references:
  - doc_id: DOC-EA4-B
    relation: derived_to
---

# 总体需求文档

本文档为 EA4 线性链测试的顶层节点（A），引用下游 DOC-EA4-B。
引用链：**A → B → C**，无环，EA4 期望返回 **PASS**。

## 1. 系统推力需求

发动机额定推力 ≥ 650 kN，详见 DOC-EA4-B §2。
