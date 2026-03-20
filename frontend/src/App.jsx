import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { useMemo, useState } from 'react'
import Sidebar from './components/Sidebar'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import CandidatesPage from './pages/CandidatesPage'
import AnalyzePage from './pages/AnalyzePage'

function AppLayout({ analyses, setAnalyses }) {
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
      <Sidebar />
      <main className="main">
        <Routes>
          <Route path="/dashboard" element={<DashboardPage analyses={analyses} />} />
          <Route path="/candidates" element={<CandidatesPage analysesByCandidate={analysesByCandidate} />} />
          <Route path="/analyze" element={<AnalyzePage onNewAnalyses={onNewAnalyses} />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  const [analyses, setAnalyses] = useState([])
  const location = useLocation()

  if (location.pathname === '/') {
    return <LoginPage />
  }

  return <AppLayout analyses={analyses} setAnalyses={setAnalyses} />
}
