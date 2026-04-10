// ────────────────────────────────────────────────────────────
// Central mock data for Harnetics Prototype 2
// Mirrors data model from docs/design-docs/aerospace-mvp-v3.md
// ────────────────────────────────────────────────────────────

export type DocStatus = 'Draft' | 'UnderReview' | 'Approved' | 'Superseded'
export type ImpactLevel = 'Critical' | 'Major' | 'Minor'
export type EvalLevel = 'Blocker' | 'Warning' | 'Pass'

export interface Document {
  id: string
  doc_id: string
  title: string
  department: string
  doc_type: string
  system_level: string
  engineering_phase: string
  version: string
  status: DocStatus
  last_updated: string
  section_count: number
}

export interface Section {
  section_id: string
  heading: string
  content: string
  level: number
}

export interface DocumentEdge {
  source: string
  target: string
  relation: 'traces_to' | 'references' | 'derived_from' | 'constrained_by' | 'supersedes' | 'impacts'
}

export interface EvalResult {
  id: string
  label: string
  level: EvalLevel
  message: string
}

export interface Citation {
  anchor: string
  source_doc_id: string
  source_section: string
  snippet: string
}

export interface ImpactedDoc {
  doc_id: string
  title: string
  department: string
  impact_level: ImpactLevel
  affected_sections: string[]
  reason: string
  current_ref_version: string
}

export interface ImpactReport {
  id: string
  trigger_doc_id: string
  trigger_title: string
  old_version: string
  new_version: string
  date: string
  critical: number
  major: number
  minor: number
  impacted: ImpactedDoc[]
}

// ─── Documents ───────────────────────────────────────────────
export const documents: Document[] = [
  {
    id: '1',
    doc_id: 'DOC-ICD-001',
    title: '全局接口控制文档 (Global ICD)',
    department: '技术负责人',
    doc_type: 'ICD',
    system_level: '系统层',
    engineering_phase: '设计',
    version: 'v2.3',
    status: 'Approved',
    last_updated: '2026-04-01',
    section_count: 12,
  },
  {
    id: '2',
    doc_id: 'DOC-SYS-001',
    title: '动力系统总体需求规格说明',
    department: '系统工程部',
    doc_type: '需求文档',
    system_level: '系统层',
    engineering_phase: '需求',
    version: 'v3.1',
    status: 'Approved',
    last_updated: '2026-04-06',
    section_count: 18,
  },
  {
    id: '3',
    doc_id: 'DOC-TST-002',
    title: 'TQ-12 发动机地面试车测试大纲',
    department: '动力系统部',
    doc_type: '测试大纲',
    system_level: '分系统层',
    engineering_phase: '测试',
    version: 'v1.2',
    status: 'UnderReview',
    last_updated: '2026-04-05',
    section_count: 9,
  },
  {
    id: '4',
    doc_id: 'DOC-DES-001',
    title: '动力系统分系统详细设计文档',
    department: '动力系统部',
    doc_type: '设计文档',
    system_level: '分系统层',
    engineering_phase: '设计',
    version: 'v2.0',
    status: 'Approved',
    last_updated: '2026-03-20',
    section_count: 24,
  },
  {
    id: '5',
    doc_id: 'DOC-FMA-001',
    title: '推进系统故障模式与影响分析 (FMEA)',
    department: '质量与可靠性部',
    doc_type: '分析报告',
    system_level: '分系统层',
    engineering_phase: '测试',
    version: 'v1.0',
    status: 'Draft',
    last_updated: '2026-04-02',
    section_count: 7,
  },
  {
    id: '6',
    doc_id: 'DOC-QAP-001',
    title: '质量保证计划',
    department: '质量与可靠性部',
    doc_type: '管理文档',
    system_level: '全层级',
    engineering_phase: '全流程',
    version: 'v1.0',
    status: 'Approved',
    last_updated: '2026-02-28',
    section_count: 11,
  },
  {
    id: '7',
    doc_id: 'DOC-TPL-001',
    title: '测试大纲标准模板',
    department: '试验与验证部',
    doc_type: '模板',
    system_level: '全层级',
    engineering_phase: '测试',
    version: 'v1.0',
    status: 'Approved',
    last_updated: '2026-01-15',
    section_count: 6,
  },
  {
    id: '8',
    doc_id: 'DOC-OVR-001',
    title: '火箭总体方案设计文档',
    department: '总体设计部',
    doc_type: '设计文档',
    system_level: '系统层',
    engineering_phase: '设计',
    version: 'v1.0',
    status: 'Approved',
    last_updated: '2026-02-10',
    section_count: 16,
  },
]

