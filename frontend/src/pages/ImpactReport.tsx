/**
 * [INPUT]: 依赖 @/lib/api 的 fetchImpactReport，依赖 @/lib/utils 的 severity/时间格式化工具，依赖 @/types (AffectedSection)
 * [OUTPUT]: 对外提供 ImpactReportPage 页面组件
 * [POS]: pages 的影响分析报告详情页，US3 报告汇总 + 表格 + 详情 + 草稿预填导航
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */

import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Download, ArrowRight, ChevronRight } from 'lucide-react'
import { fetchImpactReport } from '@/lib/api'
import type { ImpactReport, AffectedSection } from '@/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { formatBeijingTime, severityKey, severityLabel } from '@/lib/utils'

const impactBadge: Record<string, 'destructive' | 'warning' | 'secondary'> = {
  critical: 'destructive',
  major: 'warning',
  minor: 'secondary',
}

function SectionBadge({ section }: { section: AffectedSection | string }) {
  if (typeof section === 'string') {
    return <code className="text-xs bg-muted px-1 rounded">{section}</code>
  }
  const label = section.heading || section.section_id
  return (
    <code className="text-xs bg-primary/10 text-primary px-1.5 py-0.5 rounded cursor-help" title={section.reason || undefined}>
      {label}
    </code>
  )
}

function buildDraftUrl(report: ImpactReport, docIds: string[]): string {
  const params = new URLSearchParams()
  params.set('report_id', report.report_id)
  params.set('source_report_id', report.report_id)
  params.set('trigger_doc_id', report.trigger_doc_id)
  if (report.new_version) params.set('new_version', report.new_version)
  for (const id of docIds) params.append('impacted_doc_id', id)
  return `/draft?${params}`
}

