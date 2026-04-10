/**
 * [INPUT]: 依赖 @/lib/api 的 fetchDocument，依赖 @/types 的 DocumentDetailResponse
 * [OUTPUT]: 对外提供 DocumentDetail 页面组件
 * [POS]: pages 的文档详情页，US1 文档浏览的二级页面
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */

import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, ExternalLink, ChevronRight, FileText, Share2 } from 'lucide-react'
import { fetchDocument } from '@/lib/api'
import type { DocumentDetailResponse } from '@/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'

const statusConfig: Record<string, { label: string; variant: 'success' | 'warning' | 'secondary' | 'destructive' }> = {
  Approved: { label: '已审批', variant: 'success' },
  UnderReview: { label: '审核中', variant: 'warning' },
  Draft: { label: '草稿', variant: 'secondary' },
  Superseded: { label: '已废止', variant: 'destructive' },
}

const relationLabel: Record<string, string> = {
  derived_from: '派生自',
  references: '引用',
  constrained_by: '约束于',
  traces_to: '追溯至',
  supersedes: '取代',
  impacts: '影响',
}

export default function DocumentDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState<DocumentDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    fetchDocument(id)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return <div className="container mx-auto max-w-screen-xl px-4 py-16 text-center text-muted-foreground">加载中…</div>
  }

  if (!data) {
    return (
      <div className="container mx-auto max-w-screen-xl px-4 py-16 text-center">
        <p className="text-muted-foreground">文档不存在或已被删除。</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate('/documents')}>返回文档库</Button>
      </div>
    )
  }

  const { document: doc, sections, upstream, downstream } = data
  const sc = statusConfig[doc.status] ?? { label: doc.status, variant: 'secondary' as const }

  return (
    <div className="container mx-auto max-w-screen-xl px-4 py-6 space-y-6">
      <nav className="flex items-center gap-1 text-sm text-muted-foreground">
        <Link to="/documents" className="hover:text-foreground transition-colors">文档库</Link>
        <ChevronRight className="h-4 w-4" />
        <span className="text-foreground font-medium">{doc.doc_id}</span>
      </nav>

      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold">{doc.title}</h1>
            <Badge variant={sc.variant}>{sc.label}</Badge>
          </div>
          <p className="text-muted-foreground text-sm">{doc.doc_id} · {doc.version} · 最近更新：{doc.updated_at}</p>
        </div>
        <div className="flex gap-2 shrink-0">
          <Button variant="outline" size="sm" className="gap-1.5" onClick={() => navigate('/documents')}>
            <ArrowLeft className="h-4 w-4" />返回
          </Button>
          <Button size="sm" className="gap-1.5" onClick={() => navigate('/draft')}>
            <FileText className="h-4 w-4" />生成对齐草稿
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
        <div className="space-y-4 lg:col-span-1">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">文档元数据</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {[
                { k: '编号', v: <code className="bg-muted px-1 rounded text-xs">{doc.doc_id}</code> },
                { k: '部门', v: doc.department },
                { k: '类型', v: doc.doc_type },
                { k: '层级', v: doc.system_level },
                { k: '版本', v: doc.version },
                { k: '阶段', v: doc.engineering_phase },
                { k: '章节数', v: `${sections.length} 节` },
              ].map(({ k, v }) => (
                <div key={k} className="flex items-start justify-between gap-2">
                  <span className="text-muted-foreground shrink-0">{k}</span>
                  <span className="text-right font-medium">{v}</span>
                </div>
              ))}
            </CardContent>
          </Card>
          <Button variant="outline" size="sm" className="w-full gap-1.5" onClick={() => navigate('/graph')}>
            <Share2 className="h-4 w-4" />查看图谱关系
          </Button>
        </div>

        <div className="lg:col-span-3 space-y-6">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">上游文档（本文档引用）</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {upstream.length === 0 ? (
                  <p className="text-sm text-muted-foreground">暂无上游依赖</p>
                ) : (
                  upstream.map((e) => (
                    <div key={e.edge_id} className="flex items-center justify-between text-sm">
                      <Link to={`/documents/${e.target_doc_id}`} className="font-mono text-primary hover:underline text-xs">{e.target_doc_id}</Link>
                      <Badge variant="outline" className="text-xs">{relationLabel[e.relation] ?? e.relation}</Badge>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">下游文档（引用本文档）</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {downstream.length === 0 ? (
                  <p className="text-sm text-muted-foreground">暂无下游引用</p>
                ) : (
                  downstream.map((e) => (
                    <div key={e.edge_id} className="flex items-center justify-between text-sm">
                      <Link to={`/documents/${e.source_doc_id}`} className="font-mono text-primary hover:underline text-xs">{e.source_doc_id}</Link>
                      <Badge variant="outline" className="text-xs">{relationLabel[e.relation] ?? e.relation}</Badge>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-2">
            <h2 className="text-base font-semibold flex items-center gap-2">
              <FileText className="h-4 w-4 text-primary" />
              文档章节
              <Badge variant="secondary" className="text-xs">{sections.length} 节</Badge>
            </h2>
            {sections.length === 0 ? (
              <Card>
                <CardContent className="py-8 text-center text-muted-foreground text-sm">
                  章节内容加载中 — 请上传实际文档解析
                  <div className="mt-3">
                    <Button variant="outline" size="sm" className="gap-1.5">
                      <ExternalLink className="h-3 w-3" />上传 / 重新解析
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : (
              sections.map((s) => (
                <Card key={s.section_id}>
                  <CardContent className="py-4 px-5">
                    <p className="font-semibold text-sm mb-2">{s.heading}</p>
                    <Separator className="mb-2" />
                    <pre className="text-xs text-muted-foreground font-mono whitespace-pre-wrap leading-relaxed">{s.content}</pre>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
