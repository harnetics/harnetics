/**
 * [INPUT]: 依赖 @/lib/api 的 fetchImpactReports/analyzeImpact/fetchDocuments
 * [OUTPUT]: 对外提供 Impact 页面组件
 * [POS]: pages 的影响分析首页，US3 报告列表 + 发起新分析
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, ArrowRight, AlertTriangle, ChevronRight } from 'lucide-react'
import { fetchImpactReports, analyzeImpact, fetchDocuments } from '@/lib/api'
import type { ImpactReport, Document } from '@/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'

export default function Impact() {
  const navigate = useNavigate()
  const [reports, setReports] = useState<ImpactReport[]>([])
  const [docs, setDocs] = useState<Document[]>([])
  const [selectedDocId, setSelectedDocId] = useState('')
  const [newVersion, setNewVersion] = useState('')
  const [analyzing, setAnalyzing] = useState(false)

  useEffect(() => {
    fetchImpactReports().then(setReports).catch(() => {})
    fetchDocuments({ per_page: 200 }).then((r) => setDocs(r.documents)).catch(() => {})
  }, [])

  function handleAnalyze() {
    if (!selectedDocId) return
    setAnalyzing(true)
    analyzeImpact({ doc_id: selectedDocId, new_version: newVersion })
      .then((rpt) => navigate(`/impact/${rpt.report_id}`))
      .catch(() => setAnalyzing(false))
  }

  return (
    <div className="container mx-auto max-w-screen-xl px-4 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">变更影响分析</h1>
        <p className="mt-1 text-muted-foreground">选择触发文档，自动分析对下游文档的级联影响</p>
      </div>

      <Card className="border-dashed border-2">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Upload className="h-4 w-4 text-primary" />发起新的影响分析
          </CardTitle>
          <CardDescription>选择触发文档并指定新版本号</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3 items-end">
            <div className="space-y-1.5">
              <Label>触发文档</Label>
              <select
                value={selectedDocId}
                onChange={(e) => setSelectedDocId(e.target.value)}
                className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">选择文档…</option>
                {docs.map((d) => <option key={d.doc_id} value={d.doc_id}>{d.doc_id} {d.title}</option>)}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label>新版本号</Label>
              <Input placeholder="例如 v3.2" value={newVersion} onChange={(e) => setNewVersion(e.target.value)} />
            </div>
            <Button className="gap-2 w-full md:w-auto" disabled={!selectedDocId || analyzing} onClick={handleAnalyze}>
              <Upload className="h-4 w-4" />{analyzing ? '分析中…' : '分析影响'}
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-3">
        <h2 className="text-base font-semibold">历史分析报告</h2>
        {reports.length === 0 ? (
          <p className="text-sm text-muted-foreground">暂无历史报告</p>
        ) : (
          reports.map((rpt) => {
            const criticalCount = rpt.impacted_docs.filter((d) => d.severity === 'Critical').length
            const majorCount = rpt.impacted_docs.filter((d) => d.severity === 'Major').length
            const minorCount = rpt.impacted_docs.filter((d) => d.severity === 'Minor').length
            return (
              <Card key={rpt.report_id} className="cursor-pointer hover:border-primary/50 transition-colors" onClick={() => navigate(`/impact/${rpt.report_id}`)}>
                <CardContent className="py-4 px-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-2 flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <code className="text-sm font-mono font-bold text-primary">{rpt.trigger_doc_id}</code>
                        <span className="flex items-center gap-1 text-sm text-muted-foreground">
                          <code className="bg-muted px-1 rounded text-xs">{rpt.old_version}</code>
                          <ArrowRight className="h-3.5 w-3.5" />
                          <code className="bg-primary/10 text-primary px-1 rounded text-xs font-semibold">{rpt.new_version}</code>
                        </span>
                        <Badge variant="secondary" className="text-xs">{rpt.created_at}</Badge>
                      </div>
                      <p className="text-sm font-medium truncate">{rpt.summary}</p>
                      <Separator />
                      <div className="flex items-center gap-3 flex-wrap">
                        <span className="text-sm text-muted-foreground flex items-center gap-1">
                          <AlertTriangle className="h-4 w-4" />影响 <strong>{rpt.impacted_docs.length}</strong> 份文档
                        </span>
                        {criticalCount > 0 && <Badge variant="destructive">{criticalCount} Critical</Badge>}
                        {majorCount > 0 && <Badge variant="warning">{majorCount} Major</Badge>}
                        {minorCount > 0 && <Badge variant="secondary">{minorCount} Minor</Badge>}
                      </div>
                    </div>
                    <div className="flex items-center gap-1 text-muted-foreground shrink-0">
                      <span className="text-sm">查看报告</span>
                      <ChevronRight className="h-4 w-4" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })
        )}
      </div>
    </div>
  )
}
