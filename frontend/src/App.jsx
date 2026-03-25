import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'
import Sidebar from './components/Sidebar'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import CandidatesPage from './pages/CandidatesPage'
import AnalyzePage from './pages/AnalyzePage'
import SettingsPage from './pages/SettingsPage'
import ProfilePage from './pages/ProfilePage'

function AppLayout({ analyses, setAnalyses, theme, onToggleTheme }) {
  const analysesByCandidate = useMemo(() => {
    const map = {}
    analyses.forEach((a) => {
      const prev = map[a.candidateId]
      if (!prev || prev.score < a.score) {
        map[a.candidateId] = a
      }
    })
    return map
  }, [analyses])

  function onNewAnalyses(items) {
    setAnalyses((prev) => [...items, ...prev])
  }

  return (
    <div className="app-shell">
      <Sidebar onLogout={() => setAnalyses([])} />
      <main className="main">
        <Routes>
          <Route
            path="/dashboard"
            element={<DashboardPage analyses={analyses} theme={theme} onToggleTheme={onToggleTheme} />}
          />
          <Route
            path="/candidates"
            element={<CandidatesPage analysesByCandidate={analysesByCandidate} theme={theme} onToggleTheme={onToggleTheme} />}
          />
          <Route
            path="/analyze"
            element={<AnalyzePage onNewAnalyses={onNewAnalyses} theme={theme} onToggleTheme={onToggleTheme} />}
          />
          <Route
            path="/settings"
            element={<SettingsPage theme={theme} onToggleTheme={onToggleTheme} />}
          />
          <Route
            path="/profile"
            element={<ProfilePage theme={theme} onToggleTheme={onToggleTheme} />}
          />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  const [analyses, setAnalyses] = useState([])
  const [theme, setTheme] = useState('dark')
  const location = useLocation()

  useEffect(() => {
    const saved = localStorage.getItem('skillsphere-theme')
    if (saved === 'light' || saved === 'dark') {
      setTheme(saved)
      return
    }
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
    setTheme(prefersDark ? 'dark' : 'light')
  }, [])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('skillsphere-theme', theme)
  }, [theme])

  function toggleTheme() {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }

  if (location.pathname === '/') {
    return <LoginPage theme={theme} onToggleTheme={toggleTheme} />
  }

  return (
    <AppLayout
      analyses={analyses}
      setAnalyses={setAnalyses}
      theme={theme}
      onToggleTheme={toggleTheme}
    />
  )
}