export default function ImpactReportPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [rpt, setRpt] = useState<ImpactReport | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    fetchImpactReport(id)
      .then(setRpt)
      .catch(() => setRpt(null))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="container mx-auto max-w-screen-xl px-4 py-16 text-center text-muted-foreground">加载中…</div>
  if (!rpt) {
    return (
      <div className="container mx-auto max-w-screen-xl px-4 py-16 text-center">
        <p className="text-muted-foreground">报告不存在。</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate('/impact')}>返回</Button>
      </div>
    )
  }

  const criticalCount = rpt.impacted_docs.filter((d) => severityKey(d.severity) === 'critical').length
  const majorCount = rpt.impacted_docs.filter((d) => severityKey(d.severity) === 'major').length
  const minorCount = rpt.impacted_docs.filter((d) => severityKey(d.severity) === 'minor').length

  return (
    <div className="container mx-auto max-w-screen-xl px-4 py-6 space-y-6">
      <nav className="flex items-center gap-1 text-sm text-muted-foreground">
        <Link to="/impact" className="hover:text-foreground transition-colors">变更影响</Link>
        <ChevronRight className="h-4 w-4" />
        <span className="text-foreground font-medium">{rpt.report_id}</span>
      </nav>

      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-xl font-bold">影响分析报告</h1>
            <code className="text-xs bg-muted px-2 py-0.5 rounded font-mono">{rpt.report_id}</code>
          </div>
          <div className="flex items-center gap-2 text-sm flex-wrap">
            <code className="font-mono text-primary font-semibold">{rpt.trigger_doc_id}</code>
            <span className="flex items-center gap-1 text-muted-foreground">
              <code className="bg-muted px-1 rounded text-xs">{rpt.old_version}</code>
              <ArrowRight className="h-3.5 w-3.5" />
              <code className="bg-primary/10 text-primary px-1 rounded text-xs font-semibold">{rpt.new_version}</code>
            </span>
            <Badge variant="secondary">{formatBeijingTime(rpt.created_at)}</Badge>
            {rpt.analysis_mode && <Badge variant="outline" className="text-xs">{rpt.analysis_mode === 'ai_vector' ? 'AI 向量分析' : '规则引擎'}</Badge>}
          </div>
        </div>
        <div className="flex gap-2 shrink-0">
          <Button variant="outline" size="sm" className="gap-1.5" onClick={() => navigate('/impact')}>
            <ArrowLeft className="h-4 w-4" />返回
          </Button>
          <Button variant="outline" size="sm" className="gap-1.5">
            <Download className="h-4 w-4" />导出报告
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Card><CardContent className="pt-4 pb-4 text-center"><p className="text-2xl font-bold">{rpt.impacted_docs.length}</p><p className="text-xs text-muted-foreground mt-1">受影响文档</p></CardContent></Card>
        <Card className="border-destructive/40"><CardContent className="pt-4 pb-4 text-center"><p className="text-2xl font-bold text-destructive">{criticalCount}</p><p className="text-xs text-muted-foreground mt-1">Critical</p></CardContent></Card>
        <Card className="border-amber-400/40"><CardContent className="pt-4 pb-4 text-center"><p className="text-2xl font-bold text-amber-500">{majorCount}</p><p className="text-xs text-muted-foreground mt-1">Major</p></CardContent></Card>
        <Card><CardContent className="pt-4 pb-4 text-center"><p className="text-2xl font-bold text-muted-foreground">{minorCount}</p><p className="text-xs text-muted-foreground mt-1">Minor</p></CardContent></Card>
      </div>

      {rpt.impacted_docs.length > 0 && (
        <div className="flex justify-end">
          <Button size="sm" className="gap-1.5" onClick={() => navigate(buildDraftUrl(rpt, rpt.impacted_docs.map(d => d.doc_id)))}>
            一键生成对齐草稿<ChevronRight className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}

      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-base">分析摘要</CardTitle></CardHeader>
        <CardContent>
          <pre className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">{rpt.summary}</pre>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-base">受影响文档清单</CardTitle></CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50">
                <TableHead className="w-[130px]">文档编号</TableHead>
                <TableHead>文档标题</TableHead>
                <TableHead className="w-[90px]">影响等级</TableHead>
                <TableHead className="hidden lg:table-cell">受影响章节</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rpt.impacted_docs.map((d, i) => (
                <TableRow key={i} className="hover:bg-muted/30">
                  <TableCell><code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono">{d.doc_id}</code></TableCell>
                  <TableCell><span className="font-medium text-sm">{d.title}</span></TableCell>
                  <TableCell><Badge variant={impactBadge[severityKey(d.severity)] ?? 'secondary'}>{severityLabel(d.severity)}</Badge></TableCell>
                  <TableCell className="hidden lg:table-cell">
                    {d.affected_sections.length === 0 ? (
                      <span className="text-xs text-muted-foreground">未精确定位章节，建议人工复核</span>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {d.affected_sections.map((s, j) => <SectionBadge key={j} section={s} />)}
                      </div>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <div className="space-y-3">
        <h2 className="text-base font-semibold">影响详情</h2>
        {rpt.impacted_docs.length === 0 && (
          <Card>
            <CardContent className="py-8 text-sm text-muted-foreground">
              当前图谱中没有发现依赖 <code className="bg-muted px-1 py-0.5 rounded text-xs">{rpt.trigger_doc_id}</code> 的下游文档。通常这意味着：
              1. 这份文档尚未被其他文档引用。
              2. 依赖关系还没有被导入到图谱。
            </CardContent>
          </Card>
        )}
        {rpt.impacted_docs.map((d, i) => (
          <Card key={i} className={severityKey(d.severity) === 'critical' ? 'border-destructive/40' : severityKey(d.severity) === 'major' ? 'border-amber-400/40' : ''}>
            <CardContent className="py-4 px-5">
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <code className="font-mono text-sm font-bold text-primary">{d.doc_id}</code>
                    <Badge variant={impactBadge[severityKey(d.severity)] ?? 'secondary'}>{severityLabel(d.severity)}</Badge>
                  </div>
                  <p className="text-sm font-medium">{d.title}</p>
                  <p className="text-sm text-muted-foreground">{d.relation}</p>
                  {d.affected_sections.length === 0 ? (
                    <p className="text-xs text-muted-foreground">未精确定位章节，建议结合关系链人工复核。</p>
                  ) : (
                    <div className="space-y-1 mt-1">
                      <span className="text-xs text-muted-foreground">受影响章节：</span>
                      <div className="flex flex-wrap gap-1">
                        {d.affected_sections.map((s, j) => <SectionBadge key={j} section={s} />)}
                      </div>
                    </div>
                  )}
                </div>
                <Button variant="ghost" size="sm" className="gap-1 shrink-0 text-primary" onClick={() => navigate(buildDraftUrl(rpt, [d.doc_id]))}>
                  生成对齐草稿<ChevronRight className="h-3.5 w-3.5" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
