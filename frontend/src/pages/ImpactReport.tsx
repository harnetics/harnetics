/**
 * [INPUT]: 依赖 @/lib/api 的 fetchImpactReport，依赖 @/types
 * [OUTPUT]: 对外提供 ImpactReportPage 页面组件
 * [POS]: pages 的影响分析报告详情页，US3 报告汇总 + 表格 + 详情
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */

import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Download, ArrowRight, ChevronRight } from 'lucide-react'
import { fetchImpactReport } from '@/lib/api'
import type { ImpactReport } from '@/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

const impactBadge: Record<string, 'destructive' | 'warning' | 'secondary'> = {
  Critical: 'destructive',
  Major: 'warning',
  Minor: 'secondary',
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

  const criticalCount = rpt.impacted_docs.filter((d) => d.severity === 'Critical').length
  const majorCount = rpt.impacted_docs.filter((d) => d.severity === 'Major').length
  const minorCount = rpt.impacted_docs.filter((d) => d.severity === 'Minor').length

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
            <Badge variant="secondary">{rpt.created_at}</Badge>
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
                  <TableCell><Badge variant={impactBadge[d.severity] ?? 'secondary'}>{d.severity}</Badge></TableCell>
                  <TableCell className="hidden lg:table-cell">
                    <div className="flex flex-wrap gap-1">
                      {d.affected_sections.map((s, j) => <code key={j} className="text-xs bg-muted px-1 rounded">{s}</code>)}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <div className="space-y-3">
        <h2 className="text-base font-semibold">影响详情</h2>
        {rpt.impacted_docs.map((d, i) => (
          <Card key={i} className={d.severity === 'Critical' ? 'border-destructive/40' : d.severity === 'Major' ? 'border-amber-400/40' : ''}>
            <CardContent className="py-4 px-5">
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <code className="font-mono text-sm font-bold text-primary">{d.doc_id}</code>
                    <Badge variant={impactBadge[d.severity] ?? 'secondary'}>{d.severity}</Badge>
                  </div>
                  <p className="text-sm font-medium">{d.title}</p>
                  <p className="text-sm text-muted-foreground">{d.relation}</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    <span className="text-xs text-muted-foreground">受影响章节：</span>
                    {d.affected_sections.map((s, j) => <code key={j} className="text-xs bg-muted px-1 rounded">{s}</code>)}
                  </div>
                </div>
                <Button variant="ghost" size="sm" className="gap-1 shrink-0 text-primary" onClick={() => navigate('/draft')}>
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
