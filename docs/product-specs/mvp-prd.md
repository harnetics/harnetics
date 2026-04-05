<!--
[INPUT]: 依赖 docs/design-docs/aerospace-mvp-v3.md 的架构叙事与当前产品定义
[OUTPUT]: 对外提供 Harnetics MVP 的正式 PRD、用户故事与验收标准
[POS]: product-specs/ 的主规格文档，承接设计判断并驱动实现计划
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->

# Harnetics MVP PRD v3.1 — 跨部门文档对齐系统

> 本文档是 `docs/design-docs/aerospace-mvp-v3.md`（v3 架构文档）§9 的完整展开，可直接用于开发执行。

---

## 1. 产品概述

**一句话**：一个帮助商业航天工程师自动对齐跨部门、跨层级文档的本地化 AI 工具。

**核心问题**：工程师每天 40–60% 的时间花在文档编写和评审上，其中最耗时的是跨部门对齐——找上游文档、核对 ICD 参数、确认版本一致性。

**MVP 目标**：在一个部门（动力系统部）的一个场景（发动机地面试车测试大纲）上验证：AI 能否将文档准备时间从 2–3 天降到半天。

**MVP 交付形态**：本地部署的 Web 应用（FastAPI + Jinja2/HTMX），含本地 LLM（Gemma 4 26B A4B 4-bit），工程师通过浏览器操作。

---

## 2. 用户画像

### 2.1 主要用户：分系统工程师

| 维度     | 描述                                                      |
| -------- | --------------------------------------------------------- |
| 角色     | 动力系统部工程师                                          |
| 技术水平 | 航天专业背景，熟练使用 Word/Excel，不熟悉命令行和编程     |
| 日常痛点 | 写测试大纲前要花 1–2 天找文档、读文档、手动对齐引用       |
| 期望     | 输入主题描述，得到一份带引注的草稿，直接在上面改          |
| 约束     | 所有数据必须在本地，不可上传到外部服务                    |

### 2.2 次要用户：技术负责人

| 维度     | 描述                                                       |
| -------- | ---------------------------------------------------------- |
| 角色     | 技术负责人 / 系统工程部负责人                              |
| 技术水平 | 有一定技术背景，能安装和配置软件                           |
| 日常痛点 | ICD 更新后不知道哪些下游文档受影响，靠邮件通知容易遗漏    |
| 期望     | 修改 ICD 后，系统自动告诉他哪些部门的哪些文档需要更新      |
| 约束     | 同上                                                       |

### 2.3 部署管理员

| 维度     | 描述                                                   |
| -------- | ------------------------------------------------------ |
| 角色     | IT 支持或技术负责人兼任                                |
| 技术水平 | 能按文档操作 Docker/pip install，不需要编程             |
| 职责     | 初始部署、导入文档、配置 LLM                           |

---

## 3. 用户故事

### US-1：导入文档

> 作为**部署管理员**，我希望能够通过 Web 界面上传公司文档，系统自动解析并建立索引，以便后续的对齐和分析功能可以使用这些文档。

**验收标准**：
- [ ] 支持拖拽上传 Markdown / YAML / 纯文本文件
- [ ] 上传后系统自动解析为结构化 Section
- [ ] ICD（YAML 格式）上传后自动提取接口参数列表
- [ ] 可以为每份文档指定元数据（部门、类型、层级、工程阶段）
- [ ] 文档解析完成后显示"已入库"状态和 Section 数量
- [ ] 支持批量上传（选择多个文件）

### US-2：浏览文档库

> 作为**工程师**，我希望能够按部门、文档类型、系统层级筛选和搜索已入库的文档，以便快速找到需要的信息。

**验收标准**：
- [ ] 文档列表支持按部门、类型、层级、状态筛选
- [ ] 支持关键词搜索（文档标题 + 内容）
- [ ] 点击文档可查看详情：元数据 + 所有 Section + 关联关系
- [ ] 文档详情页显示该文档的上游/下游关系列表

### US-3：生成对齐草稿

> 作为**动力系统部工程师**，我希望描述需要写的文档主题，系统自动检索相关文档并生成一份带引注的草稿，以便我可以直接审核修改而不是从零开始写。

**验收标准**：
- [ ] 选择部门、文档类型、系统层级后，输入主题描述
- [ ] 可选择上级文档和模板
- [ ] 点击生成后，系统显示进度（检索中→生成中→校验中）
- [ ] 草稿每个段落/条目带有来源引用标记（可点击查看原文）
- [ ] 检测到的上游冲突以醒目方式标记
- [ ] 底部显示 Evaluator 检查结果（通过/告警/阻断）
- [ ] 可以将草稿导出为 Markdown 文件
- [ ] 生成时间 < 3 分钟（10 份源文档场景）

### US-4：变更影响分析

> 作为**技术负责人**，我希望在更新 ICD 或需求文档后，系统自动告诉我哪些部门的哪些文档受到影响，以便我可以通知相关部门更新。

**验收标准**：
- [ ] 上传同一文档的新版本时，系统自动识别为版本更新
- [ ] 显示新旧版本差异（变更的 Section、变更的参数）
- [ ] 生成受影响文档清单：文档名 + 部门 + 影响级别 + 受影响章节
- [ ] 影响级别分三级：Critical / Major / Minor
- [ ] 报告可导出为 Markdown

### US-5：查看文档图谱

> 作为**工程师**，我希望能够可视化地看到文档之间的关系，以便理解整个文档网络的结构。

**验收标准**：
- [ ] 以图形方式展示文档节点和关系边
- [ ] 节点颜色按部门区分
- [ ] 点击节点显示文档信息
- [ ] 支持按部门/层级筛选显示范围
- [ ] ICD 节点在图谱中居于中心位置

### US-6：查看系统状态

> 作为**技术负责人**，我希望在仪表盘上看到文档库的整体健康状况。

**验收标准**：
- [ ] 显示：总文档数、总关系数、过期引用数
- [ ] 显示最近导入/更新的文档时间线
- [ ] 显示 Evaluator 检查的通过率概览

---

## 4. WebUI 设计

### 4.1 设计原则

- **简洁专业**：航天行业审美，深色/浅色主题切换，无花哨动画
- **中文优先**：所有界面元素中文标注
- **最少操作**：核心流程（生成草稿）不超过 3 步
- **零前端知识**：工程师用浏览器打开 `http://localhost:8080` 即可使用

### 4.2 技术选型

| 组件       | 选择                      | 理由                                   |
| ---------- | ------------------------- | -------------------------------------- |
| 后端框架   | FastAPI                   | 异步、性能好、自带 OpenAPI 文档        |
| 模板引擎   | Jinja2                    | 服务端渲染，无需前端构建工具           |
| 交互增强   | HTMX                      | 无需编写 JS，通过 HTML 属性实现动态交互 |
| 样式       | Tailwind CSS + DaisyUI    | 组件化、专业外观、响应式               |
| 图谱可视化 | vis-network.js            | 轻量、交互性好、无需 npm               |
| 图标       | Heroicons                 | 配合 Tailwind 生态                     |

### 4.3 信息架构

