<!--
[INPUT]: 依赖 DOC-EA4-B 的设计参数
[OUTPUT]: 注册 DOC-EA4-C，作为线性链末端节点；EA4 PASS 场景
[POS]: EA4 线性链末端节点，不引用任何上级
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->

---
doc_id: DOC-EA4-C
title: 发动机试车测试大纲（EA4 线性链末端节点）
version: v1.0
status: Approved
department: 测试部
doc_type: TestPlan
system_level: Subsystem
engineering_phase: Test
references:
  - doc_id: DOC-EA4-B
    relation: derived_from
---

# 发动机试车测试大纲

本文档为 EA4 线性链末端节点（C），仅引用上游 DOC-EA4-B，
不再往下引用，形成终止节点。EA4 对整条链应返回 **PASS**。

## 3. 验证项目

- 额定推力 650 kN 持续时间 ≥ 30 s。
- 燃烧室压力 10.0 MPa ± 0.5 MPa。
