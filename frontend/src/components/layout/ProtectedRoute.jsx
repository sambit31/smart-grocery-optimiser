import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import LoadingSpinner from '../common/LoadingSpinner'

/**
 * Guards the /app area:
 *  - not logged in        -> /login
 *  - no household yet     -> /app/household (every other page needs one)
 */
export default function ProtectedRoute() {
  const { user, household, loading } = useAuth()
  const location = useLocation()

  if (loading) return <LoadingSpinner fullPage label="Checking your session…" />
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (!household && location.pathname !== '/app/household') {
    return <Navigate to="/app/household" replace />
  }
  return <Outlet />
}