```
Harnetics
├── 首页/仪表盘        /                   → 系统状态概览
├── 文档库             /documents           → 上传、浏览、搜索文档
│   └── 文档详情       /documents/{doc_id}  → 查看文档内容和关系
├── 草稿工作台         /draft               → 生成对齐草稿（核心功能）
│   └── 草稿详情       /draft/{draft_id}    → 查看/编辑/导出草稿
├── 变更影响           /impact              → 变更影响分析
│   └── 影响报告       /impact/{report_id}  → 查看影响报告
└── 文档图谱           /graph               → 关系可视化
```

### 4.4 P1：首页/仪表盘

```
┌─────────────────────────────────────────────────────────────────┐
│  🔧 Harnetics     [首页]  [文档库]  [草稿台]  [变更影响]  [图谱] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │  📄 文档总数  │ │  🔗 关系总数  │ │  ⚠️ 过期引用  │            │
│  │     10       │ │     23       │ │      3       │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│                                                                 │
│  ── 快捷操作 ──                                                 │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │  📝 生成新草稿       │  │  📊 变更影响分析     │              │
│  └─────────────────────┘  └─────────────────────┘              │
│                                                                 │
│  ── 最近活动 ──                                                 │
│  • 14:30  导入文档 DOC-ICD-001 v2.3                             │
│  • 14:25  生成草稿「TQ-12 地面试车测试大纲」                    │
│  • 13:00  变更影响分析 DOC-SYS-001 v3.0 → v3.1                 │
│                                                                 │
│  ── 文档健康度 ──                                               │
│  引用最新版本  ████████░░ 78%                                    │
│  ICD 一致性    ██████████ 100%                                   │
│  引注完整性    ███████░░░ 72%                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.5 P2：文档库

```
┌─────────────────────────────────────────────────────────────────┐
│  文档库                                        [+ 上传文档]      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  📁 将文档拖放到此处上传                                │    │
│  │     支持格式：Markdown (.md)、YAML (.yaml/.yml)         │    │
│  │     [选择文件]                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  筛选：[所有部门 ▾] [所有类型 ▾] [所有层级 ▾]   🔍 搜索...    │
│                                                                 │
│  ┌────────────┬──────────────────┬──────────┬──────┬────┬────┐  │
│  │ 文档编号    │ 标题              │ 部门      │ 类型  │版本 │状态│  │
│  ├────────────┼──────────────────┼──────────┼──────┼────┼────┤  │
│  │ DOC-ICD-001│ 全局接口控制文档   │ 技术负责人│ ICD  │v2.3│ ✅ │  │
│  │ DOC-SYS-001│ 系统级需求文档     │ 系统工程部│ 需求  │v3.1│ ✅ │  │
│  │ DOC-DES-001│ 动力分系统设计     │ 动力系统部│ 设计  │v1.2│ ✅ │  │
│  │ DOC-TST-001│ 热试车测试大纲     │ 动力系统部│ 测试  │v1.0│ ✅ │  │
│  │ DOC-TST-003│ 推力室点火测试大纲 │ 动力系统部│ 测试  │v1.1│ ⚠️ │  │
│  │  ...       │  ...              │  ...     │  ... │ ...│  ..│  │
│  └────────────┴──────────────────┴──────────┴──────┴────┴────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**上传对话框**（点击"上传文档"或拖放后弹出）：

```
┌───────────────────────────────────────────┐
│  上传文档                          [✕]    │
├───────────────────────────────────────────┤
│                                           │
│  文件：system_requirements.md    ✅ 已选择 │
│                                           │
│  文档编号  [DOC-SYS-001        ]          │
│  文档标题  [天行一号系统级需求文档]        │
│  所属部门  [系统工程部         ▾]          │
│  文档类型  [需求文档           ▾]          │
│  系统层级  [系统层             ▾]          │
│  工程阶段  [需求               ▾]          │
│  版本号    [v3.1               ]          │
│                                           │
│  ☐ ICD 文档（启用接口参数提取）           │
│                                           │
│       [取消]           [确认上传]          │
│                                           │
└───────────────────────────────────────────┘
```

**文档详情页**（点击文档行进入）：

```
┌─────────────────────────────────────────────────────────────────┐
│  ← 返回文档库    DOC-SYS-001 — 天行一号系统级需求文档 v3.1      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [元数据]  [内容]  [关系]                                       │
│                                                                 │
│  ── 元数据 ──                                                   │
│  部门：系统工程部    类型：需求文档    层级：系统层               │
│  阶段：需求          版本：v3.1       状态：已批准               │
│                                                                 │
│  ── 章节列表（12 个 Section）──                                 │
│  1. 文档说明                                                    │
│  2. 引用文件                                                    │
│  3. 系统级性能需求                                              │
│     3.1 总体性能                                                │
│     3.2 动力系统性能需求                                        │
│     3.3 GNC 性能需求                                            │
│     ...                                                         │
│                                                                 │
│  ── 关联文档 ──                                                 │
│  上游（0）：无                                                  │
│  下游（4）：                                                    │
│   • DOC-ICD-001  derived_from  置信度 1.0                       │
│   • DOC-DES-001  traces_to    置信度 1.0                        │
│   • DOC-TST-001  traces_to    置信度 0.85                       │
│   • DOC-OVR-001  references   置信度 1.0                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.6 P3：草稿工作台（核心页面）

**Step 1：配置**

```
┌─────────────────────────────────────────────────────────────────┐
│  草稿工作台                                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ── 第 1 步：描述你要写的文档 ──                                │
│                                                                 │
│  所属部门    [动力系统部          ▾]                              │
│  文档类型    [测试大纲            ▾]                              │
│  系统层级    [分系统层            ▾]                              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 主题描述（用自然语言描述你要写什么）                      │    │
│  │                                                         │    │
│  │ TQ-12 液氧甲烷发动机地面全工况热试车测试大纲。           │    │
│  │ 需要覆盖额定推力、深度变推力、混合比调节、启停等         │    │
│  │ 工况。主要验证发动机在额定工况下的推力、比冲和燃烧       │    │
│  │ 稳定性。                                                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  上级文档（可选）  [DOC-SYS-001 天行一号系统级需求文档  ▾]      │
│  文档模板（可选）  [DOC-TPL-001 地面试验测试大纲模板    ▾]      │
│                                                                 │
│  ── 系统自动检索到的相关文档 ──                                 │
│  ☑ DOC-ICD-001  全局接口控制文档 v2.3       (ICD约束)           │
│  ☑ DOC-DES-001  TQ-12 动力分系统设计 v1.2   (设计依据)         │
│  ☑ DOC-TST-001  热试车测试大纲 v1.0         (历史参考)          │
│  ☑ DOC-TST-002  涡轮泵性能试验大纲 v1.0     (历史参考)         │
│  ☑ DOC-TST-003  推力室点火试验大纲 v1.1      (历史参考)         │
│  ☐ DOC-FMA-001  动力系统 FMEA v2.0          (安全参考)          │
│  ☑ DOC-QAP-001  质量管理计划 v1.0           (质量要求)          │
│                                                                 │
│              [🚀 生成对齐草稿]                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Step 2：生成中（进度状态）**

