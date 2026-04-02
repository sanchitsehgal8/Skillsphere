import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import NavItem from './NavItem'

const items = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/candidates', label: 'Candidates' },
  { to: '/analyze', label: 'Analyze' },
  { to: '/profile', label: 'Profile' },
  { to: '/settings', label: 'Settings' },
]

export default function MobileTopNav({ onLogout }) {
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef(null)
  const toggleRef = useRef(null)

  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape') setMenuOpen(false)
    }

    function handleOutside(e) {
      if (!menuOpen) return
      const target = e.target
      if (menuRef.current?.contains(target) || toggleRef.current?.contains(target)) return
      setMenuOpen(false)
    }

    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('mousedown', handleOutside)
    window.addEventListener('touchstart', handleOutside)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('mousedown', handleOutside)
      window.removeEventListener('touchstart', handleOutside)
    }
  }, [menuOpen])

  return (
    <header className="ss-mobile-topnav" role="banner">
      <div className="ss-mobile-topnav-row">
        <button
          ref={toggleRef}
          type="button"
          className="ss-mobile-icon-btn"
          onClick={() => setMenuOpen((prev) => !prev)}
          aria-label="Toggle menu"
          aria-expanded={menuOpen}
        >
          {menuOpen ? '✕' : '☰'}
        </button>

        <button
          type="button"
          className="ss-mobile-brand"
          onClick={() => navigate('/dashboard')}
          aria-label="Go to dashboard"
        >
          SkillSphere
        </button>

        <button
          type="button"
          className="ss-mobile-icon-btn"
          onClick={() => navigate('/settings')}
          aria-label="Open settings"
        >
          ⚙
        </button>
      </div>

      <div
        ref={menuRef}
        className={`ss-mobile-menu ${menuOpen ? 'open' : ''}`}
      >
        {items.map((item) => (
          <NavItem
            key={item.to}
            to={item.to}
            label={item.label}
            className="ss-mobile-menu-item"
            onClick={() => setMenuOpen(false)}
          />
        ))}
        <NavItem
          asButton
          label="Logout"
          className="ss-mobile-menu-item"
          onClick={async () => {
            setMenuOpen(false)
            await onLogout()
          }}
        />
      </div>
    </header>
  )
}
