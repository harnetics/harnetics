/**
 * [INPUT]: 依赖 @/lib/api 的 fetchEvolutionStats，依赖 @/types 的 EvolutionStats/EvolutionSignal
 * [OUTPUT]: 对外提供 Evolution 页面组件
 * [POS]: pages 的 GEP 进化视图，展示本地信号历史、当前策略、标签分布与失败检查器统计
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */

import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Dna, RefreshCw, CheckCircle, XCircle, Zap, Shield, Wrench, TrendingUp, AlertTriangle, Package } from 'lucide-react'
import { fetchEvolutionStats } from '@/lib/api'
import type { EvolutionStats, EvolutionSignal } from '@/types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'

// ---- 策略元数据 ----
const STRATEGY_META: Record<string, {
  label: string
  desc: string
  icon: React.ReactNode
  variant: 'success' | 'warning' | 'destructive' | 'secondary'
  color: string
}> = {
  innovate: {
    label: '探索创新',
    desc: '近期无阻断，LLM 被引导探索新能力',
    icon: <Zap className="h-4 w-4" />,
    variant: 'success',
    color: 'text-green-600',
  },
  balanced: {
    label: '均衡演化',
    desc: '阻断率低，稳步迭代提升质量',
    icon: <TrendingUp className="h-4 w-4" />,
    variant: 'secondary',
    color: 'text-blue-600',
  },
  harden: {
    label: '稳固优先',
    desc: '阻断率偏高，聚焦稳定性与合规',
    icon: <Shield className="h-4 w-4" />,
    variant: 'warning',
    color: 'text-amber-600',
  },
  'repair-only': {
    label: '紧急修复',
    desc: '高阻断率，集中修复失败检查项',
    icon: <Wrench className="h-4 w-4" />,
    variant: 'destructive',
    color: 'text-destructive',
  },
}

// ---- Tag 标签颜色 ----
const TAG_COLORS: Record<string, string> = {
  innovate: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  repair: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  harden: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
  'missing-context': 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  'no-icd': 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
  'citation-quality': 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  clean: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
}

function TagChip({ tag }: { tag: string }) {
  const cls = TAG_COLORS[tag] ?? 'bg-muted text-muted-foreground'
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {tag}
    </span>
  )
}

// ---- 信号时间轴气泡 ----
function SignalDot({ signal }: { signal: EvolutionSignal }) {
  const isBlocked = signal.outcome === 'blocked'
  return (
    <div className="group relative flex flex-col items-center gap-0.5">
      <div
        className={`h-3 w-3 rounded-full border-2 transition-transform group-hover:scale-150 cursor-default ${
          isBlocked
            ? 'border-destructive bg-destructive/60'
            : 'border-green-500 bg-green-500/60'
        }`}
      />
      {/* Tooltip */}
      <div className="absolute bottom-5 left-1/2 -translate-x-1/2 z-10 hidden group-hover:block
                      w-56 rounded-md border bg-popover p-2 text-xs shadow-lg">
        <p className="font-medium truncate">{signal.subject || signal.draft_id}</p>
        <p className={`mt-0.5 ${isBlocked ? 'text-destructive' : 'text-green-600'}`}>
          {isBlocked ? '阻断' : '通过'}
        </p>
        <div className="mt-1 flex flex-wrap gap-1">
          {signal.tags.map(t => <TagChip key={t} tag={t} />)}
        </div>
        <p className="mt-1 text-muted-foreground">
          节数 {signal.context_quality?.sections_used ?? '-'} ·
          ICD {signal.context_quality?.icd_params_used ?? '-'}
        </p>
        <p className="mt-0.5 text-muted-foreground text-[10px]">
          {signal.timestamp.replace('T', ' ').substring(0, 16)}
        </p>
      </div>
    </div>
  )
}

// ---- 百分比横条 ----
function BarRow({ label, count, total, color }: { label: string; count: number; total: number; color: string }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0
  return (
    <div className="flex items-center gap-3">
      <span className="w-36 truncate text-sm font-mono text-muted-foreground shrink-0">{label}</span>
      <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-right text-sm tabular-nums">{count}</span>
    </div>
  )
}