// ─── Sections (for DOC-ICD-001 detail) ───────────────────────
export const icdSections: Section[] = [
  {
    section_id: 's1',
    heading: '1. 文档目的与范围',
    content:
      '本文档定义了 TQ-12 型发动机分系统与其他分系统（GNC、结构、测控）之间的全部接口参数及约束条件，适用于动力分系统详细设计及试验阶段。',
    level: 1,
  },
  {
    section_id: 's2',
    heading: '2. 参考文档',
    content:
      '- DOC-SYS-001 v3.1 动力系统总体需求规格说明\n- DOC-OVR-001 v1.0 火箭总体方案设计文档\n- GJB 1408 液体火箭发动机通用规范',
    level: 1,
  },
  {
    section_id: 's3',
    heading: '3. 推力控制接口',
    content:
      '3.1 额定推力：1200 kN ± 5%\n3.2 推力调节范围：60%–105% 额定推力\n3.3 推力响应时间：< 0.1 s（10% 阶跃输入）\n3.4 供给压力（LOX）：8.5 MPa ± 0.2 MPa\n3.5 供给压力（Fuel）：7.2 MPa ± 0.2 MPa',
    level: 1,
  },
  {
    section_id: 's4',
    heading: '4. 电气接口定义',
    content:
      '4.1 Y-L32 供电接口：28 VDC ± 2V，最大电流 5A\n4.2 测控数据总线：CAN 2.0B，1 Mbps\n4.3 故障隔离继电器（FIR）驱动电流：≤ 200 mA',
    level: 1,
  },
  {
    section_id: 's5',
    heading: '5. 机械接口',
    content:
      '5.1 发动机安装法兰：φ800 mm，8-M20 螺栓均布\n5.2 推进剂供给管连接：KJ-24 快插接头（符合 GJB 2482）',
    level: 1,
  },
]

// ─── Graph edges ──────────────────────────────────────────────
export const graphEdges: DocumentEdge[] = [
  { source: 'DOC-SYS-001', target: 'DOC-ICD-001', relation: 'derived_from' },
  { source: 'DOC-DES-001', target: 'DOC-ICD-001', relation: 'constrained_by' },
  { source: 'DOC-TST-002', target: 'DOC-ICD-001', relation: 'references' },
  { source: 'DOC-TST-002', target: 'DOC-SYS-001', relation: 'traces_to' },
  { source: 'DOC-TST-002', target: 'DOC-DES-001', relation: 'references' },
  { source: 'DOC-TST-002', target: 'DOC-TPL-001', relation: 'derived_from' },
  { source: 'DOC-FMA-001', target: 'DOC-ICD-001', relation: 'constrained_by' },
  { source: 'DOC-FMA-001', target: 'DOC-SYS-001', relation: 'traces_to' },
  { source: 'DOC-DES-001', target: 'DOC-OVR-001', relation: 'derived_from' },
  { source: 'DOC-DES-001', target: 'DOC-SYS-001', relation: 'traces_to' },
]

