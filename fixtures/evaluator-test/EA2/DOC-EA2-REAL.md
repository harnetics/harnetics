<!--
[INPUT]: 无外部依赖，作为 EA2 真实性测试的被引目标文档
[OUTPUT]: 在图谱中注册 DOC-EA2-REAL，使草稿中引注它时 EA2 返回 PASS
[POS]: EA2 校验器测试语料，供 DOC-EA2-DRAFT-PASS 引用
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->

---
doc_id: DOC-EA2-REAL
title: 推进系统接口参数基准文档（EA2 真实性测试源）
version: v1.0
status: Approved
department: 动力系统部
doc_type: Design
system_level: Subsystem
engineering_phase: Design
---

# 推进系统接口参数基准文档

## 1. 文档说明

本文档作为 EA2（引用文档真实性）校验器的测试源文档，导入后在图谱中注册
`DOC-EA2-REAL`，使 `DOC-EA2-DRAFT-PASS` 中的 📎 引注验证通过。

## 2. 发动机推力参数

| 参数       | 值       | 单位 |
|------------|----------|------|
| 地面额定推力 | 650      | kN   |
| 真空推力   | 720      | kN   |
| 燃烧室压力 | 10.0     | MPa  |
| 比冲（真空）| 360      | s    |