// ---- 信号详情行 ----
function SignalRow({ signal }: { signal: EvolutionSignal }) {
  const [expanded, setExpanded] = useState(false)
  const isBlocked = signal.outcome === 'blocked'

  return (
    <div
      className={`rounded-md border px-3 py-2 cursor-pointer hover:bg-muted/40 transition-colors ${
        isBlocked ? 'border-destructive/30' : 'border-green-500/30'
      }`}
      onClick={() => setExpanded(v => !v)}
    >
      <div className="flex items-center gap-2">
        {isBlocked
          ? <XCircle className="h-3.5 w-3.5 text-destructive shrink-0" />
          : <CheckCircle className="h-3.5 w-3.5 text-green-500 shrink-0" />}
        <span className="flex-1 text-sm font-medium truncate">{signal.subject || signal.draft_id}</span>
        <div className="flex gap-1 shrink-0">
          {signal.tags.map(t => <TagChip key={t} tag={t} />)}
        </div>
        <span className="text-xs text-muted-foreground shrink-0 ml-1">
          {signal.timestamp.replace('T', ' ').substring(0, 16)}
        </span>
      </div>
      {expanded && signal.failed_checks.length > 0 && (
        <ul className="mt-2 space-y-0.5 border-t pt-2">
          {signal.failed_checks.map((fc, i) => (
            <li key={i} className="text-xs text-muted-foreground flex gap-1">
              <AlertTriangle className="h-3 w-3 text-amber-500 mt-0.5 shrink-0" />
              <span>{fc}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

// ================================================================
// 主页面
// ================================================================

export default function Evolution() {
  const [stats, setStats] = useState<EvolutionStats | null>(null)
  const [loading, setLoading] = useState(true)

  function load() {
    setLoading(true)
    fetchEvolutionStats()
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  if (loading) {
    return (
      <div className="container mx-auto max-w-screen-xl px-4 py-16 text-center text-muted-foreground">
        加载中…
      </div>
    )
  }

  // 空状态：还没有任何信号
  if (!stats || stats.total_signals === 0) {
    return (
      <div className="container mx-auto max-w-screen-xl px-4 py-16">
        <div className="flex items-center gap-3 mb-6">
          <Dna className="h-6 w-6 text-primary" />
          <h1 className="text-2xl font-bold tracking-tight">GEP 自进化</h1>
        </div>
        <Card>
          <CardContent className="py-16 text-center space-y-4">
            <Dna className="mx-auto h-12 w-12 text-muted-foreground/30" />
            <p className="text-muted-foreground">
              还没有任何进化信号。
              <Link to="/draft" className="text-primary hover:underline ml-1">生成第一份草稿</Link>
              后，系统将自动开始积累本机演化记忆。
            </p>
            {stats && !stats.evolver_installed && (
              <div className="inline-flex items-center gap-2 rounded-md border border-amber-300 bg-amber-50 dark:bg-amber-900/20 px-3 py-2 text-sm text-amber-700 dark:text-amber-300">
                <Package className="h-4 w-4 shrink-0" />
                evolver 未安装——运行
                <code className="font-mono bg-amber-100 dark:bg-amber-900/40 px-1 rounded">
                  npm install -g @evomap/evolver
                </code>
                以启用 GEP 引导
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }

  const meta = STRATEGY_META[stats.current_strategy] ?? STRATEGY_META.balanced
  const tagTotal = Object.values(stats.tag_counts).reduce((a, b) => a + b, 0)
  const checkTotal = Object.values(stats.check_failure_counts).reduce((a, b) => a + b, 0)

  return (
    <div className="container mx-auto max-w-screen-xl px-4 py-6 space-y-6">
      {/* ---- 页头 ---- */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Dna className="h-6 w-6 text-primary" />
          <div>
            <h1 className="text-2xl font-bold tracking-tight">GEP 自进化</h1>
            <p className="text-sm text-muted-foreground">本机演化记忆 · 每次草稿生成后自动更新</p>
          </div>
        </div>
        <Button variant="outline" size="sm" className="gap-2" onClick={load}>
          <RefreshCw className="h-4 w-4" />刷新
        </Button>
      </div>

      {/* ---- 顶部统计卡 ---- */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {/* 当前策略 */}
        <Card className="sm:col-span-2">
          <CardHeader className="pb-2">
            <CardDescription>当前演化策略</CardDescription>
          </CardHeader>
          <CardContent className="space-y-1">
            <div className="flex items-center gap-2">
              <Badge variant={meta.variant} className="gap-1 text-sm px-3 py-1">
                {meta.icon}{meta.label}
              </Badge>
              {!stats.evolver_installed && (
                <Badge variant="secondary" className="gap-1 text-xs">
                  <Package className="h-3 w-3" />evolver 未安装
                </Badge>
              )}
            </div>
            <p className="text-xs text-muted-foreground">{meta.desc}</p>
          </CardContent>
        </Card>

        {/* 总信号数 */}
        <Card>
          <CardHeader className="pb-2 flex flex-row items-center justify-between">
            <CardDescription>总信号数</CardDescription>
            <Dna className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats.total_signals}</div>
            <p className="text-xs text-muted-foreground mt-1">累计生成记录</p>
          </CardContent>
        </Card>

        {/* 阻断率 */}
        <Card>
          <CardHeader className="pb-2 flex flex-row items-center justify-between">
            <CardDescription>近20次阻断率</CardDescription>
            <XCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-3xl font-bold ${
              stats.blocked_ratio >= 0.6 ? 'text-destructive'
              : stats.blocked_ratio >= 0.3 ? 'text-amber-500'
              : 'text-green-600'
            }`}>
              {Math.round(stats.blocked_ratio * 100)}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats.blocked_ratio === 0 ? '无阻断，可探索新能力' : '含阻断草稿'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* ---- 信号时间轴 ---- */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">近期信号时间轴</CardTitle>
          <CardDescription>最近 20 次草稿生成结果（从左到右为旧→新，悬停查看详情）</CardDescription>
        </CardHeader>
        <CardContent>
          {stats.recent.length === 0 ? (
            <p className="text-sm text-muted-foreground">暂无数据</p>
          ) : (
            <div className="flex items-end gap-1 py-4 px-2 overflow-x-auto">
              {[...stats.recent].reverse().map((s, i) => (
                <SignalDot key={s.draft_id ?? i} signal={s} />
              ))}
            </div>
          )}
          <div className="mt-2 flex items-center gap-4 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-green-500" />通过
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-destructive" />阻断
            </span>
          </div>
        </CardContent>
      </Card>

      {/* ---- 分布统计 ---- */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* 标签分布 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">基因标签分布</CardTitle>
            <CardDescription>evolver 根据标签选择对应 Gene 指导生成</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2.5">
            {Object.entries(stats.tag_counts).length === 0 ? (
              <p className="text-sm text-muted-foreground">暂无数据</p>
            ) : (
              Object.entries(stats.tag_counts).map(([tag, cnt]) => (
                <BarRow
                  key={tag}
                  label={tag}
                  count={cnt}
                  total={tagTotal}
                  color={
                    tag === 'innovate' ? 'bg-green-500'
                    : tag === 'repair' ? 'bg-destructive'
                    : tag === 'harden' ? 'bg-amber-500'
                    : 'bg-primary/60'
                  }
                />
              ))
            )}
          </CardContent>
        </Card>

        {/* 失败检查器 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">高频失败检查器</CardTitle>
            <CardDescription>累计触发 Warning / Blocker 最多的评估项</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2.5">
            {Object.entries(stats.check_failure_counts).length === 0 ? (
              <p className="text-sm text-muted-foreground">暂无失败记录</p>
            ) : (
              Object.entries(stats.check_failure_counts).map(([check, cnt]) => (
                <BarRow
                  key={check}
                  label={check}
                  count={cnt}
                  total={checkTotal}
                  color="bg-amber-500"
                />
              ))
            )}
          </CardContent>
        </Card>
      </div>

      <Separator />

      {/* ---- 近期信号详情列表 ---- */}
      <div>
        <h2 className="text-base font-semibold mb-3">近期信号详情</h2>
        <div className="space-y-1.5">
          {stats.recent.map((s, i) => (
            <SignalRow key={s.draft_id ?? i} signal={s} />
          ))}
        </div>
      </div>
    </div>
  )
}
