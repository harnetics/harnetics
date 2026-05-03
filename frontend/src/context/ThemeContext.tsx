/**
 * [INPUT]: 依赖 @/lib/theme 的 getInitialTheme / applyTheme / persistTheme / Theme
 * [OUTPUT]: 导出 ThemeProvider 组件、useTheme hook、Theme 类型
 * [POS]: context 的主题状态根，包裹 App 根节点；所有子组件通过 useTheme() 消费主题
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { getInitialTheme, applyTheme, persistTheme, THEME_KEY, type Theme } from '@/lib/theme'

// ----------------------------------------------------------------
// Context 类型
// ----------------------------------------------------------------

interface ThemeContextValue {
  theme: Theme
  toggleTheme: () => void
  setTheme: (theme: Theme) => void
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

// ----------------------------------------------------------------
// Provider
// ----------------------------------------------------------------

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(getInitialTheme)

  // 主题变化时同步到 DOM 和 localStorage
  useEffect(() => {
    applyTheme(theme)
    persistTheme(theme)
  }, [theme])

  // 跟随系统偏好（仅当用户未手动覆盖时）
  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = (e: MediaQueryListEvent) => {
      try {
        if (!localStorage.getItem(THEME_KEY)) {
          setThemeState(e.matches ? 'dark' : 'light')
        }
      } catch {
        setThemeState(e.matches ? 'dark' : 'light')
      }
    }
    mq.addEventListener('change', handleChange)
    return () => mq.removeEventListener('change', handleChange)
  }, [])

  const toggleTheme = () => setThemeState((prev) => (prev === 'dark' ? 'light' : 'dark'))
  const setTheme = (t: Theme) => setThemeState(t)

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

// ----------------------------------------------------------------
// Hook
// ----------------------------------------------------------------

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}

export type { Theme }
