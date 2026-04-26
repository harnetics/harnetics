<!--
[INPUT]: 冲突检测已运行并返回 2 处冲突，草稿内容包含 ⚠️ 标记
[OUTPUT]: ED3 检查 len(⚠️) >= len(conflicts)，应返回 PASS
[POS]: ED3 PASS 场景：所有检测到的冲突均在正文中打了 ⚠️ 标记
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

注意：ED3 的 conflicts 字段来自冲突检测器运行结果（非 frontmatter）。
本文档由 `harnetics generate` 调用后，在生成结果中添加 ⚠️ 标记来模拟此场景。
-->

---
doc_id: DOC-ED3-DRAFT-PASS
title: 跨分系统接口草稿（ED3 冲突标记 PASS 样本）
version: v0.1
status: Draft
department: 系统工程部
doc_type: Draft
system_level: System
engineering_phase: Design
---

# 跨分系统接口草稿（冲突已标记）

## 1. 燃烧室压力接口

⚠️ **冲突：燃烧室压力值存在歧义**
本草稿采用 10 MPa（来源 DOC-ICD-001），GNC 系统需求文档提出 12 MPa（旧版本遗留）。
建议以 ICD 最新版本 DOC-ICD-001 §interfaces 为准。

## 2. 额定推力接口

⚠️ **冲突：推力分配存在重叠定义**
动力系统设计额定推力 650 kN，结构载荷分析假设 700 kN。
建议召开接口协调会明确边界条件。

## 3. 比冲参数

真空比冲 360 s，当前无冲突。

> **ED3 预期结果：PASS** — 草稿有 2 个 ⚠️ 标记，与 `conflicts` 列表中
> 的 2 处冲突数量匹配，ED3 视为已正确标记所有冲突。
