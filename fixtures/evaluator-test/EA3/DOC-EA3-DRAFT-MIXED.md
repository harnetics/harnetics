<!--
[INPUT]: 依赖 DOC-EA3-CURRENT、DOC-EA3-OLD 已导入图谱
[OUTPUT]: 两份草稿——分别引用新版/旧版文档，触发 PASS 和 WARN
[POS]: EA3 两种结果的测试草稿，同一文件包含两个场景描述
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->

---
doc_id: DOC-EA3-DRAFT-MIXED
title: GNC 制导精度方案草稿（EA3 混合场景样本）
version: v0.1
status: Draft
department: GNC系统部
doc_type: Draft
system_level: Subsystem
engineering_phase: Design
---

# GNC 制导精度方案草稿

## 场景 A：引用当前版本（EA3 期望：PASS）

系统制导精度要求：轨道半长轴误差 ≤ 5 km。
[📎 DOC-EA3-CURRENT §2]

---

## 场景 B：引用已废止版本（EA3 期望：WARN）

旧版方案中制导精度为 ≤ 10 km（本段引用已废止文档）。
[📎 DOC-EA3-OLD §2]

> **注意**：EA3 对场景 B 应报 WARN：`引用文档版本已过期：DOC-EA3-OLD`
