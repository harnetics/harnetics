/**
 * [INPUT]: 依赖 @/lib/api 的 fetchSettings/updateSettings
 * [OUTPUT]: 对外提供 Settings 页面组件
 * [POS]: pages 的运行时配置页，允许用户查看和修改 LLM/Embedding 参数
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */

import { useState, useEffect } from 'react'
import { fetchSettings, updateSettings, type SettingsData } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Save } from 'lucide-react'

const EMPTY: SettingsData = {
  llm_model: '',
  llm_base_url: '',
  llm_api_key: '',
  embedding_model: '',
  embedding_base_url: '',
  embedding_api_key: '',
}

interface FieldDef {
  key: keyof SettingsData
  label: string
  placeholder: string
  sensitive?: boolean
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

export default function Settings() {
  const [data, setData] = useState<SettingsData>(EMPTY)
  const [form, setForm] = useState<SettingsData>(EMPTY)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    fetchSettings()
      .then((s) => { setData(s); setForm(s) })
      .catch((e) => setError(e instanceof Error ? e.message : '加载失败'))
  }, [])

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
      {fields.map(({ key, label, placeholder, sensitive }) => (
        <div key={key} className="grid grid-cols-[140px_1fr] items-center gap-3">
          <label className="text-sm font-medium text-right">{label}</label>
          <Input
            type={sensitive ? 'password' : 'text'}
            autoComplete="off"
            placeholder={placeholder}
            value={form[key]}
            onChange={(e) => setForm((prev) => ({ ...prev, [key]: e.target.value }))}
          />
        </div>
      ))}
    </div>
  )

  return (
    <div className="container mx-auto max-w-screen-md px-4 py-8 space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">设置</h1>
        <Button className="gap-2" onClick={handleSave} disabled={saving}>
          <Save className="h-4 w-4" />
          {saving ? '保存中…' : '保存'}
        </Button>
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
      {message && <p className="text-sm text-muted-foreground">{message}</p>}

      <div className="rounded-xl border bg-card p-6 space-y-6">
        {renderFields('LLM 配置', LLM_FIELDS)}
      </div>
      <div className="rounded-xl border bg-card p-6 space-y-6">
        {renderFields('Embedding 配置', EMBEDDING_FIELDS)}
      </div>
    </div>
  )
}
