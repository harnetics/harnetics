/**
 * [INPUT]: 无外部依赖
 * [OUTPUT]: 对外提供全部前端领域类型 (Document/Section/Edge/Draft/Impact/Dashboard)
 * [POS]: types 的唯一入口，被 lib/api.ts 和各 page 组件消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */

// ================================================================
// 文档域
// ================================================================

export interface Document {
  doc_id: string
  title: string
  doc_type: string
  department: string
  system_level: string
  engineering_phase: string
  version: string
  status: string
  created_at: string
  updated_at: string
}

export interface Section {
  section_id: string
  doc_id: string
  heading: string
  content: string
  level: number
  order_index: number
}

export interface DocumentEdge {
  edge_id: number
  source_doc_id: string
  target_doc_id: string
  relation: string
  confidence: number
}

export interface ICDParameter {
  param_id: string
  doc_id: string
  name: string
  interface_type: string
  subsystem_a: string
  subsystem_b: string
  value: string
  unit: string
  range: string
  owner_department: string
  version: string
}

// ================================================================
// 草稿域
// ================================================================

export interface Draft {
  draft_id: string
  status: string
  content_md: string
  citations: Citation[]
  conflicts: Conflict[]
  eval_results: EvalResult[]
  generated_by: string
  created_at: string
}

export interface DraftSummary {
  draft_id: string
  status: string
  generated_by: string
  created_at: string
}

export interface Citation {
  source_doc_id: string
  source_section_id: string
  quote: string
  confidence: number
}

export interface Conflict {
  doc_a_id: string
  doc_b_id: string
  description: string
  severity: string
}

export interface EvalResult {
  evaluator_id: string
  name: string
  status: string
  level: string
  detail: string
  locations: string[]
}

// ================================================================
// 影响分析域
// ================================================================

export interface ImpactReport {
  report_id: string
  trigger_doc_id: string
  old_version: string
  new_version: string
  summary: string
  changed_sections: ChangedSection[]
  impacted_docs: ImpactedDoc[]
  created_at: string
}

export interface ChangedSection {
  section_id: string
  heading: string
  change_type: string
  summary: string
}

export interface ImpactedDoc {
  doc_id: string
  title: string
  relation: string
  affected_sections: string[]
  severity: string
}

// ================================================================
// 仪表盘域
// ================================================================

export interface DashboardStats {
  documents: number
  drafts: number
  icd_parameters: number
  impact_reports: number
  stale_references: number
  llm_available: boolean
  eval_pass_rate: number | null
  eval_pass: number
  eval_blocked: number
}

// ================================================================
// 图谱域 (vis-network 格式)
// ================================================================

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface GraphNode {
  id: string
  label: string
  group: string
}

export interface GraphEdge {
  from: string
  to: string
  label: string
  arrows: string
}

// ================================================================
// API 响应包装
// ================================================================

export interface DocumentListResponse {
  total: number
  page: number
  per_page: number
  documents: Document[]
}

export interface DocumentDetailResponse {
  document: Document
  sections: Section[]
  upstream: DocumentEdge[]
  downstream: DocumentEdge[]
  icd_parameters: ICDParameter[]
}
