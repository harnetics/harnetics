<!--
[INPUT]: 冲突检测已运行并返回 2 处冲突，草稿内容缺少 ⚠️ 标记
[OUTPUT]: ED3 检查 len(⚠️)=0 < len(conflicts)=2，应返回 FAIL
[POS]: ED3 FAIL 场景：冲突未在正文中标记
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

注意：ED3 的 conflicts 字段来自冲突检测器运行结果（非 frontmatter）。
本文档模拟：冲突已被检测到，但作者没有在草稿中添加任何 ⚠️ 标记。
-->

---
doc_id: DOC-ED3-DRAFT-FAIL
title: 跨分系统接口草稿（ED3 冲突标记 FAIL 样本）
version: v0.1
status: Draft
department: 系统工程部
doc_type: Draft
system_level: System
engineering_phase: Design
---

# 跨分系统接口草稿（冲突未标记）

## 1. 燃烧室压力接口

本草稿采用 10 MPa，GNC 需求参考旧值 12 MPa（两方存在冲突，但此处未标记）。

## 2. 额定推力接口

动力系统设计额定推力 650 kN，结构载荷分析假设 700 kN（冲突未标记）。

## 3. 比冲参数

真空比冲 360 s，当前无冲突。

> **ED3 预期结果：FAIL** — 草稿内容有 0 个 ⚠️ 标记，但 `conflicts` 列表
> 包含 2 处冲突，ED3 应报 BLOCK：「2 处冲突但正文只有 0 个 ⚠️ 标记」。
