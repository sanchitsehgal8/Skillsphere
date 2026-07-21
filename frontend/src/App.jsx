import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import PrivateRoute from './components/PrivateRoute'
import AppShell from './components/shell/AppShell'
import { RouteFallback } from './components/shell/RouteFallback'

const LandingPage = lazy(() => import('./pages/LandingPage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const AuthCallback = lazy(() => import('./pages/AuthCallback'))
const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const CandidatesPage = lazy(() => import('./pages/CandidatesPage'))
const AnalyzePage = lazy(() => import('./pages/AnalyzePage'))
const AnalysisResultsPage = lazy(() => import('./pages/AnalysisResultsPage'))
const CopilotPage = lazy(() => import('./pages/CopilotPage'))
const SettingsPage = lazy(() => import('./pages/SettingsPage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))

export default function App() {
  const location = useLocation()

  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes location={location}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/auth/callback" element={<AuthCallback />} />

        <Route element={<PrivateRoute />}>
          <Route element={<AppShell />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/candidates" element={<CandidatesPage />} />
            <Route path="/analyze" element={<AnalyzePage />} />
            <Route path="/analyze/results" element={<AnalysisResultsPage />} />
            <Route path="/copilot" element={<CopilotPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/profile" element={<ProfilePage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}
