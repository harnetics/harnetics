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
  subject: string
  eval_summary: {
    pass: number
    warn: number
    block: number
  } | null
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

export interface AffectedSection {
  section_id: string
  heading: string
  reason: string
}

export interface ImpactReport {
  report_id: string
  trigger_doc_id: string
  old_version: string
  new_version: string
  summary: string
  analysis_mode?: string
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
  affected_sections: AffectedSection[]
  severity: 'critical' | 'major' | 'minor'
  analysis_mode?: string
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
  // embedding 字段
  embedding_available: boolean
  embedding_model: string
  embedding_base_url: string
  embedding_error: string
  embedding_collection_reset: boolean
  sections_indexed: number
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
// 进化域 (GEP 自进化)
// ================================================================

export interface EvolutionSignal {
  timestamp: string
  draft_id: string
  subject: string
  outcome: 'pass' | 'blocked'
  tags: string[]
  eval_summary: Record<string, number>
  context_quality: { sections_used: number; icd_params_used: number }
  failed_checks: string[]
}

export interface EvolutionStats {
  total_signals: number
  current_strategy: string
  strategy_label: string
  blocked_ratio: number
  evolver_installed: boolean
  recent: EvolutionSignal[]
  tag_counts: Record<string, number>
  check_failure_counts: Record<string, number>
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

export interface DocumentSearchResult extends Document {
  relevance_score: number
}

export interface DocumentSearchResponse {
  results: DocumentSearchResult[]
  analysis_mode: 'ai_vector' | 'keyword'
}

// ================================================================
// 夹具测试域 (Fixture Test Lab)
// ================================================================

export interface FixtureScenario {
  scenario_id: string
  evaluator: string
  label: string
  expected_outcome: 'pass' | 'warn' | 'fail'
  fixture_path: string
}

export interface FixtureRunResult {
  scenario_id: string
  draft_id: string
  outcome: 'pass' | 'blocked'
  expected_outcome: 'pass' | 'warn' | 'fail'
  match: boolean
  eval_results: EvalResult[]
  error: string
}

export interface FixtureImportResult {
  status: string
  imported: number
  doc_ids: string[]
}

export interface FixtureRunAllResult {
  total: number
  passed: number
  failed: number
  results: FixtureRunResult[]
}

// ================================================================
// 文档比对域 (Doc Comparison Review)
// ================================================================

export interface ComparisonFinding {
  finding_id: string
  chapter: string
  requirement_heading: string
  requirement_content: string
  status: 'covered' | 'partial' | 'missing' | 'unclear'
  detail: string
  requirement_ref: string
  response_ref: string
}

export interface ComparisonSessionSummary {
  session_id: string
  req_filename: string
  resp_filename: string
  status: 'pending' | 'completed' | 'failed'
  created_at: string
  findings_count: number
  covered: number
  partial: number
  missing: number
  unclear: number
}

export interface ComparisonSectionItem {
  section_id: string
  doc_id: string
  heading: string
  content: string
  level: number
  order_index: number
}

export interface ComparisonSession {
  session_id: string
  req_filename: string
  resp_filename: string
  req_sections: ComparisonSectionItem[]
  resp_sections: ComparisonSectionItem[]
  analysis_md: string
  findings: ComparisonFinding[]
  status: 'pending' | 'completed' | 'failed'
  created_at: string
}

