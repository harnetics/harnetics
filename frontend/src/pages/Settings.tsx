/**
 * [INPUT]: 依赖 @/lib/api 的 fetchSettings/updateSettings/fetchDeveloperLogs
 * [OUTPUT]: 对外提供 Settings 页面组件，含 LLM thinking 开关、四步比对高级推理边界配置与开发者模式实时日志窗口
 * [POS]: pages 的运行时配置与调试页，允许用户查看/修改 LLM/Embedding 参数、thinking 请求开关、比对推理边界并观察后端日志
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */

import { useState, useEffect } from 'react'
import { fetchDeveloperLogs, fetchSettings, updateSettings, type SettingsData } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { DeveloperLogs } from '@/types'
import { Bug, Save, ScrollText } from 'lucide-react'

const EMPTY: SettingsData = {
  llm_model: '',
  llm_base_url: '',
  llm_api_key: '',
  llm_thinking_supported: 'false',
  llm_enable_thinking: 'false',
  embedding_model: '',
  embedding_base_url: '',
  embedding_api_key: '',
  llm_max_tokens: '',
  llm_timeout_seconds: '',
  comparison_4step_batch_size: '',
  comparison_step1_max_tokens: '',
  comparison_step3_max_tokens: '',
  comparison_step4_max_tokens: '',
}

interface FieldDef {
  key: keyof SettingsData
  label: string
  placeholder: string
  sensitive?: boolean
  numeric?: boolean
}

const LLM_FIELDS: FieldDef[] = [
  { key: 'llm_model', label: '模型', placeholder: 'gpt-4o-mini / ollama/qwen3:8b' },
  { key: 'llm_base_url', label: 'Base URL', placeholder: 'https://api.openai.com/v1（留空使用默认）' },
  { key: 'llm_api_key', label: 'API Key', placeholder: 'sk-...', sensitive: true },
]

const EMBEDDING_FIELDS: FieldDef[] = [
  { key: 'embedding_model', label: '模型', placeholder: 'text-embedding-3-small' },
  { key: 'embedding_base_url', label: 'Base URL', placeholder: 'https://api.openai.com/v1（留空使用默认）' },
  { key: 'embedding_api_key', label: 'API Key', placeholder: 'sk-...', sensitive: true },
]

const ADVANCED_FIELDS: FieldDef[] = [
  { key: 'llm_timeout_seconds', label: '请求超时秒数', placeholder: '180', numeric: true },
  { key: 'llm_max_tokens', label: '通用输出上限', placeholder: '16384', numeric: true },
  { key: 'comparison_step1_max_tokens', label: 'Step1 输出上限', placeholder: '500000', numeric: true },
  { key: 'comparison_4step_batch_size', label: 'Step3 批大小', placeholder: '10', numeric: true },
  { key: 'comparison_step3_max_tokens', label: 'Step3 输出上限', placeholder: '16384', numeric: true },
  { key: 'comparison_step4_max_tokens', label: 'Step4 输出上限', placeholder: '500000', numeric: true },
]

