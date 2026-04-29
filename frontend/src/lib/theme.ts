/**
 * [INPUT]: 无外部依赖，仅消费 window.localStorage 和 window.matchMedia
 * [OUTPUT]: 导出 Theme 类型、THEME_KEY 常量、getInitialTheme / applyTheme / persistTheme 工具函数
 * [POS]: lib 的主题初始化层，被 ThemeContext 消费，与 index.html 内联脚本逻辑保持一致
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */

export type Theme = 'dark' | 'light'

export const THEME_KEY = 'harnetics-theme'

// ----------------------------------------------------------------
// 解析初始主题：localStorage → matchMedia → 默认浅色
// ----------------------------------------------------------------

export function getInitialTheme(): Theme {
  try {
    const stored = localStorage.getItem(THEME_KEY)
    if (stored === 'dark' || stored === 'light') return stored
  } catch {
    // localStorage 被禁用（隐私模式）时静默降级
  }
  if (typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark'
  }
  return 'light'
}

// ----------------------------------------------------------------
// 应用主题：增减 <html> 上的 .dark 类
// ----------------------------------------------------------------

export function applyTheme(theme: Theme): void {
  const root = document.documentElement
  if (theme === 'dark') {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }
}

// ----------------------------------------------------------------
// 持久化主题选择到 localStorage
// ----------------------------------------------------------------

export function persistTheme(theme: Theme): void {
  try {
    localStorage.setItem(THEME_KEY, theme)
  } catch {
    // 静默处理
  }
}
