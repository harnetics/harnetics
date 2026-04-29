/**
 * [INPUT]: 依赖 @/lib/api 的 analyzeComparisonStream/listComparisonSessions/deleteComparisonSession，依赖 @/types 的 ComparisonFinding/ComparisonSessionSummary
 * [OUTPUT]: 对外提供 Comparison 页面组件（上传工作台 + 流式进度 + 历史记录列表）
 * [POS]: pages 的文档比对入口，上传要求文件和应答文件，触发 LLM 分批流式符合性审查，实时展示进度
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */

import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, FileText, Trash2, ExternalLink, GitCompare, Loader2, X } from 'lucide-react'
import { analyzeComparisonStream, listComparisonSessions, deleteComparisonSession } from '@/lib/api'
import type { ComparisonFinding, ComparisonSessionSummary } from '@/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'

// ================================================================
// 状态样式
// ================================================================

const statusConfig = {
  completed: { label: '已完成', variant: 'success' as const },
  analyzing: { label: '审查中', variant: 'warning' as const },
  pending:   { label: '处理中', variant: 'warning' as const },
  failed:    { label: '失败',   variant: 'destructive' as const },
}

const findingStatusConfig = {
  covered: { label: '已覆盖', variant: 'success' as const },
  partial: { label: '部分',   variant: 'warning' as const },
  missing: { label: '未覆盖', variant: 'destructive' as const },
  unclear: { label: '待明确', variant: 'secondary' as const },
}

// ================================================================
// FileZone — 单文件拖放上传区
// ================================================================

interface FileZoneProps {
  label: string
  hint: string
  file: File | null
  onFile: (f: File) => void
  disabled?: boolean
}

function FileZone({ label, hint, file, onFile, disabled }: FileZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    if (disabled) return
    const dropped = e.dataTransfer.files[0]
    if (dropped) onFile(dropped)
  }

  return (
    <div
      className={`flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-8 transition-colors cursor-pointer
        ${disabled ? 'opacity-50 cursor-not-allowed border-muted' : 'hover:border-primary hover:bg-muted/30 border-muted-foreground/30'}
        ${file ? 'bg-muted/20 border-primary/50' : ''}`}
      onClick={() => !disabled && inputRef.current?.click()}
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.md,.txt,.docx"
        className="hidden"
        disabled={disabled}
        onChange={(e) => { const f = e.target.files?.[0]; if (f) onFile(f) }}
      />
      {file ? (
        <>
          <FileText className="h-8 w-8 text-primary" />
          <div className="text-center">
            <p className="font-medium text-sm truncate max-w-[200px]">{file.name}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{(file.size / 1024).toFixed(0)} KB</p>
          </div>
          <p className="text-xs text-primary">点击重新选择</p>
        </>
      ) : (
        <>
          <Upload className="h-8 w-8 text-muted-foreground" />
          <div className="text-center">
            <p className="font-medium text-sm">{label}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{hint}</p>
          </div>
          <p className="text-xs text-muted-foreground">支持 PDF / DOCX / Markdown</p>
        </>
      )}
    </div>
  )
}

// ================================================================
// 主页面
// ================================================================

