import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, BookOpen, FileEdit, GitMerge, Share2, Palette } from 'lucide-react'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '/', label: '仪表盘', icon: LayoutDashboard },
  { to: '/documents', label: '文档库', icon: BookOpen },
  { to: '/draft', label: '草稿台', icon: FileEdit },
  { to: '/impact', label: '变更影响', icon: GitMerge },
  { to: '/graph', label: '图谱', icon: Share2 },
]

export default function Header() {
  const { pathname } = useLocation()
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur">
      <div className="container mx-auto flex h-14 max-w-screen-xl items-center gap-6 px-4">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 font-bold text-primary shrink-0">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="2" />
            <circle cx="10" cy="10" r="3" fill="currentColor" />
            <line x1="10" y1="1" x2="10" y2="5" stroke="currentColor" strokeWidth="2" />
            <line x1="10" y1="15" x2="10" y2="19" stroke="currentColor" strokeWidth="2" />
            <line x1="1" y1="10" x2="5" y2="10" stroke="currentColor" strokeWidth="2" />
            <line x1="15" y1="10" x2="19" y2="10" stroke="currentColor" strokeWidth="2" />
          </svg>
          Harnetics
        </Link>

        {/* Nav */}
        <nav className="flex items-center gap-1 flex-1">
          {navItems.map(({ to, label, icon: Icon }) => {
            const active = to === '/' ? pathname === '/' : pathname.startsWith(to)
            return (
              <Link
                key={to}
                to={to}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                  active
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                )}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            )
          })}
        </nav>
      </div>
    </header>
  )
}
