<!--
[INPUT]: 无外部依赖，与 DOC-EA4-CYC-X 相互引用
[OUTPUT]: 注册 DOC-EA4-CYC-Y，引用回 DOC-EA4-CYC-X，形成环；EA4 返回 FAIL
[POS]: EA4 循环引用测试的第二个节点
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->

---
doc_id: DOC-EA4-CYC-Y
title: 接口文档 Y（EA4 循环引用测试 — 对等节点）
version: v1.0
status: Approved
department: 系统工程部
doc_type: Design
system_level: System
engineering_phase: Design
references:
  - doc_id: DOC-EA4-CYC-X
    relation: references
---

# 接口文档 Y（故意循环）

本文档引用 DOC-EA4-CYC-X，与之形成 Y → X → Y 循环。
导入两份文档（X + Y）后，EA4 应检出环并返回 **FAIL**。
