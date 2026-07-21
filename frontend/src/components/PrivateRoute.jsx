import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { RouteFallback } from './shell/RouteFallback'

export default function PrivateRoute() {
  const { user, loading } = useAuth()

  if (loading === true) return <RouteFallback />
  if (!user) return <Navigate to="/login" replace />
  return <Outlet />
}
