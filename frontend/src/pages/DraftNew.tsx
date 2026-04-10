/**
 * [INPUT]: 依赖 @/lib/api 的 fetchDocuments/generateDraft，依赖 @/types
 * [OUTPUT]: 对外提供 DraftNew 页面组件
 * [POS]: pages 的草稿创建页，US2 两步式草稿生成工作台
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Check, ChevronRight, FileText, Sparkles } from 'lucide-react'
import { fetchDocuments, generateDraft } from '@/lib/api'
import type { Document } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'

export default function DraftNew() {
  const navigate = useNavigate()
  const [step, setStep] = useState<1 | 2>(1)
  const [topic, setTopic] = useState('')
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [generating, setGenerating] = useState(false)
  const [candidates, setCandidates] = useState<Document[]>([])
  const [allDocs, setAllDocs] = useState<Document[]>([])

  useEffect(() => {
    fetchDocuments({ per_page: 200 })
      .then((res) => setAllDocs(res.documents))
      .catch(() => {})
  }, [])

  function toggleDoc(docId: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(docId) ? next.delete(docId) : next.add(docId)
      return next
    })
  }

  function handleSearch() {
    setCandidates(allDocs)
    setStep(2)
  }

  function handleGenerate() {
    setGenerating(true)
    generateDraft({
      subject: topic,
      related_doc_ids: Array.from(selected),
    })
      .then((draft) => navigate(`/draft/${draft.draft_id}`))
      .catch(() => setGenerating(false))
  }

  return (
    <div className="container mx-auto max-w-screen-xl px-4 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">草稿工作台</h1>
        <p className="mt-1 text-muted-foreground">填写草稿参数，检索候选来源，一键生成对齐草稿</p>
      </div>

      <div className="flex items-center gap-2 text-sm">
        <span className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${step >= 1 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'}`}>1</span>
        <span className={step >= 1 ? 'font-medium' : 'text-muted-foreground'}>填写草稿参数</span>
        <ChevronRight className="h-4 w-4 text-muted-foreground" />
        <span className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${step >= 2 ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'}`}>2</span>
        <span className={step >= 2 ? 'font-medium' : 'text-muted-foreground'}>确认来源文档</span>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <FileText className="h-4 w-4 text-primary" />步骤一：草稿参数
            </CardTitle>
            <CardDescription>描述草稿主题并设定文档类型信息</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="topic">草稿主题描述</Label>
              <Textarea id="topic" rows={4} placeholder="请描述需要生成的文档内容，越详细越准确…" value={topic} onChange={(e) => setTopic(e.target.value)} />
            </div>
            <Separator />
            <Button className="w-full gap-2" onClick={handleSearch} disabled={!topic.trim()}>
              <Search className="h-4 w-4" />检索候选来源文档
            </Button>
          </CardContent>
        </Card>

        <Card className={step < 2 ? 'opacity-50 pointer-events-none' : ''}>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Search className="h-4 w-4 text-primary" />步骤二：候选来源文档
            </CardTitle>
            <CardDescription>已检索到 {candidates.length} 份文档，勾选要引用的来源</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {step < 2 ? (
              <p className="text-sm text-muted-foreground text-center py-8">请先完成步骤一</p>
            ) : (
              <>
                {candidates.map((doc) => {
                  const checked = selected.has(doc.doc_id)
                  return (
                    <label
                      key={doc.doc_id}
                      className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${checked ? 'border-primary bg-primary/5' : 'border-border hover:bg-muted/40'}`}
                      onClick={() => toggleDoc(doc.doc_id)}
                    >
                      <div className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border ${checked ? 'bg-primary border-primary' : 'border-input'}`}>
                        {checked && <Check className="h-3 w-3 text-primary-foreground" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <code className="text-xs font-mono text-primary">{doc.doc_id}</code>
                          <Badge variant="secondary" className="text-xs">{doc.version}</Badge>
                          <Badge variant="outline" className="text-xs">{doc.doc_type}</Badge>
                        </div>
                        <p className="text-sm font-medium mt-0.5 truncate">{doc.title}</p>
                        <p className="text-xs text-muted-foreground">{doc.department}</p>
                      </div>
                    </label>
                  )
                })}
                <Separator />
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">已选 <strong>{selected.size}</strong> 份来源文档</p>
                  <Button className="w-full gap-2" disabled={selected.size === 0 || generating} onClick={handleGenerate}>
                    {generating ? (
                      <><div className="h-4 w-4 rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground animate-spin" />AI 生成中…</>
                    ) : (
                      <><Sparkles className="h-4 w-4" />生成对齐草稿</>
                    )}
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