```
┌─────────────────────────────────────────────────────────────────┐
│  草稿工作台 — 正在生成...                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✅ 检索相关文档              7 份文档，42 个相关章节            │
│  ✅ 提取 ICD 约束             12 个接口参数                      │
│  ✅ 检查上游需求覆盖           8 条需求已匹配                    │
│  🔄 生成草稿内容              LLM 推理中... (预计 60–120 秒)     │
│  ⬜ 验证引注完整性                                               │
│  ⬜ 运行 Evaluator 检查                                          │
│                                                                 │
│  ████████████████░░░░░░░░░░  62%                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Step 3：草稿结果**

```
┌─────────────────────────────────────────────────────────────────┐
│  草稿工作台 — 草稿已生成                            [导出 .md]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──── 左侧：草稿内容 ────────────┐ ┌── 右侧：引用面板 ──────┐ │
│  │                                │ │                        │ │
│  │ # TQ-12 液氧甲烷发动机         │ │ 📎 当前引用            │ │
│  │ # 地面全工况热试车测试大纲       │ │                        │ │
│  │                                │ │ DOC-SYS-001 §3.2      │ │
│  │ ## 1. 测试目的                  │ │ ──────────────         │ │
│  │                                │ │ 动力系统性能需求：      │ │
│  │ 本试验旨在验证 TQ-12 液氧      │ │ REQ-SYS-003 地面推力   │ │
│  │ 甲烷发动机在地面工况下的推      │ │ ≥ 650 kN ±3%          │ │
│  │ 力性能、燃烧稳定性和系统        │ │ REQ-SYS-004 真空比冲   │ │
│  │ 可靠性。📎¹                     │ │ ≥ 315 s               │ │
│  │                                │ │                        │ │
│  │ ## 2. 测试依据                  │ │                        │ │
│  │ - 系统级需求 📎²                │ │                        │ │
│  │ - ICD 接口定义 📎³              │ │                        │ │
│  │                                │ │                        │ │
│  │ ## 3. 测试项目                  │ │                        │ │
│  │                                │ │                        │ │
│  │ ### 3.1 额定推力性能试验        │ │                        │ │
│  │ 试验目标：验证发动机地面推      │ │ DOC-ICD-001 ICD-PRP-001│ │
│  │ 力 ≥ 650 kN（📎⁴），混合比     │ │ ──────────────         │ │
│  │ 3.5:1 ±5%（📎⁵）               │ │ 地面推力：650 kN       │ │
│  │                                │ │ 允许范围：630.5~669.5  │ │
│  │ ⚠️ 冲突：DOC-TST-003 v1.1     │ │                        │ │
│  │ 引用的推力值为 600 kN，与       │ │ ⚠️ 版本冲突            │ │
│  │ 当前 ICD v2.3 不一致            │ │ DOC-TST-003 引用       │ │
│  │ ─────────────────              │ │ ICD v2.1 (推力600kN)   │ │
│  │                                │ │ 当前 ICD v2.3 (650kN)  │ │
│  │ ### 3.2 深度变推力试验          │ │                        │ │
│  │ ...                            │ │                        │ │
│  │                                │ │                        │ │
│  └────────────────────────────────┘ └────────────────────────┘ │
│                                                                 │
│  ── Evaluator 检查结果 ──                                       │
│  ✅ EA.1 每个技术指标有来源引用   ✅ EA.2 引用文档真实存在       │
│  ⚠️ EA.3 引用版本告警（1处）     ✅ EA.4 无循环引用             │
│  ✅ EA.5 引注覆盖率 92%          ✅ EB.1 ICD 参数一致           │
│  ⚠️ EB.2 ICD 版本引用告警（1处） ✅ EB.3 无私有接口             │
│  ✅ ED.1 无捏造指标              ✅ ED.2 无错误归因              │
│  ✅ ED.3 冲突已标记                                             │
│                                                                 │
│  阻断项：0    告警项：2    通过项：9                             │
│                                                                 │
│  [📋 复制全文]  [💾 保存到文档库]  [📤 导出 .md]                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.7 P4：变更影响分析

```
┌─────────────────────────────────────────────────────────────────┐
│  变更影响分析                                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  选择已变更的文档  [DOC-ICD-001 全局接口控制文档        ▾]      │
│  旧版本           [v2.1                                ▾]      │
│  新版本           [v2.3（当前）                         ▾]      │
│                                                                 │
│                    [🔍 分析影响]                                  │
│                                                                 │
│  ═══════════════════════════════════════════════════════════════ │
│                                                                 │
│  ── 变更内容 ──                                                 │
│  ┌─────────────────────┬────────────┬────────────┐              │
│  │ 参数                │ v2.1       │ v2.3       │              │
│  ├─────────────────────┼────────────┼────────────┤              │
│  │ 🔴 ICD-PRP-001 推力  │ 600 kN     │ 650 kN     │              │
│  │ 🟡 ICD-PRP-004 室压  │ 9.5 MPa    │ 10.0 MPa   │              │
│  │ 🟢 ICD-PRP-006 法兰  │ Φ420 mm    │ Φ420 mm    │              │
│  └─────────────────────┴────────────┴────────────┘              │
│                                                                 │
│  ── 受影响文档（4 份）──                                       │
│  ┌────────────┬────────────┬────┬─────────────────┬──────┐     │
│  │ 文档        │ 部门        │级别│ 受影响章节       │ 建议 │     │
│  ├────────────┼────────────┼────┼─────────────────┼──────┤     │
│  │ DOC-DES-001│ 动力系统部  │ 🔴 │ §3.1 推力设计点 │ 更新 │     │
│  │ DOC-TST-001│ 动力系统部  │ 🔴 │ §3.1 额定推力   │ 更新 │     │
│  │ DOC-TST-003│ 动力系统部  │ 🔴 │ §2.1 试验参数   │ 更新 │     │
│  │ DOC-OVR-001│ 总体设计部  │ 🟡 │ §4.2 动力指标   │ 审查 │     │
│  └────────────┴────────────┴────┴─────────────────┴──────┘     │
│                                                                 │
│  [📤 导出报告]                                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.8 P5：文档图谱

```
┌─────────────────────────────────────────────────────────────────┐
│  文档图谱                  筛选：[所有部门 ▾] [所有层级 ▾]      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│          ┌──────────┐                                           │
│          │DOC-SYS-001│ ← 系统工程部（蓝色）                     │
│          │ 系统需求  │                                           │
│          └────┬─────┘                                           │
│         ╱     │     ╲                                           │
│        ╱      │      ╲                                          │
│  ┌─────────┐ │  ┌──────────┐                                   │
│  │DOC-OVR  │ │  │DOC-ICD   │ ← 技术管理（橙色）                │
│  │总体方案  │ │  │全局ICD   │ ← 中心枢纽节点（大圆）            │
│  └─────────┘ │  └────┬─────┘                                   │
│              │  ╱    │    ╲                                      │
│         ┌────┴──┐    │  ┌─────────┐                             │
│         │DOC-DES│    │  │DOC-TPL  │ ← 试验验证部（绿色）        │
│         │动力设计│    │  │测试模板 │                              │
│         └───┬───┘    │  └─────────┘                             │
│          ╱  │  ╲     │                                           │
│  ┌──────┐┌──┴───┐┌──┴───┐                                     │
│  │TST-01││TST-02││TST-03│ ← 动力系统部（红色）                 │
│  │热试车 ││涡轮泵 ││推力室 │                                     │
│  └──────┘└──────┘└──────┘                                      │
│                                                                 │
│  图例：                                                         │
│  ── traces_to   --- references   ··· constrained_by             │
│  🔵 系统工程  🔴 动力系统  🟢 试验验证  🟠 技术管理              │
│                                                                 │
│  点击节点查看文档详情 | 双击节点展开关联关系                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.9 交互流程：草稿生成

