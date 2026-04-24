/**
 * [INPUT]: 依赖 @/lib/api 的 fetchDocuments/uploadDocument，依赖 @/types 的 Document
 * [OUTPUT]: 对外提供 Documents 页面组件
 * [POS]: pages 的文档库列表页，US1 核心入口
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */

import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, Search } from 'lucide-react'
import { fetchDocuments, uploadDocument } from '@/lib/api'
import type { Document } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

const statusConfig: Record<string, { label: string; variant: 'success' | 'warning' | 'secondary' | 'destructive' }> = {
  Approved: { label: '已审批', variant: 'success' },
  UnderReview: { label: '审核中', variant: 'warning' },
  Draft: { label: '草稿', variant: 'secondary' },
  Superseded: { label: '已废止', variant: 'destructive' },
}

const departments = ['全部部门', '技术负责人', '系统工程部', '动力系统部', '质量与可靠性部', '试验与验证部', '总体设计部']
const docTypes = ['全部类型', 'ICD', '需求文档', '设计文档', '测试大纲', '分析报告', '管理文档', '模板']
const levels = ['全部层级', '系统层', '分系统层', '全层级']

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
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [search, dept, type, level])

  useEffect(() => { loadDocs() }, [loadDocs])

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

  return (
    <div className="container mx-auto max-w-screen-xl px-4 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">文档库</h1>
          <p className="mt-1 text-muted-foreground">共 {total} 份文档 · 点击行查看详情</p>
        </div>
        <Button className="gap-2" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
          <Upload className="h-4 w-4" />
          {uploading ? '上传中…' : '上传文档'}
        </Button>
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
              <TableHead className="w-[130px]">文档编号</TableHead>
              <TableHead>标题</TableHead>
              <TableHead className="hidden md:table-cell">部门</TableHead>
              <TableHead className="hidden md:table-cell">类型</TableHead>
              <TableHead className="hidden lg:table-cell">层级</TableHead>
              <TableHead className="w-[80px]">版本</TableHead>
              <TableHead className="w-[100px]">状态</TableHead>
              <TableHead className="hidden lg:table-cell w-[110px]">最近更新</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow><TableCell colSpan={8} className="text-center text-muted-foreground py-10">加载中…</TableCell></TableRow>
            ) : docs.length === 0 ? (
              <TableRow><TableCell colSpan={8} className="text-center text-muted-foreground py-10">未找到匹配文档</TableCell></TableRow>
            ) : (
              docs.map((doc) => {
                const sc = statusConfig[doc.status] ?? { label: doc.status, variant: 'secondary' as const }
                return (
                  <TableRow key={doc.doc_id} className="cursor-pointer hover:bg-muted/40 transition-colors" onClick={() => navigate(`/documents/${doc.doc_id}`)}>
                    <TableCell><code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono">{doc.doc_id}</code></TableCell>
                    <TableCell><span className="font-medium text-sm">{doc.title}</span></TableCell>
                    <TableCell className="hidden md:table-cell"><span className="text-sm text-muted-foreground">{doc.department}</span></TableCell>
                    <TableCell className="hidden md:table-cell"><span className="text-sm">{doc.doc_type}</span></TableCell>
                    <TableCell className="hidden lg:table-cell"><span className="text-sm text-muted-foreground">{doc.system_level}</span></TableCell>
                    <TableCell><code className="text-xs text-muted-foreground">{doc.version}</code></TableCell>
                    <TableCell><Badge variant={sc.variant}>{sc.label}</Badge></TableCell>
                    <TableCell className="hidden lg:table-cell text-sm text-muted-foreground">{doc.updated_at}</TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </div>
      <p className="text-sm text-muted-foreground">显示 {docs.length} / {total} 条</p>
    </div>
  )
}
