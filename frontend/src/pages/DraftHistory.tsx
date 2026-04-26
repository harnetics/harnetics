/**
 * [INPUT]: 依赖 @/lib/api 的 fetchDrafts/deleteDraft，依赖 @/types 的 DraftSummary
 * [OUTPUT]: 对外提供 DraftHistory 页面组件
 * [POS]: pages 的历史草稿列表页，US6 展示所有草稿及其状态，支持逐条删除
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, Plus, CheckCircle, XCircle, Trash2 } from 'lucide-react'
import { fetchDrafts, deleteDraft } from '@/lib/api'
import type { DraftSummary } from '@/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'

const statusConfig: Record<string, { label: string; variant: 'success' | 'warning' | 'destructive' | 'secondary'; icon: React.ReactNode }> = {
  eval_pass: { label: '通过', variant: 'success', icon: <CheckCircle className="h-3.5 w-3.5" /> },
  blocked: { label: '阻断', variant: 'destructive', icon: <XCircle className="h-3.5 w-3.5" /> },
  completed: { label: '已完成', variant: 'secondary', icon: <FileText className="h-3.5 w-3.5" /> },
}

export default function DraftHistory() {
  const navigate = useNavigate()
  const [drafts, setDrafts] = useState<DraftSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState<string | null>(null)

  useEffect(() => {
    fetchDrafts()
      .then(setDrafts)
      .catch(() => setDrafts([]))
      .finally(() => setLoading(false))
  }, [])

  async function handleDelete(e: React.MouseEvent, draftId: string) {
    e.stopPropagation()
    setDeleting(draftId)
    try {
      await deleteDraft(draftId)
      setDrafts(prev => prev.filter(d => d.draft_id !== draftId))
    } finally {
      setDeleting(null)
    }
  }

  if (loading) {
    return <div className="container mx-auto max-w-screen-xl px-4 py-16 text-center text-muted-foreground">加载中…</div>
  }

  return (
    <div className="container mx-auto max-w-screen-xl px-4 py-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">历史草稿</h1>
          <p className="mt-1 text-muted-foreground">查看所有已生成的对齐草稿及其评估状态</p>
        </div>
        <Button className="gap-2" onClick={() => navigate('/draft')}>
          <Plus className="h-4 w-4" />新建草稿
        </Button>
      </div>

      {drafts.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center">
            <FileText className="mx-auto h-12 w-12 text-muted-foreground/40" />
            <p className="mt-4 text-muted-foreground">还没有任何草稿，点击上方按钮创建第一份。</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {drafts.map((d) => {
            const cfg = statusConfig[d.status] ?? statusConfig.completed
            return (
              <Card
                key={d.draft_id}
                className="cursor-pointer transition-colors hover:bg-muted/40"
                onClick={() => navigate(`/draft/${d.draft_id}`)}
              >
                <CardContent className="flex items-center gap-4 py-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-sm truncate">{d.subject || d.draft_id}</span>
                      <Badge variant={cfg.variant} className="gap-1 text-xs shrink-0">
                        {cfg.icon}{cfg.label}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                      <code className="bg-muted px-1 py-0.5 rounded">{d.draft_id}</code>
                      <span>{d.generated_by}</span>
                      <span>{d.created_at}</span>
                    </div>
                  </div>
                  {d.eval_summary && (
                    <div className="flex gap-1.5 shrink-0">
                      {d.eval_summary.pass > 0 && <Badge variant="success" className="text-xs">{d.eval_summary.pass}✓</Badge>}
                      {d.eval_summary.warn > 0 && <Badge variant="warning" className="text-xs">{d.eval_summary.warn}⚠</Badge>}
                      {d.eval_summary.block > 0 && <Badge variant="destructive" className="text-xs">{d.eval_summary.block}✗</Badge>}
                    </div>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="shrink-0 text-muted-foreground hover:text-destructive"
                    disabled={deleting === d.draft_id}
                    onClick={(e) => handleDelete(e, d.draft_id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
