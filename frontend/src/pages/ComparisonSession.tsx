/**
 * [INPUT]: 依赖 @/lib/api 的 fetchComparisonSession，依赖 @/lib/utils 的 formatBeijingTime，依赖 @/types 的 ComparisonSession/ComparisonFinding/ComparisonSectionItem
 * [OUTPUT]: 对外提供 ComparisonSession 页面组件（审查结果详情 + 溯源 + 文件预览）
 * [POS]: pages 的文档比对结果页，展示 findings 列表、两份文件章节预览，支持点击引用溯源跳转
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  CheckCircle2, AlertTriangle, XCircle, HelpCircle,
  Download, ChevronDown, ChevronUp, ArrowLeft, GitCompare,
} from 'lucide-react'
import { fetchComparisonSession } from '@/lib/api'
import { formatBeijingTime } from '@/lib/utils'
import type { ComparisonSession, ComparisonFinding, ComparisonSectionItem } from '@/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import MarkdownRenderer from '@/components/MarkdownRenderer'

// ================================================================
// 状态映射
// ================================================================

const statusConfig: Record<string, {
  label: string
  variant: 'success' | 'warning' | 'destructive' | 'secondary'
  icon: React.ReactNode
}> = {
  covered: { label: '已覆盖', variant: 'success',     icon: <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" /> },
  partial: { label: '部分覆盖', variant: 'warning',   icon: <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" /> },
  missing: { label: '未覆盖', variant: 'destructive', icon: <XCircle className="h-4 w-4 text-destructive shrink-0" /> },
  unclear: { label: '待明确', variant: 'secondary',   icon: <HelpCircle className="h-4 w-4 text-muted-foreground shrink-0" /> },
}

// ================================================================
// 溯源辅助：将文本引用（如 "Page 3"）转换为 section anchor id
// ================================================================

function refToAnchorId(ref: string): string {
  return ref.trim().replace(/\s+/g, '-').toLowerCase()
}

function sectionToAnchorId(heading: string): string {
  return heading.trim().replace(/\s+/g, '-').toLowerCase()
}

// ================================================================
// FindingCard — 单条审查意见
// ================================================================

interface FindingCardProps {
  finding: ComparisonFinding
  onTraceReq: (ref: string) => void
  onTraceResp: (ref: string) => void
}

function FindingCard({ finding, onTraceReq, onTraceResp }: FindingCardProps) {
  const [expanded, setExpanded] = useState(false)
  const sc = statusConfig[finding.status] ?? statusConfig.unclear

  return (
    <Card className="overflow-hidden">
      <CardHeader
        className="py-3 px-4 cursor-pointer hover:bg-muted/30 transition-colors"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="flex items-start gap-2">
          {sc.icon}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-mono text-muted-foreground">{finding.finding_id}</span>
              <span className="text-sm font-semibold">{finding.chapter}</span>
              <Badge variant={sc.variant} className="text-xs">{sc.label}</Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5 truncate">{finding.requirement_heading}</p>
          </div>
          <div className="shrink-0 text-muted-foreground">
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </div>
        </div>
      </CardHeader>

      {expanded && (
        <CardContent className="pt-0 pb-4 px-4 space-y-3">
          {finding.requirement_content && (
            <div className="rounded-md bg-muted/40 px-3 py-2 text-xs text-muted-foreground border-l-2 border-primary/30">
              <span className="font-medium text-foreground">要求原文：</span>
              {finding.requirement_content.slice(0, 200)}
              {finding.requirement_content.length > 200 && '…'}
            </div>
          )}

          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">审查意见</p>
            <p className="text-sm leading-relaxed">{finding.detail}</p>
          </div>

          <div className="flex flex-wrap gap-2 pt-1">
            {finding.requirement_ref && (
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs gap-1.5"
                onClick={() => onTraceReq(finding.requirement_ref)}
              >
                📄 要求文件 · {finding.requirement_ref}
              </Button>
            )}
            {finding.response_ref && finding.response_ref !== '未找到对应内容' && (
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs gap-1.5"
                onClick={() => onTraceResp(finding.response_ref)}
              >
                📋 应答文件 · {finding.response_ref}
              </Button>
            )}
            {finding.response_ref === '未找到对应内容' && (
              <span className="inline-flex items-center text-xs text-destructive gap-1">
                <XCircle className="h-3.5 w-3.5" /> 应答文件未找到对应内容
              </span>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  )
}

// ================================================================
// SectionPanel — 文件章节预览
// ================================================================

interface SectionPanelProps {
  sections: ComparisonSectionItem[]
  highlightRef?: string
}

function SectionPanel({ sections, highlightRef }: SectionPanelProps) {
  const targetId = highlightRef ? refToAnchorId(highlightRef) : null

  useEffect(() => {
    if (!targetId) return
    // 尝试通过 anchor id 精确匹配，fallback 到模糊包含匹配
    const el = document.getElementById(targetId)
      ?? Array.from(document.querySelectorAll('[data-section-anchor]')).find((el) => {
        const h = el.getAttribute('data-section-anchor') ?? ''
        return h.toLowerCase().includes(highlightRef?.toLowerCase() ?? '')
      })
    el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [targetId, highlightRef])

  if (sections.length === 0) {
    return <p className="text-sm text-muted-foreground text-center py-12">暂无解析章节</p>
  }

  return (
    <div className="space-y-3 py-2">
      {sections.map((sec) => {
        const anchorId = sectionToAnchorId(sec.heading)
        const isHighlighted = targetId && anchorId.includes(targetId)
        return (
          <div
            key={sec.section_id}
            id={anchorId}
            data-section-anchor={sec.heading}
            className={`rounded-lg border px-4 py-3 transition-colors ${isHighlighted ? 'border-primary bg-primary/5' : 'bg-card'}`}
          >
            <h3 className={`text-sm font-semibold mb-1.5 ${isHighlighted ? 'text-primary' : ''}`}>
              {sec.heading}
            </h3>
            <p className="text-xs text-muted-foreground leading-relaxed whitespace-pre-wrap line-clamp-6">
              {sec.content}
            </p>
          </div>
        )
      })}
    </div>
  )
}

// ================================================================
// 概览统计
// ================================================================

function StatsRow({ findings }: { findings: ComparisonFinding[] }) {
  const total = findings.length
  if (total === 0) return null

  const counts = {
    covered: findings.filter((f) => f.status === 'covered').length,
    partial: findings.filter((f) => f.status === 'partial').length,
    missing: findings.filter((f) => f.status === 'missing').length,
    unclear: findings.filter((f) => f.status === 'unclear').length,
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      {(Object.entries(counts) as [string, number][]).map(([k, v]) => {
        const sc = statusConfig[k]
        return (
          <Card key={k}>
            <CardContent className="p-4 flex items-center gap-3">
              {sc.icon}
              <div>
                <p className="text-2xl font-bold">{v}</p>
                <p className="text-xs text-muted-foreground">{sc.label}</p>
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}

// ================================================================
// 主页面
// ================================================================

export default function ComparisonSessionPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [session, setSession] = useState<ComparisonSession | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('findings')
  const [reqHighlight, setReqHighlight] = useState<string | undefined>()
  const [respHighlight, setRespHighlight] = useState<string | undefined>()

  useEffect(() => {
    if (!id) return
    setLoading(true)
    fetchComparisonSession(id)
      .then(setSession)
      .catch(() => setSession(null))
      .finally(() => setLoading(false))
  }, [id])

  const handleTraceReq = useCallback((ref: string) => {
    setReqHighlight(ref)
    setActiveTab('req')
  }, [])

  const handleTraceResp = useCallback((ref: string) => {
    setRespHighlight(ref)
    setActiveTab('resp')
  }, [])

  // 切换 tab 时重置高亮（避免旧高亮残留）
  const handleTabChange = (val: string) => {
    setActiveTab(val)
    if (val !== 'req') setReqHighlight(undefined)
    if (val !== 'resp') setRespHighlight(undefined)
  }

  const handleExport = () => {
    if (!session) return
    const blob = new Blob([session.analysis_md], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${session.session_id}-审查报告.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="container mx-auto max-w-screen-lg px-4 py-16 text-center text-muted-foreground">
        加载中…
      </div>
    )
  }

  if (!session) {
    return (
      <div className="container mx-auto max-w-screen-lg px-4 py-16 text-center space-y-4">
        <p className="text-muted-foreground">比对会话不存在或已删除。</p>
        <Button variant="outline" onClick={() => navigate('/comparison')}>返回比对工作台</Button>
      </div>
    )
  }

  const sessionStatusConfig: Record<string, { label: string; variant: 'success' | 'warning' | 'destructive' | 'secondary' }> = {
    completed: { label: '审查完成', variant: 'success' },
    pending:   { label: '处理中',   variant: 'warning' },
    failed:    { label: '分析失败', variant: 'destructive' },
  }
  const ssc = sessionStatusConfig[session.status] ?? { label: session.status, variant: 'secondary' as const }

  return (
    <div className="container mx-auto max-w-screen-lg px-4 py-8 space-y-6">

      {/* ---- 页头 ---- */}
      <div className="flex items-start gap-4">
        <Button variant="ghost" size="icon" className="mt-0.5 shrink-0" onClick={() => navigate('/comparison')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <GitCompare className="h-5 w-5 text-primary shrink-0" />
            <h1 className="text-xl font-bold tracking-tight">符合性审查结果</h1>
            <Badge variant={ssc.variant}>{ssc.label}</Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            <span className="text-primary font-medium">{session.req_filename}</span>
            <span className="mx-2 text-muted-foreground">vs</span>
            <span>{session.resp_filename}</span>
            <span className="ml-3 text-xs">{formatBeijingTime(session.created_at)}</span>
          </p>
        </div>
        <Button variant="outline" size="sm" className="gap-1.5 shrink-0" onClick={handleExport}>
          <Download className="h-4 w-4" />
          导出报告
        </Button>
      </div>

      {/* ---- 概览统计 ---- */}
      {session.findings.length > 0 && <StatsRow findings={session.findings} />}

      {/* ---- 主体 Tabs ---- */}
      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList>
          <TabsTrigger value="findings">
            审查意见
            {session.findings.length > 0 && (
              <span className="ml-1.5 text-xs bg-muted rounded-full px-1.5 py-0.5">
                {session.findings.length}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="report">完整报告</TabsTrigger>
          <TabsTrigger value="req">
            要求文件
            {session.req_sections.length > 0 && (
              <span className="ml-1.5 text-xs bg-muted rounded-full px-1.5 py-0.5">
                {session.req_sections.length}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="resp">
            应答文件
            {session.resp_sections.length > 0 && (
              <span className="ml-1.5 text-xs bg-muted rounded-full px-1.5 py-0.5">
                {session.resp_sections.length}
              </span>
            )}
          </TabsTrigger>
        </TabsList>

        {/* 审查意见 */}
        <TabsContent value="findings" className="mt-4">
          {session.findings.length === 0 ? (
            <p className="text-center text-muted-foreground py-12">
              {session.status === 'failed' ? '分析失败，请检查文件内容和 LLM 配置后重试' : '暂无审查意见'}
            </p>
          ) : (
            <div className="space-y-2">
              {session.findings.map((f) => (
                <FindingCard
                  key={f.finding_id}
                  finding={f}
                  onTraceReq={handleTraceReq}
                  onTraceResp={handleTraceResp}
                />
              ))}
            </div>
          )}
        </TabsContent>

        {/* 完整 Markdown 报告 */}
        <TabsContent value="report" className="mt-4">
          <div className="rounded-xl border bg-card px-6 py-4">
            <MarkdownRenderer content={session.analysis_md} />
          </div>
        </TabsContent>

        {/* 要求文件预览 */}
        <TabsContent value="req" className="mt-4">
          <SectionPanel sections={session.req_sections} highlightRef={reqHighlight} />
        </TabsContent>

        {/* 应答文件预览 */}
        <TabsContent value="resp" className="mt-4">
          <SectionPanel sections={session.resp_sections} highlightRef={respHighlight} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
