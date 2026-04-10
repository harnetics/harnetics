/**
 * [INPUT]: 依赖 @/types 的全部接口定义
 * [OUTPUT]: 对外提供 fetch 封装函数 (fetchDocuments/fetchDocument/fetchDraft/generateDraft 等)
 * [POS]: lib 的 API 通信层，被各 page 组件调用，统一处理请求/错误
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */

import type {
  DocumentListResponse,
  DocumentDetailResponse,
  DraftSummary,
  Draft,
  ImpactReport,
  DashboardStats,
  GraphData,
  DocumentEdge,
} from '@/types'

// ================================================================
// 通用请求
// ================================================================

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText}: ${body}`)
  }
  return res.json() as Promise<T>
}

// ================================================================
// 文档
// ================================================================

export interface DocumentListParams {
  department?: string
  doc_type?: string
  system_level?: string
  status?: string
  q?: string
  page?: number
  per_page?: number
}

export function fetchDocuments(params: DocumentListParams = {}): Promise<DocumentListResponse> {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== '') qs.set(k, String(v))
  }
  const query = qs.toString()
  return request<DocumentListResponse>(`/api/documents${query ? `?${query}` : ''}`)
}

export function fetchDocument(docId: string): Promise<DocumentDetailResponse> {
  return request<DocumentDetailResponse>(`/api/documents/${encodeURIComponent(docId)}`)
}

// ================================================================
// 草稿
// ================================================================

export function fetchDrafts(): Promise<DraftSummary[]> {
  return request<DraftSummary[]>('/api/draft')
}

export function fetchDraft(draftId: string): Promise<Draft> {
  return request<Draft>(`/api/draft/${encodeURIComponent(draftId)}`)
}

export interface GenerateDraftRequest {
  subject: string
  related_doc_ids?: string[]
  template_id?: string
  extra?: Record<string, unknown>
}

export function generateDraft(req: GenerateDraftRequest): Promise<Draft> {
  return request<Draft>('/api/draft/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

// ================================================================
// 评估
// ================================================================

export function runEvaluation(draftId: string) {
  return request<{ draft_id: string; status: string; has_blocking_failures: boolean; results: unknown[] }>(
    `/api/evaluate/${encodeURIComponent(draftId)}`,
    { method: 'POST' },
  )
}

// ================================================================
// 影响分析
// ================================================================

export function fetchImpactReports(): Promise<ImpactReport[]> {
  return request<ImpactReport[]>('/api/impact')
}

export function fetchImpactReport(reportId: string): Promise<ImpactReport> {
  return request<ImpactReport>(`/api/impact/${encodeURIComponent(reportId)}`)
}

export interface AnalyzeImpactRequest {
  doc_id: string
  old_version?: string
  new_version?: string
  changed_section_ids?: string[]
}

export function analyzeImpact(req: AnalyzeImpactRequest): Promise<ImpactReport> {
  return request<ImpactReport>('/api/impact/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
}

// ================================================================
// 图谱
// ================================================================

export interface GraphParams {
  department?: string
  system_level?: string
}

export function fetchGraph(params: GraphParams = {}): Promise<GraphData> {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== '') qs.set(k, String(v))
  }
  const query = qs.toString()
  return request<GraphData>(`/api/graph${query ? `?${query}` : ''}`)
}

export function fetchGraphEdges(): Promise<DocumentEdge[]> {
  return request<DocumentEdge[]>('/api/graph/edges')
}

// ================================================================
// 仪表盘
// ================================================================

export function fetchDashboardStats(): Promise<DashboardStats> {
  return request<DashboardStats>('/api/status')
}
