import { useState } from 'react'
import TopBar from '../components/TopBar'

export default function SettingsPage({ theme, onToggleTheme }) {
  const [emailAlerts, setEmailAlerts] = useState(true)
  const [weeklyDigest, setWeeklyDigest] = useState(true)
  const [autoExport, setAutoExport] = useState(false)

  function saveSettings() {
    localStorage.setItem(
      'skillsphere-settings',
      JSON.stringify({ emailAlerts, weeklyDigest, autoExport }),
    )
    window.alert('Settings saved successfully.')
  }

  function resetSettings() {
    setEmailAlerts(true)
    setWeeklyDigest(true)
    setAutoExport(false)
  }

  return (
    <div className="page">
      <TopBar
        title="Settings"
        subtitle="Control workspace preferences and notifications"
        theme={theme}
        onToggleTheme={onToggleTheme}
      />

      <section className="card filter-panel">
        <div className="filter-head">
          <h3>Workspace Preferences</h3>
          <span className="badge-soft">Account</span>
        </div>

        <div className="settings-grid">
          <label className="check-inline">
            <input
              type="checkbox"
              checked={emailAlerts}
              onChange={(e) => setEmailAlerts(e.target.checked)}
            />
            Email alerts for candidate updates
          </label>

          <label className="check-inline">
            <input
              type="checkbox"
              checked={weeklyDigest}
              onChange={(e) => setWeeklyDigest(e.target.checked)}
            />
            Weekly pipeline digest
          </label>

          <label className="check-inline">
            <input
              type="checkbox"
              checked={autoExport}
              onChange={(e) => setAutoExport(e.target.checked)}
            />
            Auto-export weekly report
          </label>
        </div>

        <div className="settings-actions">
          <button type="button" className="ghost-btn" onClick={resetSettings}>
            Reset
          </button>
          <button type="button" className="primary-btn" onClick={saveSettings}>
            Save Settings
          </button>
        </div>
      </section>
    </div>
  )
}
