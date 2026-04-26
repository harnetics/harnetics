<!--
[INPUT]: 无外部依赖
[OUTPUT]: 草稿含 5 个技术段落，仅 1 个有 📎，覆盖率 20%；EA5 应返回 WARN
[POS]: EA5 WARN 场景：引注覆盖率低于 80% 阈值
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->

---
doc_id: DOC-EA5-LOW-COV
title: 推进系统性能草稿（EA5 低覆盖率 WARN 样本）
version: v0.1
status: Draft
department: 动力系统部
doc_type: Draft
system_level: Subsystem
engineering_phase: Design
---

# 推进系统性能草稿（低引注覆盖率）

## 1. 推力参数（有引注）

发动机地面额定推力 650 kN。
[📎 DOC-SYS-001 §3.1]

## 2. 燃烧室压力（无引注）

燃烧室工作压力 10.0 MPa，工作温度 3500 K。

## 3. 比冲（无引注）

真空比冲 360 s，海平面比冲 320 s。

## 4. 混合比（无引注）

氧燃混合比 3.5（质量比），工作范围 3.2 ~ 3.8。

## 5. 推力调节（无引注）

推力调节范围 60% ~ 100% 额定推力（390 kN ~ 650 kN）。

> **EA5 预期结果：WARN** — 1/5 技术段落有引注，覆盖率 20% < 80% 阈值。