export default function Settings() {
  const [data, setData] = useState<SettingsData>(EMPTY)
  const [form, setForm] = useState<SettingsData>(EMPTY)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [developerMode, setDeveloperMode] = useState(false)
  const [logs, setLogs] = useState<DeveloperLogs>({ path: '', lines: [] })
  const [logError, setLogError] = useState('')
  const thinkingSupported = form.llm_thinking_supported === 'true'

  useEffect(() => {
    fetchSettings()
      .then((s) => { setData(s); setForm(s) })
      .catch((e) => setError(e instanceof Error ? e.message : '加载失败'))
  }, [])

  useEffect(() => {
    if (!developerMode) return

    let active = true
    const loadLogs = () => {
      fetchDeveloperLogs()
        .then((next) => {
          if (!active) return
          setLogs(next)
          setLogError('')
        })
        .catch((e) => {
          if (!active) return
          setLogError(e instanceof Error ? e.message : '日志加载失败')
        })
    }

    loadLogs()
    const timer = window.setInterval(loadLogs, 1000)
    return () => {
      active = false
      window.clearInterval(timer)
    }
  }, [developerMode])

  const handleSave = async () => {
    setSaving(true)
    setMessage('')
    setError('')
    const changes: Record<string, string> = {}
    for (const k of Object.keys(form) as (keyof SettingsData)[]) {
      if (form[k] !== data[k]) changes[k] = form[k]
    }
    if (!Object.keys(changes).length) {
      setMessage('无变更')
      setSaving(false)
      return
    }
    try {
      const updated = await updateSettings(changes)
      setData(updated)
      setForm(updated)
      setMessage('已保存')
    } catch (e) {
      setError(e instanceof Error ? e.message : '保存失败')
    } finally {
      setSaving(false)
    }
  }

  const renderFields = (title: string, fields: FieldDef[]) => (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">{title}</h2>
      {fields.map(({ key, label, placeholder, sensitive, numeric }) => (
        <div key={key} className="grid grid-cols-[140px_1fr] items-center gap-3">
          <label className="text-sm font-medium text-right">{label}</label>
          <Input
            type={sensitive ? 'password' : numeric ? 'number' : 'text'}
            min={numeric ? 1 : undefined}
            step={numeric && key === 'llm_timeout_seconds' ? '0.1' : numeric ? '1' : undefined}
            autoComplete="off"
            placeholder={placeholder}
            value={form[key]}
            onChange={(e) => setForm((prev) => ({ ...prev, [key]: e.target.value }))}
          />
        </div>
      ))}
    </div>
  )

  const setBooleanField = (key: keyof SettingsData, checked: boolean) => {
    setForm((prev) => ({ ...prev, [key]: checked ? 'true' : 'false' }))
  }

  const renderThinkingControls = () => (
    <div className="space-y-3 border-t pt-4">
      <label className="flex items-center gap-3 text-sm">
        <input
          type="checkbox"
          className="h-4 w-4 rounded border-border"
          checked={thinkingSupported}
          onChange={(e) => {
            const checked = e.target.checked
            setForm((prev) => ({
              ...prev,
              llm_thinking_supported: checked ? 'true' : 'false',
              llm_enable_thinking: checked ? prev.llm_enable_thinking : 'false',
            }))
          }}
        />
        <span className="font-medium">模型支持 thinking 参数</span>
      </label>
      <label className={`flex items-center gap-3 text-sm ${thinkingSupported ? '' : 'text-muted-foreground'}`}>
        <input
          type="checkbox"
          className="h-4 w-4 rounded border-border"
          checked={form.llm_enable_thinking === 'true'}
          disabled={!thinkingSupported}
          onChange={(e) => setBooleanField('llm_enable_thinking', e.target.checked)}
        />
        <span className="font-medium">请求时发送 enable_thinking</span>
      </label>
    </div>
  )

  return (
    <div className="container mx-auto max-w-screen-xl px-4 py-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">设置</h1>
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant={developerMode ? 'default' : 'outline'}
            className="gap-2"
            onClick={() => setDeveloperMode((v) => !v)}
          >
            <Bug className="h-4 w-4" />
            开发者模式
          </Button>
          <Button className="gap-2" onClick={handleSave} disabled={saving}>
            <Save className="h-4 w-4" />
            {saving ? '保存中…' : '保存'}
          </Button>
        </div>
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
      {message && <p className="text-sm text-muted-foreground">{message}</p>}

      <div className={`mt-8 grid gap-6 ${developerMode ? 'lg:grid-cols-[minmax(0,1fr)_430px]' : 'max-w-screen-md'}`}>
        <div className="space-y-6">
          <div className="rounded-xl border bg-card p-6 space-y-6">
            {renderFields('LLM 配置', LLM_FIELDS)}
            {renderThinkingControls()}
          </div>
          <div className="rounded-xl border bg-card p-6 space-y-6">
            {renderFields('Embedding 配置', EMBEDDING_FIELDS)}
          </div>
          <div className="rounded-xl border bg-card p-6 space-y-6">
            {renderFields('高级 / 开发者配置', ADVANCED_FIELDS)}
          </div>
        </div>

        {developerMode && (
          <aside className="rounded-xl border bg-card p-0 lg:sticky lg:top-20 lg:h-[calc(100vh-7rem)]">
            <div className="flex items-center justify-between gap-3 border-b px-4 py-3">
              <div className="flex min-w-0 items-center gap-2">
                <ScrollText className="h-4 w-4 shrink-0 text-primary" />
                <div className="min-w-0">
                  <h2 className="text-sm font-semibold">后端日志</h2>
                  <p className="truncate text-xs text-muted-foreground">
                    {logs.path || '等待日志文件'}
                  </p>
                </div>
              </div>
              <span className="shrink-0 rounded-full bg-green-500/15 px-2 py-0.5 text-xs font-medium text-green-700 dark:text-green-300">
                实时
              </span>
            </div>
            <div className="h-[520px] overflow-auto bg-muted/30 p-3 lg:h-[calc(100%-58px)]">
              {logError ? (
                <p className="text-sm text-destructive">{logError}</p>
              ) : logs.lines.length ? (
                <pre className="whitespace-pre-wrap break-words font-mono text-xs leading-5 text-foreground">
                  {logs.lines.join('\n')}
                </pre>
              ) : (
                <p className="text-sm text-muted-foreground">暂无日志输出</p>
              )}
            </div>
          </aside>
        )}
      </div>
    </div>
  )
}