export default function Comparison() {
  const navigate = useNavigate()
  const [reqFile, setReqFile] = useState<File | null>(null)
  const [respFile, setRespFile] = useState<File | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [analyzeError, setAnalyzeError] = useState('')
  const [sessions, setSessions] = useState<ComparisonSessionSummary[]>([])
  const [deletingId, setDeletingId] = useState<string | null>(null)

  // 流式状态
  const [streamProgress, setStreamProgress] = useState<{ batch: number; total: number } | null>(null)
  const [streamFindings, setStreamFindings] = useState<ComparisonFinding[]>([])
  const abortRef = useRef<AbortController | null>(null)

  const loadSessions = () => {
    listComparisonSessions()
      .then((res) => setSessions(res.sessions))
      .catch(() => {})
  }

  useEffect(() => { loadSessions() }, [])

  const handleAnalyze = async () => {
    if (!reqFile || !respFile) return
    setAnalyzing(true)
    setAnalyzeError('')
    setStreamProgress(null)
    setStreamFindings([])

    const controller = new AbortController()
    abortRef.current = controller

    try {
      await analyzeComparisonStream(
        reqFile,
        respFile,
        (event) => {
          if (event.type === 'started') {
            setStreamProgress({ batch: 0, total: event.total_batches ?? 1 })
          } else if (event.type === 'batch_progress') {
            setStreamProgress({ batch: event.batch ?? 0, total: event.total_batches ?? 1 })
            setStreamFindings((prev) => [...prev, ...(event.batch_findings ?? [])])
          } else if (event.type === 'completed') {
            navigate(`/comparison/${event.session_id}`)
          } else if (event.type === 'error') {
            setAnalyzeError(event.message ?? '部分批次审查失败')
          }
        },
        controller.signal,
      )
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        setAnalyzeError(err instanceof Error ? err.message : '分析失败')
      }
    } finally {
      setAnalyzing(false)
      abortRef.current = null
    }
  }

  const handleCancel = () => {
    abortRef.current?.abort()
  }

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    if (!window.confirm('确认删除此比对记录？')) return
    setDeletingId(id)
    try {
      await deleteComparisonSession(id)
      setSessions((prev) => prev.filter((s) => s.session_id !== id))
    } catch {
      // ignore
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="container mx-auto max-w-screen-lg px-4 py-8 space-y-8">

      {/* ---- 页头 ---- */}
      <div className="flex items-center gap-3">
        <GitCompare className="h-6 w-6 text-primary" />
        <div>
          <h1 className="text-2xl font-bold tracking-tight">文档比对审查</h1>
          <p className="mt-0.5 text-muted-foreground text-sm">上传审查大纲与安全分析报告，AI 逐条执行符合性审查</p>
        </div>
      </div>

      {/* ---- 上传区 ---- */}
      <Card>
        <CardContent className="pt-6 space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FileZone
              label="要求文件（审查大纲）"
              hint="拖放文件到此处，或点击选择"
              file={reqFile}
              onFile={setReqFile}
              disabled={analyzing}
            />
            <FileZone
              label="应答文件（安全分析报告）"
              hint="拖放文件到此处，或点击选择"
              file={respFile}
              onFile={setRespFile}
              disabled={analyzing}
            />
          </div>

          {analyzeError && (
            <p className="text-sm text-destructive">{analyzeError}</p>
          )}

          <div className="flex justify-end gap-2">
            {analyzing && (
              <Button variant="outline" size="lg" className="gap-2" onClick={handleCancel}>
                <X className="h-4 w-4" />
                取消
              </Button>
            )}
            <Button
              size="lg"
              className="gap-2 min-w-[140px]"
              disabled={!reqFile || !respFile || analyzing}
              onClick={handleAnalyze}
            >
              {analyzing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  审查中…
                </>
              ) : (
                <>
                  <GitCompare className="h-4 w-4" />
                  开始审查
                </>
              )}
            </Button>
          </div>

          {/* 流式进度区域 */}
          {analyzing && streamProgress && (
            <div className="space-y-3 pt-2">
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>
                    正在审查第 {streamProgress.batch}/{streamProgress.total} 批
                    {streamFindings.length > 0 && `，已发现 ${streamFindings.length} 条意见`}
                  </span>
                  <span>{Math.round((streamProgress.batch / streamProgress.total) * 100)}%</span>
                </div>
                <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full rounded-full bg-primary transition-all duration-500"
                    style={{ width: `${(streamProgress.batch / streamProgress.total) * 100}%` }}
                  />
                </div>
              </div>

              {streamFindings.length > 0 && (
                <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
                  {streamFindings.slice(-8).map((f) => {
                    const sc = findingStatusConfig[f.status] ?? { label: f.status, variant: 'secondary' as const }
                    return (
                      <div key={f.finding_id} className="flex items-start gap-2 rounded-md border px-3 py-2 text-xs bg-muted/30">
                        <Badge variant={sc.variant} className="shrink-0 mt-0.5 text-[10px] px-1.5">{sc.label}</Badge>
                        <div className="min-w-0">
                          <p className="font-medium truncate">{f.requirement_heading || f.chapter}</p>
                          <p className="text-muted-foreground line-clamp-1 mt-0.5">{f.detail}</p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )}

          {analyzing && !streamProgress && (
            <p className="text-xs text-center text-muted-foreground">
              正在解析文件并调用 AI 逐条审查，可能需要 30–300 秒，请勿关闭页面
            </p>
          )}
        </CardContent>
      </Card>

      {/* ---- 历史记录 ---- */}
      {sessions.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-base font-semibold text-muted-foreground">历史比对记录</h2>
          <div className="space-y-2">
            {sessions.map((s) => {
              const sc = statusConfig[s.status] ?? { label: s.status, variant: 'secondary' as const }
              return (
                <div
                  key={s.session_id}
                  className="flex items-center gap-3 rounded-lg border bg-card px-4 py-3 cursor-pointer hover:bg-muted/40 transition-colors"
                  onClick={() => navigate(`/comparison/${s.session_id}`)}
                >
                  <GitCompare className="h-4 w-4 text-muted-foreground shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      <span className="text-primary">{s.req_filename}</span>
                      <span className="text-muted-foreground mx-1.5">vs</span>
                      <span>{s.resp_filename}</span>
                    </p>
                    <p className="text-xs text-muted-foreground mt-0.5">{s.created_at.slice(0, 19).replace('T', ' ')}</p>
                  </div>
                  {s.status === 'completed' && s.findings_count > 0 && (
                    <div className="flex items-center gap-1.5 shrink-0">
                      {s.covered > 0 && <Badge variant="success">{s.covered} ✅</Badge>}
                      {s.partial > 0 && <Badge variant="warning">{s.partial} ⚠️</Badge>}
                      {s.missing > 0 && <Badge variant="destructive">{s.missing} ❌</Badge>}
                    </div>
                  )}
                  <Badge variant={sc.variant}>{sc.label}</Badge>
                  <div className="flex items-center gap-1 shrink-0">
                    <Button
                      variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-foreground"
                      onClick={(e) => { e.stopPropagation(); navigate(`/comparison/${s.session_id}`) }}
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-destructive"
                      disabled={deletingId === s.session_id}
                      onClick={(e) => handleDelete(e, s.session_id)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {sessions.length === 0 && !analyzing && (
        <p className="text-center text-sm text-muted-foreground py-4">暂无历史比对记录</p>
      )}
    </div>
  )
}

export { findingStatusConfig }
