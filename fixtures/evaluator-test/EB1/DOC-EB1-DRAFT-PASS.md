<!--
[INPUT]: 依赖 DOC-EB1-ICD 已导入图谱（燃烧室压力=10 MPa，额定推力=650 kN）
[OUTPUT]: 草稿参数值与 ICD 完全一致，EB1 应返回 PASS
[POS]: EB1 PASS 场景的草稿，参数名从行首开始以满足 _PARAM_PATTERN 匹配要求
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->

---
doc_id: DOC-EB1-DRAFT-PASS
title: 推进系统方案草稿（EB1 一致性 PASS 样本）
version: v0.1
status: Draft
department: 动力系统部
doc_type: Draft
system_level: Subsystem
engineering_phase: Design
---

# 推进系统方案草稿（EB1 PASS）

## 1. 主要接口参数

燃烧室压力为 10 MPa，处于设计包络 9.5 ~ 10.5 MPa 范围内。

额定推力为 650 kN，满足运载需求。

> **EB1 预期结果：PASS** — 草稿中「燃烧室压力=10 MPa」和「额定推力=650 kN」
> 与 `DOC-EB1-ICD` 中的 ICD 值完全一致。