```
用户                        系统
 │                           │
 ├─ 选择部门/类型/层级 ──────→│
 │                           ├─ 检索文档图谱
 ├─ 输入主题描述 ────────────→│ ├─ 匹配相关文档
 │                           ├─ 返回推荐文档列表
 │←─ 显示推荐文档 ───────────┤
 │                           │
 ├─ 勾选/取消相关文档 ───────→│
 ├─ 选择上级文档/模板 ───────→│
 ├─ 点击「生成」─────────────→│
 │                           ├─ 提取 ICD 约束
 │                           ├─ 组装 LLM 上下文
 │                           ├─ 调用 Gemma 4 生成
 │                           ├─ 解析引注标记
 │                           ├─ 运行 Evaluator
 │←─ 返回草稿 + 引注 + 检查 ─┤
 │                           │
 ├─ 点击引注标记 ────────────→│
 │←─ 右侧面板显示原文片段 ──┤
 │                           │
 ├─ 点击「导出」─────────────→│
 │←─ 下载 .md 文件 ─────────┤
```

---

## 5. 技术规格

### 5.1 系统架构

```
┌────────────────────────────────────────────────────────────┐
│  浏览器 (http://localhost:8080)                            │
│  Jinja2 Templates + HTMX + Tailwind/DaisyUI               │
└──────────────────────┬─────────────────────────────────────┘
                       │ HTTP
┌──────────────────────┴─────────────────────────────────────┐
│  FastAPI Server                                            │
│  ┌─────────┐ ┌──────────┐ ┌───────────┐ ┌──────────────┐ │
│  │ 路由层   │ │ 对齐引擎  │ │ Evaluator │ │ 文档解析器    │ │
│  └─────────┘ └──────────┘ └───────────┘ └──────────────┘ │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  文档图谱层 (DocumentGraph)                          │ │
│  │  SQLite + chromadb                                   │ │
│  └──────────────────────────────────────────────────────┘ │
└──────────────────────┬─────────────────────────────────────┘
                       │ HTTP (localhost:11434)
┌──────────────────────┴─────────────────────────────────────┐
│  Ollama (LLM Server)                                       │
│  gemma4:26b-it-a4b-q4_K_M                                  │
└────────────────────────────────────────────────────────────┘
```

### 5.2 LLM 配置

**模型**：Gemma 4 26B A4B（4-bit 量化）

| 属性         | 值                              |
| ------------ | ------------------------------- |
| 模型全名     | gemma4:26b-it-a4b-q4_K_M        |
| 架构         | MoE（26B 总参数，4B 活跃参数）   |
| 量化级别     | Q4_K_M（4-bit）                 |
| 模型文件大小 | ~15 GB                          |
| 推理显存需求 | ~18 GB（含 KV cache）           |
| 上下文窗口   | 32,768 tokens                   |
| 部署方式     | Ollama                          |
| 推理速度     | ~20–40 tok/s @ RTX 4090         |

**选型理由**：

1. **MoE 架构**：26B 总参数带来的知识量，4B 活跃参数带来的推理速度，两者兼得
2. **4-bit 量化**：单卡 RTX 4090 (24GB) 或 Apple M 系列即可运行
3. **中英双语**：Gemma 4 在中文航天术语上的表现优于同量级模型
4. **纯本地**：满足航天数据不可上传的安全要求
5. **长上下文**：32K tokens 足以装下 MVP 场景中 7–10 份文档的关键章节

**部署步骤**：

```bash
# 1. 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. 拉取模型（首次约 15 GB 下载）
ollama pull gemma4:26b-it-a4b-q4_K_M

# 3. 验证运行
ollama run gemma4:26b-it-a4b-q4_K_M "你好，请简要介绍液氧甲烷发动机的主要性能参数"
```

**LLM 调用策略**：

```python
# harnetics/llm/client.py
import litellm

class HarneticsLLM:
    def __init__(self, model: str = "ollama/gemma4:26b-it-a4b-q4_K_M"):
        self.model = model

    def generate_draft(self, system_prompt: str, context: str, user_request: str) -> str:
        """
        system_prompt: 角色定义 + 输出格式要求 + 引注规则
        context: 检索到的相关文档章节（拼接）
        user_request: 用户的主题描述
        """
        response = litellm.completion(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"## 参考文档\n\n{context}\n\n## 任务\n\n{user_request}"}
            ],
            temperature=0.3,       # 低温度：技术文档需要严谨
            max_tokens=8192,       # 足够生成一份完整测试大纲
            top_p=0.9,
        )
        return response.choices[0].message.content
```

**草稿生成 System Prompt**：

```
你是一名专业的航天系统工程文档助手。你的任务是根据用户提供的参考文档，
生成一份结构化的技术文档草稿。

## 严格规则

1. **每个技术指标必须标注来源**：使用格式 [📎 DOC-XXX-XXX §X.X] 标注
2. **不允许捏造数字**：所有数值参数必须来自参考文档，不可自行编造
3. **发现冲突必须标记**：如果两份参考文档对同一参数给出不同值，
   用 ⚠️ 标记冲突，列出两个来源和各自的值
4. **遵循模板格式**：如果提供了文档模板，严格按模板的章节结构生成
5. **使用中文**：正文使用中文，技术术语可保留英文缩写
6. **ICD 参数引用**：涉及接口参数时，标注 ICD 参数编号

## 输出格式

使用 Markdown 格式，章节使用 ## 和 ### 标题层级。
每个段落末尾标注引用来源。
冲突使用引用块标注：
> ⚠️ 冲突：[参数名]
> - DOC-XXX §X.X: [值A]
> - DOC-YYY §Y.Y: [值B]
```

### 5.3 后端 API

```
# 文档管理
POST   /api/documents/upload              上传并解析文档
GET    /api/documents                      文档列表（支持筛选参数）
GET    /api/documents/{doc_id}             文档详情（含 sections）
DELETE /api/documents/{doc_id}             删除文档
GET    /api/documents/{doc_id}/sections    获取文档所有章节

# ICD 参数
GET    /api/icd/parameters                 所有 ICD 参数列表
GET    /api/icd/parameters/{param_id}      单个 ICD 参数详情

# 文档图谱
GET    /api/graph                          完整图谱数据（vis.js 格式）
GET    /api/graph/upstream/{doc_id}        上游追溯
GET    /api/graph/downstream/{doc_id}      下游追溯
GET    /api/graph/stale                    过期引用列表
GET    /api/graph/related/{doc_id}         横向关联

# 草稿生成
POST   /api/draft/generate                 生成对齐草稿
GET    /api/draft/{draft_id}               获取草稿详情
GET    /api/drafts                         草稿列表

# 变更影响
POST   /api/impact/analyze                 分析变更影响
GET    /api/impact/{report_id}             获取影响报告

# Evaluator
POST   /api/evaluate/{doc_id}              对文档运行 Evaluator
GET    /api/evaluate/results/{eval_id}     获取检查结果

# 系统状态
GET    /api/status                         系统状态概览
```

