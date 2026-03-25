import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function TopBar({ title, subtitle, onExport, theme, onToggleTheme }) {
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')

  function showNotifications() {
    window.alert('No new notifications right now.')
  }

  function submitSearch(e) {
    e.preventDefault()
    const q = searchQuery.trim()
    if (!q) {
      navigate('/candidates')
      return
    }
    navigate(`/candidates?query=${encodeURIComponent(q)}`)
  }

  return (
    <>
      <header className="topbar-shell">
        <form className="top-search" onSubmit={submitSearch}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
          <input
            className="search"
            placeholder="Search candidate insights..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </form>

        <div className="topbar-actions">
          <span className="status-pill">
            <span className="status-dot" />
            System live
          </span>
          <button className="notif-btn" aria-label="Notifications" onClick={showNotifications}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 01-3.46 0" />
            </svg>
          </button>
          <button
            className={`theme-toggle ${theme === 'dark' ? 'is-dark' : 'is-light'}`}
            onClick={onToggleTheme}
            title="Toggle dark/light mode"
            aria-label="Toggle dark/light mode"
          >
            <span className="theme-knob">{theme === 'dark' ? '☾' : '☼'}</span>
          </button>
          {onExport && (
            <button className="primary-btn compact" onClick={onExport}>Export Report</button>
          )}
          <button type="button" className="header-user profile-trigger" onClick={() => navigate('/profile')}>
            <div>
              <div className="name">Alex Rivers</div>
              <div className="role">Recruitment Lead</div>
            </div>
            <div className="header-avatar">AR</div>
          </button>
        </div>
      </header>

      <div className="page-header">
        <div>
          <p className="page-eyebrow">Precision Analytics</p>
          <h2 className="page-title">{title}</h2>
          {subtitle && <p className="page-subtitle">{subtitle}</p>}
        </div>
      </div>
    </>
  )
}
