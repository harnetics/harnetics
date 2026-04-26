<!--
[INPUT]: 依赖 DOC-EB1-ICD 已导入图谱（燃烧室压力=10 MPa）
[OUTPUT]: 草稿写错燃烧室压力（15 MPa），EB1 应返回 FAIL
[POS]: EB1 FAIL 场景的草稿，故意填写与 ICD 不符的参数值
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->

---
doc_id: DOC-EB1-DRAFT-FAIL
title: 推进系统方案草稿（EB1 一致性 FAIL 样本）
version: v0.1
status: Draft
department: 动力系统部
doc_type: Draft
system_level: Subsystem
engineering_phase: Design
---

# 推进系统方案草稿（EB1 FAIL）

## 1. 主要接口参数

燃烧室压力为 15 MPa，高于标准设计工况。

额定推力为 650 kN，满足运载需求。

> **EB1 预期结果：FAIL** — 草稿中「燃烧室压力=15 MPa」与
> `DOC-EB1-ICD` 规定的 ICD 值 10 MPa 不符，EB1 应报 BLOCK 并列出冲突项。