**关键 API 请求/响应示例**：

```python
# POST /api/draft/generate
# Request:
{
    "requester_department": "动力系统部",
    "doc_type": "TestPlan",
    "system_level": "Subsystem",
    "subject": "TQ-12液氧甲烷发动机地面全工况热试车测试大纲",
    "parent_doc_id": "DOC-SYS-001",
    "template_id": "DOC-TPL-001",
    "related_doc_ids": ["DOC-ICD-001", "DOC-DES-001", "DOC-TST-001"],
    "constraints": []
}

# Response:
{
    "draft_id": "DRAFT-20260405-001",
    "status": "completed",
    "sections": [
        {
            "heading": "1. 测试目的",
            "content": "本试验旨在验证TQ-12液氧甲烷发动机...",
            "citations": [
                {
                    "source_doc_id": "DOC-SYS-001",
                    "source_section_id": "sec-3.2",
                    "source_text_snippet": "动力系统地面推力 ≥ 650 kN...",
                    "relation": "需求依据"
                }
            ],
            "confidence": 0.92
        }
        // ...
    ],
    "conflicts": [
        {
            "parameter": "地面推力",
            "doc_a": {"doc_id": "DOC-ICD-001", "version": "v2.3"},
            "value_a": "650 kN",
            "doc_b": {"doc_id": "DOC-TST-003", "version": "v1.1"},
            "value_b": "600 kN",
            "resolution": "DOC-TST-003 引用的是 ICD v2.1 版本，应更新至 v2.3"
        }
    ],
    "eval_results": [
        {"evaluator": "EA.1", "status": "pass", "detail": "所有技术指标有来源引用"},
        {"evaluator": "EA.3", "status": "warn", "detail": "DOC-TST-003 引用 ICD v2.1 已过期"}
    ]
}
```

### 5.4 数据库 Schema（SQLite）

```sql
-- 文档表
CREATE TABLE documents (
    doc_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    doc_type TEXT NOT NULL CHECK(doc_type IN (
        'ICD','Requirement','Design','TestPlan','TestReport',
        'Analysis','Status','Template','QualityPlan','FMEA','OverallDesign'
    )),
    department TEXT,
    system_level TEXT CHECK(system_level IN (
        'Mission','System','Subsystem','Unit','Component'
    )),
    engineering_phase TEXT CHECK(engineering_phase IN (
        'Requirement','Design','Integration','Test','Operation'
    )),
    version TEXT NOT NULL,
    status TEXT DEFAULT 'Approved' CHECK(status IN (
        'Draft','UnderReview','Approved','Superseded'
    )),
    content_hash TEXT,
    file_path TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- 章节表
CREATE TABLE sections (
    section_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    heading TEXT,
    content TEXT,
    level INTEGER DEFAULT 1,
    order_index INTEGER DEFAULT 0,
    tags TEXT DEFAULT '[]'  -- JSON array
);

-- 文档关系边
CREATE TABLE edges (
    edge_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_doc_id TEXT NOT NULL REFERENCES documents(doc_id),
    source_section_id TEXT,
    target_doc_id TEXT NOT NULL REFERENCES documents(doc_id),
    target_section_id TEXT,
    relation TEXT NOT NULL CHECK(relation IN (
        'traces_to','references','derived_from',
        'constrained_by','supersedes','impacts'
    )),
    confidence REAL DEFAULT 0.5,
    created_by TEXT DEFAULT 'ai_ingest',
    created_at TEXT DEFAULT (datetime('now'))
);

-- ICD 参数表
CREATE TABLE icd_parameters (
    param_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL REFERENCES documents(doc_id),
    name TEXT NOT NULL,
    interface_type TEXT CHECK(interface_type IN (
        'Mechanical','Electrical','Software','Thermal','Data','Propellant'
    )),
    subsystem_a TEXT,
    subsystem_b TEXT,
    value TEXT,
    unit TEXT,
    range TEXT,
    owner_department TEXT,
    version TEXT
);

-- 文档版本历史
CREATE TABLE versions (
    version_id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT NOT NULL REFERENCES documents(doc_id),
    version TEXT NOT NULL,
    content_hash TEXT,
    file_path TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- AI 生成的草稿
CREATE TABLE drafts (
    draft_id TEXT PRIMARY KEY,
    request_json TEXT NOT NULL,
    content_md TEXT,
    citations_json TEXT DEFAULT '[]',
    conflicts_json TEXT DEFAULT '[]',
    eval_results_json TEXT DEFAULT '[]',
    status TEXT DEFAULT 'generated' CHECK(status IN (
        'generating','completed','reviewed','exported'
    )),
    generated_by TEXT DEFAULT 'gemma4-26b',
    created_at TEXT DEFAULT (datetime('now')),
    reviewed_at TEXT
);

-- 变更影响报告
CREATE TABLE impact_reports (
    report_id TEXT PRIMARY KEY,
    trigger_doc_id TEXT NOT NULL REFERENCES documents(doc_id),
    old_version TEXT,
    new_version TEXT,
    changed_sections_json TEXT DEFAULT '[]',
    impacted_docs_json TEXT DEFAULT '[]',
    summary TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- 索引
CREATE INDEX idx_sections_doc ON sections(doc_id);
CREATE INDEX idx_edges_source ON edges(source_doc_id);
CREATE INDEX idx_edges_target ON edges(target_doc_id);
CREATE INDEX idx_edges_relation ON edges(relation);
CREATE INDEX idx_icd_params_doc ON icd_parameters(doc_id);
CREATE INDEX idx_documents_dept ON documents(department);
CREATE INDEX idx_documents_type ON documents(doc_type);
```

---

## 6. Evaluator 实现规格

### 6.1 Evaluator 接口

```python
from enum import Enum
from dataclasses import dataclass

class EvalLevel(Enum):
    BLOCK = "block"   # 阻断：必须修复才能继续
    WARN = "warn"     # 告警：建议修复但不阻断

class EvalStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"

@dataclass
class EvalResult:
    evaluator_id: str      # e.g. "EA.1"
    name: str              # e.g. "引注完整性"
    status: EvalStatus
    level: EvalLevel
    detail: str            # 具体描述
    locations: list[str]   # 问题位置列表

class BaseEvaluator:
    evaluator_id: str
    name: str
    level: EvalLevel

    def evaluate(self, draft, graph) -> EvalResult:
        raise NotImplementedError
```

### 6.2 MVP 必须实现的 Evaluator

