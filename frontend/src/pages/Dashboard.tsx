/**
 * [INPUT]: 依赖 @/lib/api 的 fetchDashboardStats，依赖 @/types 的 DashboardStats
 * [OUTPUT]: 对外提供 Dashboard 页面组件
 * [POS]: pages 的系统仪表盘，US5 首页概览 + 快捷操作
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */

import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { FileText, Link2, AlertTriangle, FileEdit, GitMerge, Upload, TrendingUp } from 'lucide-react'
import { fetchDashboardStats } from '@/lib/api'
import type { DashboardStats } from '@/types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)

  useEffect(() => {
    fetchDashboardStats().then(setStats).catch(() => {})
  }, [])

  const statCards = stats
    ? [
        { label: '文档总数', value: stats.documents, sub: `${stats.icd_parameters} 个 ICD 参数`, icon: FileText, color: 'text-primary' },
        { label: '跨文档关系', value: stats.drafts, sub: `${stats.impact_reports} 份影响报告`, icon: Link2, color: 'text-blue-600' },
        { label: '过期引用/告警', value: stats.stale_references, sub: '需人工审核', icon: AlertTriangle, color: 'text-amber-500' },
      ]
    : []

  const passRate = stats?.eval_pass_rate != null ? Math.round(stats.eval_pass_rate * 100) : null

  return (
    <div className="container mx-auto max-w-screen-xl px-4 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">系统仪表盘</h1>
        <p className="mt-1 text-muted-foreground">实时掌握文档对齐状态 · 驱动工程决策</p>
      </div>

      {!stats ? (
        <p className="text-muted-foreground">加载中…</p>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {statCards.map((s) => (
              <Card key={s.label}>
                <CardHeader className="pb-2 flex flex-row items-center justify-between">
                  <CardDescription>{s.label}</CardDescription>
                  <s.icon className={`h-5 w-5 ${s.color}`} />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{s.value}</div>
                  <p className="mt-1 text-xs text-muted-foreground">{s.sub}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-primary" />文档健康度
                </CardTitle>
                <CardDescription>基于文档图谱自动计算</CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">LLM 可用性</span>
                    <span className={stats.llm_available ? 'text-green-600' : 'text-destructive'}>
                      {stats.llm_available ? '可用' : '不可用'}
                    </span>
                  </div>
                  <Progress value={stats.llm_available ? 100 : 0} />
                </div>
                {passRate != null && (
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">评估通过率</span>
                      <span className={passRate >= 90 ? 'text-green-600' : passRate >= 70 ? 'text-amber-500' : 'text-destructive'}>
                        {passRate}%
                      </span>
                    </div>
                    <Progress value={passRate} />
                    <p className="text-xs text-muted-foreground">{stats.eval_pass} 通过 / {stats.eval_blocked} 阻断</p>
                  </div>
                )}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">陈旧引用数</span>
                    <span className={stats.stale_references === 0 ? 'text-green-600' : 'text-amber-500'}>
                      {stats.stale_references}
                    </span>
                  </div>
                  <Progress value={stats.stale_references === 0 ? 100 : Math.max(0, 100 - stats.stale_references * 10)} />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">快捷操作</CardTitle>
                <CardDescription>核心工作流入口</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Link to="/draft" className="block">
                  <Button className="w-full justify-start gap-2" size="lg"><FileEdit className="h-4 w-4" />生成对齐草稿</Button>
                </Link>
                <Link to="/impact" className="block">
                  <Button variant="outline" className="w-full justify-start gap-2" size="lg"><GitMerge className="h-4 w-4" />变更影响分析</Button>
                </Link>
                <Link to="/documents" className="block">
                  <Button variant="outline" className="w-full justify-start gap-2" size="lg"><Upload className="h-4 w-4" />上传新文档</Button>
                </Link>
                <Link to="/graph" className="block">
                  <Button variant="ghost" className="w-full justify-start gap-2" size="lg"><Link2 className="h-4 w-4" />查看文档图谱</Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  )
}
