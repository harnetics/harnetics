/**
 * [INPUT]: 依赖 react、button 基元
 * [OUTPUT]: 对外提供 ConfirmDialog 应用内确认弹窗组件
 * [POS]: components/ui 的确认交互基元，替代 window.confirm 以兼容桌面 WebView
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */

import { Button } from '@/components/ui/button'

interface ConfirmDialogProps {
  open: boolean
  title: string
  description: string
  confirmLabel?: string
  cancelLabel?: string
  busy?: boolean
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = '确认',
  cancelLabel = '取消',
  busy = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 px-4">
      <div className="w-full max-w-md rounded-lg border bg-card p-5 shadow-lg">
        <h2 className="text-base font-semibold text-foreground">{title}</h2>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">{description}</p>
        <div className="mt-5 flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onCancel} disabled={busy}>
            {cancelLabel}
          </Button>
          <Button type="button" variant="destructive" onClick={onConfirm} disabled={busy}>
            {busy ? '处理中...' : confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}
