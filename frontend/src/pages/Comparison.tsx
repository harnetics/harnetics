/**
 * [INPUT]: 依赖 @/lib/api 的 analyzeComparisonStream/analyzeComparison4Step/listComparisonSessions/deleteComparisonSession，依赖 @/types 的 ComparisonFinding/ComparisonSessionSummary/Comparison4StepEvent/ComparisonFlowMode
 * [OUTPUT]: 对外提供 Comparison 页面组件（上传工作台 + 四步/传统双模式流式进度 + 历史记录列表）
 * [POS]: pages 的文档比对入口，支持四步向量模式与传统流式模式切换，统一展示步骤状态、匹配进度、符合率与历史会话
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  CheckCircle2,
  Circle,
  ExternalLink,
  FileText,
  GitCompare,
  Loader2,
  Trash2,
  Upload,
  X,
  Zap,
} from 'lucide-react'
import {
  analyzeComparison4Step,
  analyzeComparisonStream,
  deleteComparisonSession,
  listComparisonSessions,
} from '@/lib/api'
import type {
  Comparison4StepEvent,
  ComparisonFinding,
  ComparisonFlowMode,
  ComparisonProgressEvent,
  ComparisonReviewCorrection,
  ComparisonSessionSummary,
} from '@/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'
// ================================================================
// 状态样式
// ================================================================

const statusConfig = {
  completed: { label: '已完成', variant: 'success' as const },
  analyzing: { label: '审查中', variant: 'warning' as const },
  pending: { label: '处理中', variant: 'warning' as const },
  failed: { label: '失败', variant: 'destructive' as const },
}

const findingStatusConfig = {
  covered: { label: '已覆盖', variant: 'success' as const },
  partial: { label: '部分', variant: 'warning' as const },
  missing: { label: '未覆盖', variant: 'destructive' as const },
  unclear: { label: '待明确', variant: 'secondary' as const },
}

const flowModeCopy: Record<ComparisonFlowMode, { label: string; hint: string }> = {
  four_step: {
    label: '四步向量流',
    hint: '先拆需求、再做章节匹配与逐项评估，适合长文档精审。',
  },
  classic: {
    label: '传统流式',
    hint: '沿用原有分批审查链路，适合快速回归或兼容旧流程。',
  },
}

// ================================================================
// 四步状态定义
// ================================================================

type StepNumber = 1 | 2 | 3 | 4
type StepState = 'pending' | 'active' | 'done'
type StepStateMap = Record<StepNumber, StepState>

interface FourStepProgressState {
  requirementsTotal: number
  matched: number
  matchingTotal: number
  evaluated: number
  evaluationTotal: number
  complianceRate: number | null
  summary: string
  corrections: ComparisonReviewCorrection[]
  activeLabel: string
}

const STEP_DEFS = [
  { step: 1 as const, label: '识别需求条款' },
  { step: 2 as const, label: '向量匹配章节' },
  { step: 3 as const, label: 'LLM 逐项评估' },
  { step: 4 as const, label: '全局校验' },
]

function createInitialStepStates(): StepStateMap {
  return {
    1: 'pending',
    2: 'pending',
    3: 'pending',
    4: 'pending',
  }
}

function createInitialFourStepProgress(): FourStepProgressState {
  return {
    requirementsTotal: 0,
    matched: 0,
    matchingTotal: 0,
    evaluated: 0,
    evaluationTotal: 0,
    complianceRate: null,
    summary: '',
    corrections: [],
    activeLabel: '',
  }
}

function activateStep(step: StepNumber): StepStateMap {
  return {
    1: step > 1 ? 'done' : step === 1 ? 'active' : 'pending',
    2: step > 2 ? 'done' : step === 2 ? 'active' : 'pending',
    3: step > 3 ? 'done' : step === 3 ? 'active' : 'pending',
    4: step > 4 ? 'done' : step === 4 ? 'active' : 'pending',
  }
}

function finishStep(states: StepStateMap, step: StepNumber): StepStateMap {
  return { ...states, [step]: 'done' }
}

function finishAllSteps(): StepStateMap {
  return {
    1: 'done',
    2: 'done',
    3: 'done',
    4: 'done',
  }
}

function toPercent(value: number | null): string {
  if (value === null || Number.isNaN(value)) return '--'
  const normalized = value <= 1 ? value * 100 : value
  const rounded = normalized >= 10 ? normalized.toFixed(0) : normalized.toFixed(1)
  return `${rounded}%`
}

function getRatioPercent(done: number, total: number): number {
  if (total <= 0) return 0
  return Math.max(0, Math.min(100, (done / total) * 100))
}

// ================================================================
// StepIndicator — 四步骤进度条
// ================================================================

interface StepIndicatorProps {
  states: StepStateMap
}

function StepIndicator({ states }: StepIndicatorProps) {
  return (
    <div className="flex items-center gap-0 overflow-x-auto pb-1">
      {STEP_DEFS.map(({ step, label }, idx) => {
        const state = states[step]
        return (
          <div key={step} className="flex items-center">
            <div className="flex min-w-16 flex-col items-center gap-1">
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full border-2 transition-all duration-300 ${
                  state === 'done'
                    ? 'border-primary bg-primary text-primary-foreground'
                    : state === 'active'
                      ? 'border-primary text-primary animate-pulse'
                      : 'border-muted-foreground/30 text-muted-foreground/40'
                }`}
              >
                {state === 'done' ? (
                  <CheckCircle2 className="h-4 w-4" />
                ) : state === 'active' ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Circle className="h-4 w-4" />
                )}
              </div>
              <span
                className={`w-16 text-center text-[10px] leading-tight ${
                  state === 'pending' ? 'text-muted-foreground/40' : 'text-foreground'
                }`}
              >
                {label}
              </span>
            </div>
            {idx < STEP_DEFS.length - 1 && (
              <div
                className={`mx-1 mb-4 h-0.5 w-8 transition-colors duration-300 ${
                  states[(step + 1) as StepNumber] !== 'pending' || state === 'done'
                    ? 'bg-primary/50'
                    : 'bg-muted-foreground/20'
                }`}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}

// ================================================================
// FileZone — 单文件拖放上传区
// ================================================================

interface FileZoneProps {
  label: string
  hint: string
  file: File | null
  onFile: (file: File) => void
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
      className={`cursor-pointer rounded-xl border-2 border-dashed p-8 transition-colors ${
        disabled
          ? 'cursor-not-allowed border-muted opacity-50'
          : 'border-muted-foreground/30 hover:border-primary hover:bg-muted/30'
      } ${file ? 'border-primary/50 bg-muted/20' : ''}`}
      onClick={() => !disabled && inputRef.current?.click()}
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
    >
      <div className="flex flex-col items-center justify-center gap-3">
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.md,.txt,.docx"
          className="hidden"
          disabled={disabled}
          onChange={(e) => {
            const pickedFile = e.target.files?.[0]
            if (pickedFile) onFile(pickedFile)
          }}
        />
        {file ? (
          <>
            <FileText className="h-8 w-8 text-primary" />
            <div className="text-center">
              <p className="max-w-[200px] truncate text-sm font-medium">{file.name}</p>
              <p className="mt-0.5 text-xs text-muted-foreground">{(file.size / 1024).toFixed(0)} KB</p>
            </div>
            <p className="text-xs text-primary">点击重新选择</p>
          </>
        ) : (
          <>
            <Upload className="h-8 w-8 text-muted-foreground" />
            <div className="text-center">
              <p className="text-sm font-medium">{label}</p>
              <p className="mt-0.5 text-xs text-muted-foreground">{hint}</p>
            </div>
            <p className="text-xs text-muted-foreground">支持 PDF / DOCX / Markdown</p>
          </>
        )}
      </div>
    </div>
  )
}

// ================================================================
// FindingPreviewList — 最近审查意见
// ================================================================

interface FindingPreviewListProps {
  findings: ComparisonFinding[]
  limit?: number
}

function FindingPreviewList({ findings, limit = 8 }: FindingPreviewListProps) {
  if (findings.length === 0) return null

  return (
    <div className="space-y-1.5">
      {findings.slice(-limit).map((finding, idx) => {
        const sc = findingStatusConfig[finding.status] ?? {
          label: finding.status,
          variant: 'secondary' as const,
        }
        return (
          <div
            key={finding.finding_id || `${finding.requirement_ref}-${idx}`}
            className="flex items-start gap-2 rounded-md border bg-muted/30 px-3 py-2 text-xs"
          >
            <Badge variant={sc.variant} className="mt-0.5 shrink-0 px-1.5 text-[10px]">
              {sc.label}
            </Badge>
            <div className="min-w-0">
              <p className="truncate font-medium">{finding.requirement_heading || finding.chapter}</p>
              <p className="mt-0.5 line-clamp-1 text-muted-foreground">{finding.detail}</p>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ================================================================
// 主页面
// ================================================================

export default function Comparison() {
  const navigate = useNavigate()
  const abortRef = useRef<AbortController | null>(null)

  const [reqFile, setReqFile] = useState<File | null>(null)
  const [respFile, setRespFile] = useState<File | null>(null)
  const [flowMode, setFlowMode] = useState<ComparisonFlowMode>('four_step')
  const [analyzing, setAnalyzing] = useState(false)
  const [analyzeError, setAnalyzeError] = useState('')
  const [sessions, setSessions] = useState<ComparisonSessionSummary[]>([])
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null)

  const [streamProgress, setStreamProgress] = useState<{ batch: number; total: number } | null>(null)
  const [streamFindings, setStreamFindings] = useState<ComparisonFinding[]>([])
  const [stepStates, setStepStates] = useState<StepStateMap>(() => createInitialStepStates())
  const [fourStepProgress, setFourStepProgress] = useState<FourStepProgressState>(() => createInitialFourStepProgress())

  const loadSessions = () => {
    listComparisonSessions()
      .then((res) => setSessions(res.sessions))
      .catch(() => {})
  }

  useEffect(() => {
    loadSessions()
  }, [])

  useEffect(() => {
    return () => abortRef.current?.abort()
  }, [])

  const resetProgressState = () => {
    setAnalyzeError('')
    setStreamProgress(null)
    setStreamFindings([])
    setStepStates(createInitialStepStates())
    setFourStepProgress(createInitialFourStepProgress())
  }

  const handleModeChange = (nextMode: ComparisonFlowMode) => {
    if (analyzing || flowMode === nextMode) return
    setFlowMode(nextMode)
    resetProgressState()
  }

  const handleClassicEvent = (event: ComparisonProgressEvent) => {
    if (event.type === 'started') {
      setStreamProgress({ batch: 0, total: event.total_batches ?? 1 })
      return
    }

    if (event.type === 'batch_progress') {
      setStreamProgress({ batch: event.batch ?? 0, total: event.total_batches ?? 1 })
      setStreamFindings((prev) => [...prev, ...(event.batch_findings ?? [])])
      return
    }

    if (event.type === 'completed') {
      navigate(`/comparison/${event.session_id}`)
      return
    }

    if (event.type === 'error') {
      setAnalyzeError(event.message ?? '部分批次审查失败')
    }
  }

  const handleFourStepEvent = (event: Comparison4StepEvent) => {
    if (event.type === 'step_started') {
      setStepStates(activateStep(event.step))
      setFourStepProgress((prev) => ({ ...prev, activeLabel: event.label }))
      return
    }

    if (event.type === 'scanning_done') {
      setStepStates((prev) => finishStep(prev, 1))
      setFourStepProgress((prev) => ({
        ...prev,
        requirementsTotal: event.total_requirements,
        matchingTotal: event.total_requirements,
        evaluationTotal: event.total_requirements,
        activeLabel: `已识别 ${event.total_requirements} 条需求`,
      }))
      return
    }

    if (event.type === 'matching_progress') {
      setFourStepProgress((prev) => ({
        ...prev,
        matched: event.matched,
        matchingTotal: event.total,
        activeLabel: `已完成 ${event.matched}/${event.total} 条需求的章节匹配`,
      }))
      if (event.matched >= event.total) {
        setStepStates((prev) => finishStep(prev, 2))
      }
      return
    }

    if (event.type === 'finding_batch') {
      setStreamFindings((prev) => [...prev, ...event.findings])
      setFourStepProgress((prev) => ({
        ...prev,
        evaluated: event.evaluated,
        evaluationTotal: event.total,
        activeLabel: `已评估 ${event.evaluated}/${event.total} 条需求`,
      }))
      if (event.evaluated >= event.total) {
        setStepStates((prev) => finishStep(prev, 3))
      }
      return
    }

    if (event.type === 'review_done') {
      setStepStates((prev) => finishStep(prev, 4))
      setFourStepProgress((prev) => ({
        ...prev,
        complianceRate: event.compliance_rate,
        summary: event.summary,
        corrections: event.corrections,
        activeLabel: '全局校验完成',
      }))
      return
    }

    if (event.type === 'completed') {
      setStreamFindings(event.findings)
      setStepStates(finishAllSteps())
      setFourStepProgress((prev) => ({
        ...prev,
        evaluated: event.total_findings,
        complianceRate: event.compliance_rate,
        activeLabel: '审查完成，正在打开结果页',
      }))
      navigate(`/comparison/${event.session_id}`)
      return
    }

    setAnalyzeError(event.message || '四步审查失败')
  }

  const handleAnalyze = async () => {
    if (!reqFile || !respFile) return

    setAnalyzing(true)
    resetProgressState()

    const controller = new AbortController()
    abortRef.current = controller

    try {
      if (flowMode === 'four_step') {
        await analyzeComparison4Step(reqFile, respFile, handleFourStepEvent, controller.signal)
      } else {
        await analyzeComparisonStream(reqFile, respFile, handleClassicEvent, controller.signal)
      }
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
    setPendingDeleteId(id)
  }

  const confirmDelete = async () => {
    if (!pendingDeleteId) return
    const id = pendingDeleteId
    setDeletingId(id)
    try {
      await deleteComparisonSession(id)
      setSessions((prev) => prev.filter((session) => session.session_id !== id))
    } catch {
      // ignore
    } finally {
      setDeletingId(null)
      setPendingDeleteId(null)
    }
  }

  const hasFourStepProgress =
    fourStepProgress.requirementsTotal > 0 ||
    fourStepProgress.matched > 0 ||
    fourStepProgress.evaluated > 0 ||
    fourStepProgress.complianceRate !== null

  const matchingPercent = getRatioPercent(fourStepProgress.matched, fourStepProgress.matchingTotal)
  const evaluationPercent = getRatioPercent(fourStepProgress.evaluated, fourStepProgress.evaluationTotal)
  const classicPercent = streamProgress ? getRatioPercent(streamProgress.batch, streamProgress.total) : 0

  return (
    <div className="container mx-auto max-w-screen-lg space-y-8 px-4 py-8">
      <div className="flex items-center gap-3">
        <GitCompare className="h-6 w-6 text-primary" />
        <div>
          <h1 className="text-2xl font-bold tracking-tight">文档比对审查</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">上传审查大纲与安全分析报告，按所选流程执行符合性审查</p>
        </div>
      </div>

      <Card>
        <CardContent className="space-y-5 pt-6">
          <div className="flex flex-col gap-4 rounded-xl border bg-muted/20 p-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Zap className="h-4 w-4 text-primary" />
                <span className="text-sm font-medium">审查流程</span>
                <Badge variant="secondary">可切换</Badge>
              </div>
              <p className="text-xs text-muted-foreground">{flowModeCopy[flowMode].hint}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              {(['four_step', 'classic'] as ComparisonFlowMode[]).map((mode) => (
                <Button
                  key={mode}
                  type="button"
                  variant={flowMode === mode ? 'default' : 'outline'}
                  size="sm"
                  disabled={analyzing}
                  className="min-w-[120px]"
                  onClick={() => handleModeChange(mode)}
                >
                  {flowModeCopy[mode].label}
                </Button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
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

          {analyzeError && <p className="text-sm text-destructive">{analyzeError}</p>}

          <div className="flex justify-end gap-2">
            {analyzing && (
              <Button variant="outline" size="lg" className="gap-2" onClick={handleCancel}>
                <X className="h-4 w-4" />
                取消
              </Button>
            )}
            <Button
              size="lg"
              className="min-w-[140px] gap-2"
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

          {flowMode === 'four_step' && (analyzing || hasFourStepProgress) && (
            <div className="space-y-4 rounded-xl border bg-muted/20 p-4">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="gap-1">
                      <Zap className="h-3 w-3" />
                      四步向量流
                    </Badge>
                    {fourStepProgress.complianceRate !== null && (
                      <Badge variant="success">符合率 {toPercent(fourStepProgress.complianceRate)}</Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {fourStepProgress.activeLabel || '正在建立需求条款、章节匹配与全局校验链路'}
                  </p>
                </div>
                <p className="text-xs text-muted-foreground">
                  匹配 {fourStepProgress.matched}/{fourStepProgress.matchingTotal || fourStepProgress.requirementsTotal || '--'}
                  {' · '}
                  评估 {fourStepProgress.evaluated}/{fourStepProgress.evaluationTotal || fourStepProgress.requirementsTotal || '--'}
                </p>
              </div>

              <StepIndicator states={stepStates} />

              <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                <div className="rounded-lg border bg-background px-3 py-3">
                  <p className="text-xs text-muted-foreground">需求条款</p>
                  <p className="mt-1 text-2xl font-semibold">{fourStepProgress.requirementsTotal || '--'}</p>
                  <p className="mt-1 text-xs text-muted-foreground">步骤 1 扫描结果</p>
                </div>
                <div className="rounded-lg border bg-background px-3 py-3">
                  <p className="text-xs text-muted-foreground">章节匹配</p>
                  <p className="mt-1 text-2xl font-semibold">
                    {fourStepProgress.matched}/{fourStepProgress.matchingTotal || '--'}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">步骤 2 已匹配需求数</p>
                </div>
                <div className="rounded-lg border bg-background px-3 py-3">
                  <p className="text-xs text-muted-foreground">整体符合率</p>
                  <p className="mt-1 text-2xl font-semibold">{toPercent(fourStepProgress.complianceRate)}</p>
                  <p className="mt-1 text-xs text-muted-foreground">步骤 4 全局校验输出</p>
                </div>
              </div>

              <div className="space-y-3">
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>章节匹配进度</span>
                    <span>{matchingPercent.toFixed(0)}%</span>
                  </div>
                  <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary transition-all duration-500"
                      style={{ width: `${matchingPercent}%` }}
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>逐项评估进度</span>
                    <span>{evaluationPercent.toFixed(0)}%</span>
                  </div>
                  <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary transition-all duration-500"
                      style={{ width: `${evaluationPercent}%` }}
                    />
                  </div>
                </div>
              </div>

              {fourStepProgress.summary && (
                <div className="space-y-2 rounded-lg border bg-background px-3 py-3">
                  <p className="text-sm font-medium">全局校验摘要</p>
                  <p className="text-sm leading-6 text-muted-foreground">{fourStepProgress.summary}</p>
                  {fourStepProgress.corrections.length > 0 && (
                    <div className="space-y-1.5 pt-1">
                      {fourStepProgress.corrections.map((item, idx) => (
                        <div key={`${item.type}-${idx}`} className="rounded-md border bg-muted/30 px-3 py-2 text-xs">
                          <span className="font-medium">{item.type}</span>
                          <span className="mx-1 text-muted-foreground">/</span>
                          <span className="text-muted-foreground">{item.description}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium">最新审查意见</p>
                  <p className="text-xs text-muted-foreground">累计 {streamFindings.length} 条</p>
                </div>
                <FindingPreviewList findings={streamFindings} limit={6} />
              </div>
            </div>
          )}

          {flowMode === 'classic' && analyzing && streamProgress && (
            <div className="space-y-3 pt-2">
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>
                    正在审查第 {streamProgress.batch}/{streamProgress.total} 批
                    {streamFindings.length > 0 && `，已发现 ${streamFindings.length} 条意见`}
                  </span>
                  <span>{classicPercent.toFixed(0)}%</span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-primary transition-all duration-500"
                    style={{ width: `${classicPercent}%` }}
                  />
                </div>
              </div>

              <FindingPreviewList findings={streamFindings} />
            </div>
          )}

          {analyzing && flowMode === 'classic' && !streamProgress && (
            <p className="text-center text-xs text-muted-foreground">
              正在解析文件并调用 AI 逐条审查，可能需要 30–300 秒，请勿关闭页面
            </p>
          )}
        </CardContent>
      </Card>

      {sessions.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-base font-semibold text-muted-foreground">历史比对记录</h2>
          <div className="space-y-2">
            {sessions.map((session) => {
              const sc = statusConfig[session.status] ?? {
                label: session.status,
                variant: 'secondary' as const,
              }
              return (
                <div
                  key={session.session_id}
                  className="flex cursor-pointer items-center gap-3 rounded-lg border bg-card px-4 py-3 transition-colors hover:bg-muted/40"
                  onClick={() => navigate(`/comparison/${session.session_id}`)}
                >
                  <GitCompare className="h-4 w-4 shrink-0 text-muted-foreground" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">
                      <span className="text-primary">{session.req_filename}</span>
                      <span className="mx-1.5 text-muted-foreground">vs</span>
                      <span>{session.resp_filename}</span>
                    </p>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {session.created_at.slice(0, 19).replace('T', ' ')}
                    </p>
                  </div>
                  {session.status === 'completed' && session.findings_count > 0 && (
                    <div className="flex shrink-0 items-center gap-1.5">
                      {session.covered > 0 && <Badge variant="success">{session.covered} ✅</Badge>}
                      {session.partial > 0 && <Badge variant="warning">{session.partial} ⚠️</Badge>}
                      {session.missing > 0 && <Badge variant="destructive">{session.missing} ❌</Badge>}
                    </div>
                  )}
                  <Badge variant={sc.variant}>{sc.label}</Badge>
                  <div className="flex shrink-0 items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-muted-foreground hover:text-foreground"
                      onClick={(e) => {
                        e.stopPropagation()
                        navigate(`/comparison/${session.session_id}`)
                      }}
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-muted-foreground hover:text-destructive"
                      disabled={deletingId === session.session_id}
                      onClick={(e) => handleDelete(e, session.session_id)}
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
        <p className="py-4 text-center text-sm text-muted-foreground">暂无历史比对记录</p>
      )}

      <ConfirmDialog
        open={pendingDeleteId !== null}
        title="删除比对记录"
        description="确认删除此比对记录？此操作不可撤销。"
        confirmLabel="删除"
        busy={deletingId !== null}
        onConfirm={confirmDelete}
        onCancel={() => {
          if (deletingId === null) setPendingDeleteId(null)
        }}
      />
    </div>
  )
}

export { findingStatusConfig }
