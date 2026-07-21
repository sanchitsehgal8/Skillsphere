import { NavLink, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { BarChart3, Bot, LayoutDashboard, LogOut, Settings, Sparkles, User, Users } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { Logo } from '../brand/Logo'
import { cn } from '../../lib/utils'

const nav = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/candidates', label: 'Candidates', icon: Users },
  { to: '/analyze', label: 'Analyze', icon: BarChart3, badge: 'AI' },
  { to: '/copilot', label: 'Copilot', icon: Bot },
  { to: '/profile', label: 'Profile', icon: User },
]

function NavRow({ to, label, icon: Icon, badge, onNavigate }) {
  return (
    <NavLink
      to={to}
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(
          'group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors',
          isActive ? 'text-foreground' : 'text-muted-foreground hover:text-foreground',
        )
      }
    >
      {({ isActive }) => (
        <>
          {isActive && (
            <motion.span
              layoutId="nav-active"
              className="absolute inset-0 -z-10 rounded-xl border border-border bg-secondary/70"
              transition={{ type: 'spring', stiffness: 400, damping: 32 }}
            />
          )}
          <Icon className={cn('h-[1.15rem] w-[1.15rem] transition-colors', isActive && 'text-primary')} />
          <span className="flex-1">{label}</span>
          {badge && (
            <span className="rounded-md bg-primary/15 px-1.5 py-0.5 text-2xs font-semibold text-primary">{badge}</span>
          )}
        </>
      )}
    </NavLink>
  )
}

export function SidebarContent({ onNavigate }) {
  const navigate = useNavigate()
  const { signOut } = useAuth()

  async function handleLogout() {
    await signOut()
    navigate('/login')
  }

  return (
    <div className="flex h-full flex-col">
      <div className="px-3 pb-6 pt-1">
        <NavLink to="/dashboard" onClick={onNavigate}>
          <Logo />
        </NavLink>
      </div>

      <div className="px-1">
        <p className="px-3 pb-2 text-2xs font-semibold uppercase tracking-widest text-muted-foreground/70">Workspace</p>
        <nav className="flex flex-col gap-1">
          {nav.map((item) => (
            <NavRow key={item.to} {...item} onNavigate={onNavigate} />
          ))}
        </nav>
      </div>

      <div className="mt-6 px-1">
        <p className="px-3 pb-2 text-2xs font-semibold uppercase tracking-widest text-muted-foreground/70">System</p>
        <nav className="flex flex-col gap-1">
          <NavRow to="/settings" label="Settings" icon={Settings} onNavigate={onNavigate} />
        </nav>
      </div>

      <div className="mt-auto px-1 pt-6">
        <div className="ring-gradient relative overflow-hidden rounded-2xl border border-border bg-secondary/40 p-4">
          <div className="mb-2 flex items-center gap-2 text-primary">
            <Sparkles className="h-4 w-4" />
            <span className="text-xs font-semibold">Evidence engine</span>
          </div>
          <p className="text-xs leading-relaxed text-muted-foreground">
            Every score traces back to real GitHub, resume &amp; Codeforces signals.
          </p>
        </div>
        <button
          type="button"
          onClick={handleLogout}
          className="mt-2 flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-danger/10 hover:text-danger"
        >
          <LogOut className="h-[1.15rem] w-[1.15rem]" />
          Sign out
        </button>
      </div>
    </div>
  )
}

export default function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-[264px] border-r border-border bg-surface/50 backdrop-blur-xl lg:block">
      <div className="h-full overflow-y-auto p-4">
        <SidebarContent />
      </div>
    </aside>
  )
}
