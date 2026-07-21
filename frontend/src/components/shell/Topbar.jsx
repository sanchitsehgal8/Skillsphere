import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bell, LogOut, Menu, Search, Settings, User } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { useProfile } from '../../lib/useProfile'
import { ThemeToggle } from '../brand/ThemeToggle'
import { Avatar, StatusDot } from '../ui/misc'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown'

export function Topbar({ onOpenNav }) {
  const navigate = useNavigate()
  const { signOut } = useAuth()
  const profile = useProfile()
  const [query, setQuery] = useState('')

  function submitSearch(e) {
    e.preventDefault()
    const q = query.trim()
    navigate(q ? `/candidates?query=${encodeURIComponent(q)}` : '/candidates')
  }

  async function handleLogout() {
    await signOut()
    navigate('/login')
  }

  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/80 backdrop-blur-xl">
      <div className="flex h-16 items-center gap-3 px-4 sm:px-6 lg:px-8">
        <button
          type="button"
          onClick={onOpenNav}
          className="grid h-9 w-9 place-items-center rounded-lg border border-border text-foreground/80 lg:hidden"
          aria-label="Open navigation"
        >
          <Menu className="h-5 w-5" />
        </button>

        <form onSubmit={submitSearch} className="relative flex-1 max-w-md">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search candidates, skills, roles…"
            className="h-10 w-full rounded-xl border border-input bg-surface/60 pl-9 pr-4 text-sm text-foreground placeholder:text-muted-foreground/70 transition-colors focus:border-primary/50 focus:bg-surface focus:outline-none focus:ring-4 focus:ring-primary/15"
          />
        </form>

        <div className="ml-auto flex items-center gap-2">
          <span className="hidden items-center gap-2 rounded-full border border-success/25 bg-success/10 px-3 py-1.5 text-xs font-medium text-success sm:inline-flex">
            <StatusDot tone="success" />
            System live
          </span>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                className="relative grid h-9 w-9 place-items-center rounded-lg border border-border bg-surface/60 text-foreground/80 transition-colors hover:bg-secondary/70 hover:text-foreground"
                aria-label="Notifications"
              >
                <Bell className="h-4 w-4" />
                <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-accent" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-72">
              <DropdownMenuLabel>Notifications</DropdownMenuLabel>
              <div className="px-3 py-6 text-center text-xs text-muted-foreground">You&apos;re all caught up.</div>
            </DropdownMenuContent>
          </DropdownMenu>

          <ThemeToggle />

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="flex items-center gap-2.5 rounded-xl border border-border bg-surface/60 py-1 pl-1 pr-2.5 transition-colors hover:bg-secondary/70">
                <Avatar name={profile.fullName} size="sm" />
                <span className="hidden text-left sm:block">
                  <span className="block text-xs font-semibold leading-tight text-foreground">{profile.fullName}</span>
                  <span className="block text-2xs leading-tight text-muted-foreground">{profile.role}</span>
                </span>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuLabel>{profile.email}</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => navigate('/profile')}>
                <User className="h-4 w-4" /> Profile
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate('/settings')}>
                <Settings className="h-4 w-4" /> Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout} className="text-danger focus:bg-danger/10 focus:text-danger">
                <LogOut className="h-4 w-4" /> Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}
