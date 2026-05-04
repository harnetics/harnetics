/**
 * [INPUT]: 依赖 @/types 的全部接口定义
 * [OUTPUT]: 对外提供 fetch 封装函数 (fetchDocuments/uploadDocument/fetchDeveloperLogs/analyzeComparisonStream/analyzeComparison4Step 等)
 * [POS]: lib 的 API 通信层，被各 page 组件调用，统一处理请求/错误
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */

import type {
  DocumentListResponse,
  DocumentDetailResponse,
  DocumentSearchResponse,
  DraftSummary,
  Draft,
  ImpactReport,
  DashboardStats,
  GraphData,
  DocumentEdge,
  EvolutionStats,
  FixtureScenario,
  FixtureRunResult,
  FixtureImportResult,
  FixtureRunAllResult,
  ComparisonSession,
  ComparisonSessionSummary,
  ComparisonProgressEvent,
  Comparison4StepEvent,
  DeveloperLogs,
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

async function streamSse<T>(
  url: string,
  body: BodyInit,
  onEvent: (event: T) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(url, {
    method: 'POST',
    body,
    signal,
  })
  if (!res.ok) {
    const payload = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText}: ${payload}`)
  }
  if (!res.body) {
    throw new Error('SSE 响应流不可用')
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  const flushEvent = (rawEvent: string) => {
    const dataLines = rawEvent
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice('data:'.length).trim())

    if (dataLines.length === 0) return

    try {
      onEvent(JSON.parse(dataLines.join('\n')) as T)
    } catch {
      // 忽略非 JSON 心跳或破损分片
    }
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() ?? ''

    for (const part of parts) {
      flushEvent(part)
    }
  }

  if (buffer.trim()) {
    flushEvent(buffer)
  }
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

export function searchDocuments(query: string, topK = 10): Promise<DocumentSearchResponse> {
  const qs = new URLSearchParams({ q: query, top_k: String(topK) })
  return request<DocumentSearchResponse>(`/api/documents/search?${qs}`)
}

export interface UploadResult {
  status: string
  doc_id: string
  title: string
}

export async function uploadDocument(file: File): Promise<UploadResult> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch('/api/documents/upload', { method: 'POST', body: form })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText}: ${body}`)
  }
  return res.json() as Promise<UploadResult>
}

export async function deleteDocument(docId: string): Promise<void> {
  const res = await fetch(`/api/documents/${encodeURIComponent(docId)}`, { method: 'DELETE' })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText}: ${body}`)
  }
}

export async function batchDeleteDocuments(docIds: string[]): Promise<{ failed: string[] }> {
  const results = await Promise.allSettled(docIds.map((id) => deleteDocument(id)))
  const failed = docIds.filter((_, i) => results[i].status === 'rejected')
  return { failed }
}

export function fetchStatus(): Promise<DashboardStats> {
  return request<DashboardStats>('/api/status')
}

export interface ReindexResult {
  status: string
  indexed_documents: number
  indexed_sections: number
}

export function reindexDocuments(): Promise<ReindexResult> {
  return request<ReindexResult>('/api/documents/reindex', { method: 'POST' })
}

// ================================================================
// 设置
// ================================================================

export interface SettingsData {
  llm_model: string
  llm_base_url: string
  llm_api_key: string
  llm_thinking_supported: string
  llm_enable_thinking: string
  embedding_model: string
  embedding_base_url: string
  embedding_api_key: string
  llm_max_tokens: string
  llm_timeout_seconds: string
  comparison_4step_batch_size: string
  comparison_step1_max_tokens: string
  comparison_step3_max_tokens: string
  comparison_step4_max_tokens: string
}

export function fetchSettings(): Promise<SettingsData> {
  return request<SettingsData>('/api/settings')
}

export function updateSettings(data: Partial<SettingsData>): Promise<SettingsData> {
  return request<SettingsData>('/api/settings', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
}

export function fetchDeveloperLogs(limit = 200): Promise<DeveloperLogs> {
  const qs = new URLSearchParams({ limit: String(limit) })
  return request<DeveloperLogs>(`/api/settings/logs?${qs}`)
}

// ================================================================
// 草稿
// ================================================================

export function fetchDrafts(): Promise<DraftSummary[]> {
  return request<DraftSummary[]>('/api/draft')
}

export async function deleteDraft(draftId: string): Promise<void> {
  const res = await fetch(`/api/draft/${encodeURIComponent(draftId)}`, { method: 'DELETE' })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText}: ${body}`)
  }
}