// ─── Impact Report ────────────────────────────────────────────
export const impactReport: ImpactReport = {
  id: 'rpt-001',
  trigger_doc_id: 'DOC-SYS-001',
  trigger_title: '动力系统总体需求规格说明',
  old_version: 'v3.0',
  new_version: 'v3.1',
  date: '2026-04-06',
  critical: 2,
  major: 3,
  minor: 1,
  impacted: [
    {
      doc_id: 'DOC-ICD-001',
      title: '全局接口控制文档',
      department: '技术负责人',
      impact_level: 'Critical',
      affected_sections: ['§3.2 推力控制接口', '§4.1 Y-L32 线束定义'],
      reason:
        'v3.1 移除「备份推力伺服反馈」信号，ICD 中对应的硬件电气接口需同步修减，否则下游分系统将产生冗余线缆约束。',
      current_ref_version: 'v2.2',
    },
    {
      doc_id: 'DOC-TST-002',
      title: 'TQ-12 发动机地面试车测试大纲',
      department: '动力系统部',
      impact_level: 'Critical',
      affected_sections: ['§4.1 冷试车操作时序', '§5.2 中止判据'],
      reason:
        'v3.1 将预冷起始时间轴从 T-40s 提前至 T-60s（新增 LOX 氦气吹除步骤），测试大纲第 4 节的操作时间轴需全面修订。',
      current_ref_version: 'v3.0',
    },
    {
      doc_id: 'DOC-FMA-001',
      title: '推进系统 FMEA 报告',
      department: '质量与可靠性部',
      impact_level: 'Major',
      affected_sections: ['§2 故障模式清单'],
      reason:
        '需求新增一个冗余隔离阀参数（VLV-R3），要求同步在 FMEA 中补充该阀门单点失效及共因失效分析条目。',
      current_ref_version: 'v3.0',
    },
    {
      doc_id: 'DOC-DES-001',
      title: '动力系统分系统详细设计文档',
      department: '动力系统部',
      impact_level: 'Major',
      affected_sections: ['§3 接口设计说明', '§6 可靠性设计'],
      reason:
        '供给压力约束更新（LOX 管路 8.3→8.5 MPa），设计文档中管路壁厚选型计算需重新校核。',
      current_ref_version: 'v3.0',
    },
    {
      doc_id: 'DOC-OVR-001',
      title: '火箭总体方案设计文档',
      department: '总体设计部',
      impact_level: 'Major',
      affected_sections: ['§5.2 动力分系统接口要求'],
      reason: '总体方案中引用的推力额定值需同步更新至最新指标。',
      current_ref_version: 'v3.0',
    },
    {
      doc_id: 'DOC-QAP-001',
      title: '质量保证计划',
      department: '质量与可靠性部',
      impact_level: 'Minor',
      affected_sections: ['§8 文档控制程序'],
      reason: '更新文档版本历史记录格式，minor 描述性调整。',
      current_ref_version: 'v3.0',
    },
  ],
}

// ─── Draft eval results ───────────────────────────────────────
export const evalResults: EvalResult[] = [
  { id: 'EA.1', label: 'EA.1 指标来源引用', level: 'Pass', message: '所有技术指标均已追溯到源文档章节。' },
  { id: 'EA.2', label: 'EA.2 引用真实性', level: 'Pass', message: '所有引注指向的文档/章节均在图谱中存在。' },
  {
    id: 'EA.3',
    label: 'EA.3 版本时效性',
    level: 'Warning',
    message: '第 2.1 节引用 DOC-ICD-001 v2.2（当前最新为 v2.3）。',
  },
  { id: 'EA.4', label: 'EA.4 无循环引用', level: 'Pass', message: '未检测到循环引用。' },
  {
    id: 'EA.5',
    label: 'EA.5 引注覆盖率',
    level: 'Warning',
    message: '技术性段落引注覆盖率 74%，低于阈值 80%，第 5 节存在未引注的技术描述。',
  },
  { id: 'EB.1', label: 'EB.1 ICD 参数一致性', level: 'Pass', message: '所有接口参数与 ICD 定义一致。' },
  {
    id: 'EB.2',
    label: 'EB.2 ICD 版本引用',
    level: 'Warning',
    message: '草稿声明 ICD v2.2，但图谱记录的最新版本为 v2.3。',
  },
  { id: 'ED.1', label: 'ED.1 无凭空捏造', level: 'Pass', message: '所有数字可追溯到源文档。' },
  { id: 'ED.2', label: 'ED.2 无错误归因', level: 'Pass', message: '引注内容与原文语义一致。' },
  { id: 'ED.3', label: 'ED.3 冲突标记', level: 'Pass', message: '所有检测到的上游冲突已在草稿中标记。' },
]

