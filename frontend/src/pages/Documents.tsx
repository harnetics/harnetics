/**
 * [INPUT]: 依赖 @/lib/api 的 fetchDocuments/uploadDocument/deleteDocument/batchDeleteDocuments/fetchStatus/reindexDocuments，依赖 @/types 的 Document/DashboardStats
 * [OUTPUT]: 对外提供 Documents 页面组件
 * [POS]: pages 的文档库列表页，US1 核心入口，支持上传、按行删除、多选批量删除，以及 Embedding 索引冲突提示
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, Search, Trash2, RefreshCw, AlertTriangle } from 'lucide-react'
import { fetchDocuments, uploadDocument, deleteDocument, batchDeleteDocuments, fetchStatus, reindexDocuments } from '@/lib/api'
import type { Document } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { ConfirmDialog } from '@/components/ui/confirm-dialog'

const statusConfig: Record<string, { label: string; variant: 'success' | 'warning' | 'secondary' | 'destructive' }> = {
  Approved: { label: '已审批', variant: 'success' },
  UnderReview: { label: '审核中', variant: 'warning' },
  Draft: { label: '草稿', variant: 'secondary' },
  Superseded: { label: '已废止', variant: 'destructive' },
}

const departments = ['全部部门', '技术负责人', '系统工程部', '动力系统部', '质量与可靠性部', '试验与验证部', '总体设计部']
const docTypes = ['全部类型', 'ICD', '需求文档', '设计文档', '测试大纲', '分析报告', '管理文档', '模板']
const levels = ['全部层级', '系统层', '分系统层', '全层级']

type CheckboxState = boolean | 'indeterminate'

export default function Documents() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [dept, setDept] = useState('全部部门')
  const [type, setType] = useState('全部类型')
  const [level, setLevel] = useState('全部层级')
  const [docs, setDocs] = useState<Document[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [pendingDelete, setPendingDelete] = useState<Document | null>(null)
  // 多选批量删除
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [bulkDeleting, setBulkDeleting] = useState(false)
  const [bulkConfirmOpen, setBulkConfirmOpen] = useState(false)
  // Embedding 冲突提示
  const [embReset, setEmbReset] = useState(false)
  const [reindexing, setReindexing] = useState(false)
  const [reindexResult, setReindexResult] = useState<string>('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const loadDocs = useCallback(() => {
    setLoading(true)
    fetchDocuments({
      department: dept === '全部部门' ? undefined : dept,
      doc_type: type === '全部类型' ? undefined : type,
      system_level: level === '全部层级' ? undefined : level,
      q: search || undefined,
      per_page: 200,
    })
      .then((res) => {
        setDocs(res.documents)
        setTotal(res.total)
        setSelected(new Set())
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [search, dept, type, level])

  useEffect(() => { loadDocs() }, [loadDocs])

  // 启动时检查 embedding 冲突状态
  useEffect(() => {
    fetchStatus()
      .then((s) => setEmbReset(s.embedding_collection_reset))
      .catch(() => {})
  }, [])

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files?.length) return
    setUploading(true)
    setUploadError('')
    const errors: string[] = []
    for (const file of Array.from(files)) {
      try {
        await uploadDocument(file)
      } catch (err) {
        errors.push(`${file.name}: ${err instanceof Error ? err.message : '上传失败'}`)
      }
    }
    if (errors.length) setUploadError(errors.join('\n'))
    setUploading(false)
    loadDocs()
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleDelete = async (e: React.MouseEvent, doc: Document) => {
    e.stopPropagation()
    setPendingDelete(doc)
  }

  const confirmDelete = async () => {
    if (!pendingDelete) return
    const doc = pendingDelete
    setDeletingId(doc.doc_id)
    try {
      await deleteDocument(doc.doc_id)
      loadDocs()
    } catch (err) {
      alert(`删除失败：${err instanceof Error ? err.message : '未知错误'}`)
    } finally {
      setDeletingId(null)
      setPendingDelete(null)
    }
  }

  const handleBulkDelete = async () => {
    if (selected.size === 0) return
    setBulkConfirmOpen(true)
  }

  const confirmBulkDelete = async () => {
    if (selected.size === 0) return
    setBulkDeleting(true)
    const { failed } = await batchDeleteDocuments(Array.from(selected))
    setBulkDeleting(false)
    setBulkConfirmOpen(false)
    if (failed.length) alert(`以下文档删除失败：\n${failed.join('\n')}`)
    loadDocs()
  }

  const handleReindex = async () => {
    setReindexing(true)
    setReindexResult('')
    try {
      const res = await reindexDocuments()
      setEmbReset(false)
      setReindexResult(`已索引 ${res.indexed_documents} 份文档，共 ${res.indexed_sections} 个章节`)
    } catch (err) {
      setReindexResult(`索引失败：${err instanceof Error ? err.message : '未知错误'}`)
    } finally {
      setReindexing(false)
    }
  }

  // ---- 多选辅助 ----
  const visibleIds = docs.map((d) => d.doc_id)
  const allSelected = visibleIds.length > 0 && visibleIds.every((id) => selected.has(id))
  const someSelected = visibleIds.some((id) => selected.has(id))

  const toggleAll = () => {
    if (allSelected) {
      setSelected(new Set())
    } else {
      setSelected(new Set(visibleIds))
    }
  }

  const toggleOne = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  return (
    <div className="container mx-auto max-w-screen-xl px-4 py-8 space-y-6">

      {/* ---- Embedding 冲突重置提示 Banner ---- */}
      {embReset && (
        <div className="flex items-start gap-3 rounded-lg border border-amber-400/50 bg-amber-50 dark:bg-amber-950/30 px-4 py-3 text-sm">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" />
          <div className="flex-1">
            <p className="font-medium text-amber-800 dark:text-amber-300">向量索引已重置</p>
            <p className="mt-0.5 text-amber-700 dark:text-amber-400">
              Embedding 模型已更换，ChromaDB collection 已自动重建。请重新索引以恢复语义搜索能力。
            </p>
            {reindexResult && <p className="mt-1 text-xs text-amber-600 dark:text-amber-500">{reindexResult}</p>}
          </div>
          <Button
            size="sm"
            variant="outline"
            className="shrink-0 border-amber-400 text-amber-700 hover:bg-amber-100 dark:text-amber-300 dark:hover:bg-amber-900/40 gap-1.5"
            disabled={reindexing}
            onClick={handleReindex}
          >
            <RefreshCw className={`h-3.5 w-3.5 ${reindexing ? 'animate-spin' : ''}`} />
            {reindexing ? '索引中…' : '重新索引'}
          </Button>
        </div>
      )}
      {!embReset && reindexResult && (
        <p className="text-sm text-green-600 dark:text-green-400">{reindexResult}</p>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">文档库</h1>
          <p className="mt-1 text-muted-foreground">共 {total} 份文档 · 点击行查看详情</p>
        </div>
        <div className="flex items-center gap-2">
          {selected.size > 0 && (
            <Button
              variant="destructive"
              size="sm"
              className="gap-1.5"
              disabled={bulkDeleting}
              onClick={handleBulkDelete}
            >
              <Trash2 className="h-4 w-4" />
              {bulkDeleting ? '删除中…' : `删除选中 (${selected.size})`}
            </Button>
          )}
          <Button className="gap-2" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
            <Upload className="h-4 w-4" />
            {uploading ? '上传中…' : '上传文档'}
          </Button>
        </div>
        <input ref={fileInputRef} type="file" multiple accept=".md,.yaml,.yml,.docx,.xlsx,.csv,.pdf" className="hidden" onChange={handleUpload} />
      </div>
      {uploadError && <p className="text-sm text-destructive whitespace-pre-line">{uploadError}</p>}

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input placeholder="搜索文档编号或标题…" value={search} onChange={(e) => setSearch(e.target.value)} className="pl-8" />
        </div>
        {([
          { val: dept, set: setDept, opts: departments },
          { val: type, set: setType, opts: docTypes },
          { val: level, set: setLevel, opts: levels },
        ] as const).map(({ val, set, opts }) => (
          <select key={opts[0]} value={val} onChange={(e) => set(e.target.value)} className="h-9 rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring">
            {opts.map((o) => <option key={o}>{o}</option>)}
          </select>
        ))}
        {(search || dept !== '全部部门' || type !== '全部类型' || level !== '全部层级') && (
          <Button variant="ghost" size="sm" onClick={() => { setSearch(''); setDept('全部部门'); setType('全部类型'); setLevel('全部层级') }}>重置</Button>
        )}
      </div>

      <div className="rounded-xl border bg-card overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/50">
              <TableHead className="w-[44px] pl-4">
                <input
                  type="checkbox"
                  checked={allSelected}
                  ref={(node) => {
                    if (node) {
                      node.indeterminate = someSelected && !allSelected
                    }
                  }}
                  onChange={() => toggleAll()}
                  aria-label="全选"
                  className="h-4 w-4 rounded border-input accent-foreground"
                  onClick={(e: React.MouseEvent<HTMLInputElement>) => e.stopPropagation()}
                />
              </TableHead>
              <TableHead className="w-[130px]">文档编号</TableHead>
              <TableHead>标题</TableHead>
              <TableHead className="hidden md:table-cell">部门</TableHead>
              <TableHead className="hidden md:table-cell">类型</TableHead>
              <TableHead className="hidden lg:table-cell">层级</TableHead>
              <TableHead className="w-[80px]">版本</TableHead>
              <TableHead className="w-[100px]">状态</TableHead>
              <TableHead className="hidden lg:table-cell w-[160px]">最近更新</TableHead>
              <TableHead className="w-[52px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow><TableCell colSpan={10} className="text-center text-muted-foreground py-10">加载中…</TableCell></TableRow>
            ) : docs.length === 0 ? (
              <TableRow><TableCell colSpan={10} className="text-center text-muted-foreground py-10">未找到匹配文档</TableCell></TableRow>
            ) : (
              docs.map((doc) => {
                const sc = statusConfig[doc.status] ?? { label: doc.status, variant: 'secondary' as const }
                const isSelected = selected.has(doc.doc_id)
                return (
                  <TableRow
                    key={doc.doc_id}
                    className={`cursor-pointer hover:bg-muted/40 transition-colors ${isSelected ? 'bg-muted/30' : ''}`}
                    onClick={() => navigate(`/documents/${doc.doc_id}`)}
                  >
                    <TableCell className="pl-4" onClick={(e) => { e.stopPropagation(); toggleOne(doc.doc_id) }}>
                      <input
                        type="checkbox"
                        checked={isSelected}
                        aria-label={`选择 ${doc.doc_id}`}
                        onChange={() => toggleOne(doc.doc_id)}
                        className="h-4 w-4 rounded border-input accent-foreground"
                      />
                    </TableCell>
                    <TableCell><code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono">{doc.doc_id}</code></TableCell>
                    <TableCell><span className="font-medium text-sm">{doc.title}</span></TableCell>
                    <TableCell className="hidden md:table-cell"><span className="text-sm text-muted-foreground">{doc.department}</span></TableCell>
                    <TableCell className="hidden md:table-cell"><span className="text-sm">{doc.doc_type}</span></TableCell>
                    <TableCell className="hidden lg:table-cell"><span className="text-sm text-muted-foreground">{doc.system_level}</span></TableCell>
                    <TableCell><code className="text-xs text-muted-foreground">{doc.version}</code></TableCell>
                    <TableCell><Badge variant={sc.variant}>{sc.label}</Badge></TableCell>
                    <TableCell className="hidden lg:table-cell text-sm text-muted-foreground whitespace-nowrap">{doc.updated_at}</TableCell>
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-muted-foreground hover:text-destructive"
                        disabled={deletingId === doc.doc_id}
                        onClick={(e) => handleDelete(e, doc)}
                        title="删除文档"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </div>
      <p className="text-sm text-muted-foreground">
        显示 {docs.length} / {total} 条
        {selected.size > 0 && <span className="ml-2 text-foreground">· 已选中 {selected.size} 份</span>}
      </p>

      <ConfirmDialog
        open={pendingDelete !== null}
        title="删除文档"
        description={pendingDelete ? `确认删除文档 "${pendingDelete.title}"？此操作不可撤销。` : ''}
        confirmLabel="删除"
        busy={deletingId !== null}
        onConfirm={confirmDelete}
        onCancel={() => {
          if (deletingId === null) setPendingDelete(null)
        }}
      />
      <ConfirmDialog
        open={bulkConfirmOpen}
        title="批量删除文档"
        description={`确认删除选中的 ${selected.size} 份文档？此操作不可撤销。`}
        confirmLabel="删除"
        busy={bulkDeleting}
        onConfirm={confirmBulkDelete}
        onCancel={() => {
          if (!bulkDeleting) setBulkConfirmOpen(false)
        }}
      />
    </div>
  )
}