export function fetchDraft(draftId: string): Promise<Draft> {
  return request<Draft>(`/api/draft/${encodeURIComponent(draftId)}`)
}

export interface GenerateDraftRequest {
  subject: string
  related_doc_ids?: string[]
  template_id?: string
  source_report_id?: string
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
  return request<DashboardStats>('/api/dashboard/stats')
}

// ================================================================
// 进化 (GEP)
// ================================================================

export function fetchEvolutionStats(): Promise<EvolutionStats> {
  return request<EvolutionStats>('/api/evolution/stats')
}

export async function deleteEvolutionSignal(draftId: string): Promise<void> {
  const res = await fetch(`/api/evolution/signals/${encodeURIComponent(draftId)}`, { method: 'DELETE' })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText}: ${body}`)
  }
}

export function renameEvolutionSignal(draftId: string, subject: string): Promise<{ draft_id: string; subject: string }> {
  return request(`/api/evolution/signals/${encodeURIComponent(draftId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ subject }),
  })
}

// ================================================================
// 夹具测试实验室 (Fixture Test Lab)
// ================================================================

export function importFixtures(path = 'fixtures/evaluator-test'): Promise<FixtureImportResult> {
  return request<FixtureImportResult>('/api/fixture/import', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path }),
  })
}

export function listFixtureScenarios(): Promise<FixtureScenario[]> {
  return request<FixtureScenario[]>('/api/fixture/scenarios')
}

export function runFixtureScenario(scenario_id: string): Promise<FixtureRunResult> {
  return request<FixtureRunResult>('/api/fixture/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario_id }),
  })
}

export function runAllFixtures(): Promise<FixtureRunAllResult> {
  return request<FixtureRunAllResult>('/api/fixture/run-all', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  })
}

// ================================================================
// 文档比对 (Doc Comparison Review)
// ================================================================

export async function analyzeComparison(
  reqFile: File,
  respFile: File,
): Promise<ComparisonSession> {
  const form = new FormData()
  form.append('req_file', reqFile)
  form.append('resp_file', respFile)
  const res = await fetch('/api/comparison/analyze', { method: 'POST', body: form })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText}: ${body}`)
  }
  return res.json() as Promise<ComparisonSession>
}

export function listComparisonSessions(): Promise<{ sessions: ComparisonSessionSummary[] }> {
  return request<{ sessions: ComparisonSessionSummary[] }>('/api/comparison')
}

export function fetchComparisonSession(sessionId: string): Promise<ComparisonSession> {
  return request<ComparisonSession>(`/api/comparison/${encodeURIComponent(sessionId)}`)
}

export async function deleteComparisonSession(sessionId: string): Promise<void> {
  const res = await fetch(`/api/comparison/${encodeURIComponent(sessionId)}`, { method: 'DELETE' })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText}: ${body}`)
  }
}

/**
 * 流式分批审查：消费 SSE 事件，每批完成后回调 onEvent。
 * 使用 fetch + ReadableStream 而非 EventSource（EventSource 不支持 POST）。
 */
export async function analyzeComparisonStream(
  reqFile: File,
  respFile: File,
  onEvent: (event: ComparisonProgressEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const form = new FormData()
  form.append('req_file', reqFile)
  form.append('resp_file', respFile)
  await streamSse('/api/comparison/analyze-stream', form, onEvent, signal)
}

/**
 * 四步流水线比对审查：消费 SSE 事件，每步完成后回调 onEvent。
 * 步骤：需求扫描 → 向量匹配 → LLM逐项评估 → 全局校验
 */
export async function analyzeComparison4Step(
  reqFile: File,
  respFile: File,
  onEvent: (event: Comparison4StepEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const form = new FormData()
  form.append('req_file', reqFile)
  form.append('resp_file', respFile)
  await streamSse('/api/comparison/analyze-4step', form, onEvent, signal)
}