| ID   | 名称                     | 实现要点                                                      | 级别 |
| ---- | ------------------------ | ------------------------------------------------------------- | ---- |
| EA.1 | 技术指标有来源引用       | 正则匹配段落中的数字/参数，检查是否有 📎 标记                 | 阻断 |
| EA.2 | 引用文档真实存在         | 提取引注中的 DOC-XXX-XXX，在图谱 documents 表中查询           | 阻断 |
| EA.3 | 引用版本为最新           | 比对引用的 version 与 documents 表中 status != Superseded 的版本 | 告警 |
| EA.4 | 无循环引用               | 图谱 edges 表做环检测（DFS）                                  | 阻断 |
| EA.5 | 引注覆盖率 ≥ 80%        | 识别"技术性段落"（含数字/参数），统计有引注比例               | 告警 |
| EB.1 | 接口参数与 ICD 一致      | 草稿中出现的参数名+值与 icd_parameters 表比对                 | 阻断 |
| ED.1 | 无捏造技术指标           | 交叉验证：草稿中每个数字都能在 source_documents 中找到原文    | 阻断 |
| ED.3 | 冲突明确标记             | 检查 conflicts 列表中的条目是否在草稿正文中有对应 ⚠️ 标记    | 阻断 |

Phase 1 追加：EB.2, EB.3, EC.1, EC.2, EC.3
Phase 2 追加：ED.2

---

## 7. MVP 场景定义

### 7.1 场景描述

```
角色：动力系统部工程师 小王
任务：编写「TQ-12 液氧甲烷发动机地面全工况热试车测试大纲」
背景：天行一号运载火箭进入发动机地面试车阶段，需要一份覆盖额定推力、
      变推力、混合比调节、启停等工况的测试大纲。
```

### 7.2 操作流程

```
1. 小王打开浏览器访问 http://localhost:8080
2. 首页显示文档库已有 10 份文档（管理员已导入）
3. 小王点击「草稿工作台」
4. 选择：部门=动力系统部，类型=测试大纲，层级=分系统层
5. 输入主题描述
6. 系统检索到 7 份相关文档，小王确认
7. 点击「生成对齐草稿」
8. 等待 1-2 分钟，草稿生成完成
9. 左侧显示草稿内容（带引注标记），右侧显示引用面板
10. 小王点击引注标记，右侧显示原文片段
11. 看到 1 处冲突标记（ICD 版本不一致），确认后修改
12. 底部 Evaluator 结果：0 阻断，2 告警，9 通过
13. 小王点击「导出 .md」下载草稿
14. 在 Word 中打开继续编辑完善
```

### 7.3 预期输入文档（10 份 Fixture）

| #  | 文档编号     | 标题                                | 部门         | 类型     | 格式     |
| -- | ------------ | ----------------------------------- | ------------ | -------- | -------- |
| 1  | DOC-SYS-001  | 天行一号运载火箭系统级需求文档       | 系统工程部   | 需求     | Markdown |
| 2  | DOC-ICD-001  | 天行一号全局接口控制文档             | 技术负责人   | ICD      | YAML     |
| 3  | DOC-TPL-001  | 地面试验测试大纲编写模板             | 试验与验证部 | 模板     | Markdown |
| 4  | DOC-DES-001  | TQ-12 液氧甲烷发动机分系统设计文档   | 动力系统部   | 设计     | Markdown |
| 5  | DOC-OVR-001  | 天行一号运载火箭总体设计方案         | 总体设计部   | 总体方案 | Markdown |
| 6  | DOC-TST-001  | TQ-12 发动机额定工况热试车测试大纲   | 动力系统部   | 测试大纲 | Markdown |
| 7  | DOC-TST-002  | TQ-12 涡轮泵组件性能试验测试大纲     | 动力系统部   | 测试大纲 | Markdown |
| 8  | DOC-TST-003  | TQ-12 推力室点火试验测试大纲         | 动力系统部   | 测试大纲 | Markdown |
| 9  | DOC-QAP-001  | 天行一号质量管理计划                 | 质量与可靠性部 | 质量计划 | Markdown |
| 10 | DOC-FMA-001  | TQ-12 动力系统故障模式与影响分析     | 质量与可靠性部 | FMEA     | Markdown |

### 7.4 预埋的测试用例

Fixture 数据中刻意编排了以下不一致，用于验证 Evaluator 和变更影响分析能力：

| #  | 不一致内容                                | 应触发          |
| -- | ----------------------------------------- | --------------- |
| T1 | DOC-TST-003 引用 ICD v2.1（当前 v2.3）    | EA.3, EB.2      |
| T2 | DOC-TST-003 推力值写的 600 kN（应为 650）  | EB.1, EC.1      |
| T3 | DOC-TST-002 发动机质量写 500 kg（ICD ≤480）| EB.1, EC.1      |
| T4 | DOC-TST-001 缺少 REQ-SYS-004 的追溯       | EC.2（Phase 1） |

### 7.5 预期输出

系统应生成一份类似以下结构的测试大纲草稿：

```markdown
# TQ-12 液氧甲烷发动机地面全工况热试车测试大纲

## 1. 测试目的
...（引用 DOC-SYS-001 §3.2）

## 2. 测试依据
- DOC-SYS-001 天行一号系统级需求文档 v3.1
- DOC-ICD-001 全局接口控制文档 v2.3
- DOC-DES-001 TQ-12 设计文档 v1.2
- DOC-TPL-001 测试大纲模板 v1.0

## 3. 测试项目

### 3.1 额定推力性能试验
...（引用 ICD-PRP-001, REQ-SYS-003）

### 3.2 深度变推力试验
...

### 3.3 混合比调节试验
...

### 3.4 发动机启动特性试验
...

### 3.5 发动机关机特性试验
...

### 3.6 燃烧稳定性评估
...

## 4. 测试条件与环境
...

## 5. 测试设备与设施
...

## 6. 数据采集与记录
...

## 7. 安全措施
...（引用 DOC-FMA-001, DOC-QAP-001）

## 8. 判定标准
...（引用 DOC-SYS-001, DOC-ICD-001）
```

---

## 8. 验收标准

### 8.1 功能验收

| 编号   | 验收项                           | 判定标准                                     |
| ------ | -------------------------------- | -------------------------------------------- |
| AC-01  | 文档上传与解析                   | 10 份 fixture 文档全部成功入库，Section 正确拆分 |
| AC-02  | ICD 参数提取                     | DOC-ICD-001 的 12 个参数全部正确提取          |
| AC-03  | 文档关系识别                     | 文档间至少 15 条关系被正确识别（规则匹配）    |
| AC-04  | 草稿生成完整性                   | 生成的测试大纲覆盖模板中所有必填章节          |
| AC-05  | 引注准确性                       | 草稿中 100% 的引注指向真实存在的文档和章节    |
| AC-06  | 冲突检测                         | T1/T2 两处预埋冲突全部被检测并标记            |
| AC-07  | Evaluator 阻断项                 | EA.1/EA.2/EA.4/EB.1/ED.1/ED.3 全部实现并运行 |
| AC-08  | 变更影响分析                     | 修改 ICD 推力参数后，4 份下游文档被识别        |
| AC-09  | WebUI 可访问                     | 浏览器打开即用，不需要命令行操作               |
| AC-10  | 生成时间                         | 草稿生成 < 3 分钟（10 份源文档场景）          |

### 8.2 用户体验验收

