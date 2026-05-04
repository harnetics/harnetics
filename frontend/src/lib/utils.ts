/**
 * [INPUT]: 依赖 clsx/tailwind-merge 与浏览器 Intl.DateTimeFormat
 * [OUTPUT]: 对外提供 cn、severityKey/severityLabel、formatBeijingTime 工具函数
 * [POS]: lib 的轻量通用工具模块，被页面与基础组件消费，集中处理 class 合并、等级文案与北京时间展示
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */

import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function severityKey(value: string | null | undefined) {
  return (value ?? '').trim().toLowerCase()
}

export function severityLabel(value: string | null | undefined) {
  const key = severityKey(value)
  if (!key) return 'Unknown'
  return `${key.slice(0, 1).toUpperCase()}${key.slice(1)}`
}

export function formatBeijingTime(value: string | null | undefined) {
  const raw = (value ?? '').trim()
  if (!raw) return ''
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(raw)) return raw

  const date = new Date(raw)
  if (Number.isNaN(date.getTime())) return raw.slice(0, 19).replace('T', ' ')

  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).formatToParts(date)
  const pick = (type: string) => parts.find((item) => item.type === type)?.value ?? ''
  return `${pick('year')}-${pick('month')}-${pick('day')} ${pick('hour')}:${pick('minute')}:${pick('second')}`
}
