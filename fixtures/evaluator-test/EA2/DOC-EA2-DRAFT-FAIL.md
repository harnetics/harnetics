<!--
[INPUT]: 无前置依赖——故意引用不存在的文档
[OUTPUT]: 草稿引注 DOC-EA2-GHOST（未入库）→ EA2 应返回 FAIL
[POS]: EA2 FAIL 场景的验证草稿
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->

---
doc_id: DOC-EA2-DRAFT-FAIL
title: 推进系统技术方案草稿（EA2 FAIL 样本）
version: v0.1
status: Draft
department: 动力系统部
doc_type: Draft
system_level: Subsystem
engineering_phase: Design
---

# 推进系统技术方案草稿（故意引用不存在文档）

## 1. 总体参数（EA2 期望：FAIL）

发动机地面额定推力为 650 kN，燃烧室压力 10.0 MPa。
[📎 DOC-EA2-GHOST §2]

> **EA2 预期结果：FAIL** — 引注文档 `DOC-EA2-GHOST` 未在图谱中注册，
> EA2 应检出"引注文档不存在"并阻断。