| 编号   | 验收项                 | 判定标准                                  |
| ------ | ---------------------- | ----------------------------------------- |
| UX-01  | 零 CLI 操作            | 用户从打开浏览器到导出草稿，全程无需命令行 |
| UX-02  | 操作步骤 ≤ 5 步       | 草稿生成核心流程不超过 5 步点击            |
| UX-03  | 引注可追溯             | 点击引注标记可查看原文片段                 |
| UX-04  | 导出可用               | 导出的 Markdown 文件格式正确、可用 Word 打开 |

---

## 9. 开发计划

### 9.1 Sprint 分解（总计 10 周）

| Sprint | 周次    | 交付物                                     |
| ------ | ------- | ------------------------------------------ |
| S1     | W1–W2  | 数据模型 + SQLite Schema + 文档解析器（MD/YAML） |
| S2     | W3–W4  | 文档图谱存储 + 关系抽取（规则匹配）+ 图谱查询 API |
| S3     | W5–W6  | LLM 集成（Ollama/Gemma 4）+ 草稿生成器 + 引注解析 |
| S4     | W7–W8  | Evaluator（EA.1-5, EB.1, ED.1, ED.3）+ 变更影响分析 |
| S5     | W9–W10 | WebUI 全部页面 + 端到端测试 + fixture 验证 + 文档 |

### 9.2 Sprint 详细任务

**S1：基础层（W1–W2）**

```
W1:
  - [ ] 项目骨架搭建（pyproject.toml, 目录结构）
  - [ ] 数据模型定义（models/）
  - [ ] SQLite Schema 创建 + migration 脚本
  - [ ] Markdown 解析器（→ DocumentNode + Section）
  - [ ] YAML 解析器（通用）

W2:
  - [ ] ICD YAML 专用解析器（→ ICDParameter 列表）
  - [ ] 文档入库管线（parse → store → index）
  - [ ] 基础 CRUD API（documents, sections）
  - [ ] 单元测试：10 份 fixture 文档全部成功入库
  - [ ] chromadb 向量存储接入 + Section 嵌入生成
```

**S2：图谱层（W3–W4）**

```
W3:
  - [ ] 规则关系抽取器（正则匹配文档编号引用）
  - [ ] ICD 枢纽绑定（参数→引用文档映射）
  - [ ] DocumentGraph 查询 API 实现
  - [ ] 上游/下游追溯查询

W4:
  - [ ] 语义检索（chromadb 相似度查询）
  - [ ] 过期引用检测（find_stale_references）
  - [ ] 图谱 API 端点（GET /api/graph/*）
  - [ ] 单元测试：fixture 文档间至少 15 条关系正确识别
```

**S3：对齐引擎（W5–W6）**

```
W5:
  - [ ] Ollama 安装 + Gemma 4 模型部署验证
  - [ ] LLM 客户端封装（litellm）
  - [ ] System Prompt 设计与调优
  - [ ] 草稿生成器核心流程（检索→组装→生成）

W6:
  - [ ] 引注解析器（从 LLM 输出中提取引注标记）
  - [ ] 冲突检测器
  - [ ] 草稿 API 端点（POST /api/draft/generate）
  - [ ] 集成测试：对 fixture 场景生成完整测试大纲草稿
```

**S4：质量门 + 变更分析（W7–W8）**

```
W7:
  - [ ] Evaluator 基类 + Bus 架构
  - [ ] EA.1–EA.5 实现
  - [ ] EB.1 实现
  - [ ] ED.1, ED.3 实现

W8:
  - [ ] 变更影响分析器（diff → 下游查询 → 评估）
  - [ ] 变更影响 API 端点
  - [ ] 集成测试：预埋的 T1–T4 不一致全部被检测
  - [ ] Evaluator API 端点
```

**S5：WebUI + 验收（W9–W10）**

```
W9:
  - [ ] FastAPI + Jinja2 + HTMX 项目结构
  - [ ] Tailwind/DaisyUI 集成
  - [ ] P1 首页/仪表盘
  - [ ] P2 文档库（上传 + 浏览 + 详情）
  - [ ] P3 草稿工作台（3 步流程）

W10:
  - [ ] P4 变更影响分析页
  - [ ] P5 文档图谱可视化（vis-network.js）
  - [ ] 端到端测试：完整用户场景走通
  - [ ] README.md + 快速开始文档
  - [ ] Docker Compose 部署脚本
```

---

## 10. 部署方案

### 10.1 最小硬件要求

| 组件     | 要求                                     |
| -------- | ---------------------------------------- |
| GPU      | NVIDIA RTX 4090 (24GB) 或 Apple M4 Max  |
| RAM      | 32 GB                                    |
| 存储     | 50 GB 可用空间（模型 15GB + 数据 + 系统） |
| OS       | Linux / macOS / Windows (WSL2)           |

### 10.2 Docker Compose 部署

```yaml
# docker-compose.yml
services:
  harnetics:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data          # SQLite + chromadb 数据
      - ./documents:/app/documents # 文档存储
    environment:
      - OLLAMA_HOST=http://ollama:11434
      - DATABASE_URL=sqlite:///app/data/harnetics.db
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  ollama_data:
```

### 10.3 快速启动（非 Docker）

```bash
# 1. 克隆项目
git clone https://github.com/xxx/harnetics.git
cd harnetics

# 2. 安装依赖
pip install -e .

# 3. 确保 Ollama 已安装并运行
ollama pull gemma4:26b-it-a4b-q4_K_M

# 4. 初始化数据库
harnetics init

# 5. 导入 fixture 文档（可选，用于体验）
harnetics ingest ./fixtures/ --recursive

# 6. 启动 Web 服务
harnetics serve --port 8080

# 7. 打开浏览器
open http://localhost:8080
```

---

## 11. 更新后的项目结构

