<!--
[INPUT]: 无外部依赖，故意构造双向循环引用
[OUTPUT]: 注册 DOC-EA4-CYC-X 与 DOC-EA4-CYC-Y，相互引用形成环；EA4 返回 FAIL
[POS]: EA4 FAIL 场景：X → Y → X 循环引用
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->

---
doc_id: DOC-EA4-CYC-X
title: 接口文档 X（EA4 循环引用测试 — 根节点）
version: v1.0
status: Approved
department: 系统工程部
doc_type: Design
system_level: System
engineering_phase: Design
references:
  - doc_id: DOC-EA4-CYC-Y
    relation: references
---

# 接口文档 X（故意循环）

本文档故意引用 DOC-EA4-CYC-Y，而后者又引用本文档，
形成 **X → Y → X** 循环，EA4 应返回 **FAIL（检测到循环引用节点）**。

## 说明

此文档仅用于 EA4 循环引用检测测试，不代表真实工程场景。