// ─── Draft citations ──────────────────────────────────────────
export const draftCitations: Citation[] = [
  {
    anchor: '§1.2 额定推力',
    source_doc_id: 'DOC-ICD-001',
    source_section: '§3.1 推力接口参数',
    snippet: '额定推力：1200 kN ± 5%',
  },
  {
    anchor: '§2.1 供给压力',
    source_doc_id: 'DOC-ICD-001',
    source_section: '§3.4 供给压力',
    snippet: 'LOX 供给压力：8.5 MPa ± 0.2 MPa',
  },
  {
    anchor: '§3.1 预冷时序',
    source_doc_id: 'DOC-SYS-001',
    source_section: '§4.2 地面试车约束',
    snippet: '预冷起始时间 T-60s（v3.1 更新）',
  },
  {
    anchor: '§4 验收标准',
    source_doc_id: 'DOC-ICD-001',
    source_section: '§3.3 比冲/混合比',
    snippet: '比冲 312 s ± 2 s；混合比 2.56 ± 0.05',
  },
  {
    anchor: '§2.2 测控接口',
    source_doc_id: 'DOC-ICD-001',
    source_section: '§4.1 电气接口',
    snippet: 'Y-L32 供电 28 VDC',
  },
]

// ─── Draft content (Markdown) ─────────────────────────────────
export const draftMarkdown = `# TQ-12 发动机地面试车测试大纲

> **AI 草稿 · 工程师审核版** | 部门：动力系统部 | 类型：测试大纲 | 层级：分系统层

---

## 1. 试车目的与范围

本测试大纲规定了 TQ-12 型液氧/煤油发动机在常温地面条件下开展热试车的操作流程、安全边界及验收标准，适用于正式点火前的 CFVT (Cold Flow Verification Test) 与热调试阶段。

**引注** ← DOC-SYS-001 §2.1 发动机性能指标要求

---

## 2. 前置条件

### 2.1 设备状态确认

- [ ] LOX 供给管路压力：8.5 MPa ± 0.2 MPa **[引注 ← DOC-ICD-001 §3.4]**
- [ ] Fuel 供给管路压力：7.2 MPa ± 0.2 MPa **[引注 ← DOC-ICD-001 §3.5]**
- [ ] 测控接口 Y-L32 供电确认开启（28 VDC）**[引注 ← DOC-ICD-001 §4.1]**

> ⚠️ **冲突告警（EB.2）**：本草稿引用 DOC-ICD-001 v2.2，但当前最新版为 v2.3——请确认 Y-L32 接口是否在 v2.3 中发生变更后再签发。

### 2.2 安全检查清单

- [ ] 推力室冷却通道已完成氮气吹除（参见 DOC-QAP-001 §4 安全规程）
- [ ] 逃逸警报系统已联调完毕

---

## 3. 试车时序

### 3.1 预冷阶段（T-60s 起）

> ℹ️ **版本更新说明**：DOC-SYS-001 v3.1 将预冷起始时间从 T-40s 提前至 T-60s，本草稿已采用最新参数。**[引注 ← DOC-SYS-001 §4.2]**

| 时间节点 | 操作步骤 | 责任岗位 |
|---------|---------|---------|
| T-60s | 开始 LOX 供给管路预冷 | 推进剂操作员 |
| T-45s | 发动机进入准备就绪状态，确认遥测数据链路正常 | 测控操作员 |
| T-30s | 确认推力室冷却剂流量达标 | 发动机操作员 |
| T-10s | 启动点火时序，触发 Y-L32 点火指令 | 指挥员 |
| T-0s | 点火 | — |

---

## 4. 验收标准

| 参数 | 标称值 | 允差 | 来源引注 |
|-----|-------|-----|---------|
| 额定推力 | 1200 kN | ±5% | DOC-ICD-001 §3.1 |
| 比冲 | 312 s | ±2 s | DOC-ICD-001 §3.3 |
| 混合比 | 2.56 | ±0.05 | DOC-ICD-001 §3.3 |
| 燃烧稳定性 | ≥ 3σ | — | DOC-SYS-001 §2.3 |

---

## 5. 中止判据

> ⚠️ **引注覆盖率不足（EA.5）**：本节尚未完整引注源文档，部分中止门限来源需工程师手动补充。

- 推力偏离额定值超过 ±10%，立即中止
- LOX 供给压力跌落至 8.0 MPa 以下，中止
- 测控链路中断，立即中止并执行急停程序
`