```
harnetics/
├── pyproject.toml
├── README.md
├── docker-compose.yml
├── Dockerfile
│
├── harnetics/
│   ├── __init__.py
│   ├── config.py                # 配置管理
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py          # DocumentNode, Section, DocumentEdge
│   │   ├── icd.py               # ICDParameter
│   │   ├── draft.py             # DraftRequest, AlignedDraft, Citation, Conflict
│   │   └── impact.py            # ImpactReport, ImpactedDoc, SectionDiff
│   │
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── markdown_parser.py
│   │   ├── yaml_parser.py
│   │   └── icd_parser.py        # ICD YAML 专用解析器
│   │
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── store.py             # SQLite 存储
│   │   ├── schema.sql           # 建表脚本
│   │   ├── indexer.py           # 文档入库 + 关系抽取
│   │   ├── query.py             # DocumentGraph 查询 API
│   │   └── embeddings.py        # chromadb 向量嵌入
│   │
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── draft_generator.py   # 草稿生成器
│   │   ├── impact_analyzer.py   # 变更影响分析器
│   │   └── conflict_detector.py # 冲突检测
│   │
│   ├── evaluators/
│   │   ├── __init__.py
│   │   ├── base.py              # BaseEvaluator + EvaluatorBus
│   │   ├── citation.py          # EA.1–EA.5
│   │   ├── icd.py               # EB.1
│   │   └── ai_quality.py        # ED.1, ED.3
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py            # LLM 调用封装（litellm + Ollama）
│   │   └── prompts.py           # System Prompt 模板
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py               # FastAPI app 入口
│   │   ├── routes/
│   │   │   ├── documents.py     # /api/documents/*
│   │   │   ├── graph.py         # /api/graph/*
│   │   │   ├── draft.py         # /api/draft/*
│   │   │   ├── impact.py        # /api/impact/*
│   │   │   ├── evaluate.py      # /api/evaluate/*
│   │   │   └── status.py        # /api/status
│   │   └── deps.py              # 依赖注入
│   │
│   ├── web/
│   │   ├── __init__.py
│   │   ├── routes.py            # 页面路由
│   │   ├── templates/
│   │   │   ├── base.html        # 基础布局（导航栏 + 侧栏）
│   │   │   ├── index.html       # 首页/仪表盘
│   │   │   ├── documents/
│   │   │   │   ├── list.html    # 文档库列表
│   │   │   │   ├── upload.html  # 上传对话框（HTMX partial）
│   │   │   │   └── detail.html  # 文档详情
│   │   │   ├── draft/
│   │   │   │   ├── workspace.html  # 草稿工作台
│   │   │   │   ├── progress.html   # 生成进度（HTMX partial）
│   │   │   │   └── result.html     # 草稿结果
│   │   │   ├── impact/
│   │   │   │   ├── analyze.html    # 变更影响分析
│   │   │   │   └── report.html     # 影响报告
│   │   │   └── graph/
│   │   │       └── view.html       # 文档图谱可视化
│   │   └── static/
│   │       ├── css/
│   │       │   └── app.css      # Tailwind 编译输出
│   │       ├── js/
│   │       │   ├── htmx.min.js
│   │       │   └── graph.js     # vis-network.js 图谱交互
│   │       └── tailwind.config.js
│   │
│   └── cli/
│       ├── __init__.py
│       └── main.py              # CLI 入口（init/ingest/serve）
│
├── tests/
│   ├── conftest.py              # fixture 数据加载
│   ├── test_parsers/
│   │   ├── test_markdown_parser.py
│   │   ├── test_yaml_parser.py
│   │   └── test_icd_parser.py
│   ├── test_graph/
│   │   ├── test_store.py
│   │   ├── test_indexer.py
│   │   └── test_query.py
│   ├── test_engine/
│   │   ├── test_draft_generator.py
│   │   └── test_impact_analyzer.py
│   ├── test_evaluators/
│   │   ├── test_citation.py
│   │   ├── test_icd.py
│   │   └── test_ai_quality.py
│   ├── test_api/
│   │   └── test_routes.py
│   └── test_e2e/
│       └── test_mvp_scenario.py  # 端到端场景测试
│
├── fixtures/                     # MVP mock 数据（10 份文档）
│   ├── README.md                 # fixture 文档说明
│   ├── requirements/
│   │   └── DOC-SYS-001.md
│   ├── icd/
│   │   └── DOC-ICD-001.yaml
│   ├── templates/
│   │   └── DOC-TPL-001.md
│   ├── design/
│   │   ├── DOC-DES-001.md
│   │   └── DOC-OVR-001.md
│   ├── test_plans/
│   │   ├── DOC-TST-001.md
│   │   ├── DOC-TST-002.md
│   │   └── DOC-TST-003.md
│   └── quality/
│       ├── DOC-QAP-001.md
│       └── DOC-FMA-001.md
│
└── docs/
    ├── architecture.md           # → 指向 docs/design-docs/aerospace-mvp-v3.md
    ├── prd.md                    # → 指向本文档
    └── quickstart.md
```

---

## 12. 依赖清单

```toml
# pyproject.toml [project.dependencies]
[project]
name = "harnetics"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    # Web
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "jinja2>=3.1",
    "python-multipart>=0.0.9",   # 文件上传

    # LLM
    "litellm>=1.40",

    # 文档解析
    "pyyaml>=6.0",

    # 向量索引
    "chromadb>=0.5",
    "sentence-transformers>=3.0",

    # 数据库
    # SQLite 内置，无需额外依赖

    # 工具
    "typer>=0.12",               # CLI
    "rich>=13.0",                # 终端美化
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "httpx>=0.27",               # 测试 API
    "ruff>=0.5",                 # lint
]
```

---

## 13. 不做清单（MVP 明确排除）

| 不做                     | 原因                                        |
| ------------------------ | ------------------------------------------- |
| Word/Excel/PDF 解析      | Phase 1 再加，MVP 只支持 Markdown + YAML    |
| 用户认证/权限            | MVP 单机部署，Phase 3 才需要                |
| 多项目/多型号            | MVP 只做天行一号一个项目                    |
| LLM 辅助关系抽取        | Phase 1 再加，MVP 只用规则匹配              |
| DOORS/PDM 集成           | Phase 3                                     |
| 实时协作编辑             | 不做——文档编辑仍在 Word 中完成             |
| 自动审批工作流           | 不做——审批流程不变                         |
| 国际化（英文界面）       | MVP 只做中文界面                            |
| 移动端适配               | MVP 只支持桌面浏览器                        |

---

## 14. Fixture 数据说明

10 份 mock 文档存放在 `fixtures/` 目录下，模拟天行一号运载火箭 TQ-12 发动机项目的真实文档体系。

### 14.1 文档间关系图

```
DOC-SYS-001 (系统需求)
    │
    ├─ derived_from ──→ DOC-ICD-001 (ICD)
    │                      │
    ├─ traces_to ─────→ DOC-OVR-001 (总体方案)
    │                      │
    ├─ traces_to ─────→ DOC-DES-001 (动力设计)
    │                      ├─ constrained_by ──→ DOC-ICD-001
    │                      ├─ references ──────→ DOC-FMA-001
    │                      └─ traces_to ───────→ DOC-TST-001
    │                                             DOC-TST-002
    │                                             DOC-TST-003
    │
    └─ references ────→ DOC-QAP-001 (质量计划)

DOC-TPL-001 (测试模板)
    └─ constrained_by ──→ DOC-TST-001, DOC-TST-002, DOC-TST-003

DOC-FMA-001 (FMEA)
    └─ references ──→ DOC-QAP-001
```

### 14.2 关键跨文档参数追踪

| 参数              | DOC-SYS-001 | DOC-ICD-001 | DOC-DES-001 | DOC-TST-001 | DOC-TST-003 |
| ----------------- | ------------ | ------------ | ------------ | ------------ | ------------ |
| 地面推力 (kN)     | ≥650         | 650 ±3%      | 650          | 650          | **600** ⚠️   |
| 真空比冲 (s)      | ≥315         | ≥315         | 316.5        | 315          | 310          |
| 混合比            | 3.5:1        | 3.5:1 ±5%    | 3.5:1        | 3.5:1        | 3.5:1        |
| 燃烧室压力 (MPa)  | —            | 10.0         | 10.0         | 10.0         | **9.5** ⚠️   |
| 发动机干重 (kg)   | ≤480         | ≤480         | 470          | —            | —            |

⚠️ 标记的值与当前 ICD v2.3 不一致，是预埋的测试用例。
