import { CheckCircle2 } from 'lucide-react'
import { Navigate, Outlet } from 'react-router-dom'
import Brand from '../components/common/Brand'
import LoadingSpinner from '../components/common/LoadingSpinner'
import { useAuth } from '../context/AuthContext'

const POINTS = [
  'Predicts next month’s needs from your own usage',
  'Subtracts what is already in your kitchen',
  'Keeps essentials first when the budget is tight',
]

export default function AuthLayout() {
  const { user, loading } = useAuth()
  if (loading) return <LoadingSpinner fullPage />
  if (user) return <Navigate to="/app" replace />

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="hidden flex-col justify-between bg-brand-900 p-10 text-white lg:flex">
        <Brand light />
        <div>
          <h2 className="text-3xl font-semibold leading-tight">Plan smarter. Shop better. Save more.</h2>
          <ul className="mt-6 space-y-3">
            {POINTS.map((point) => (
              <li key={point} className="flex items-start gap-3 text-brand-100">
                <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-brand-200" aria-hidden="true" />
                {point}
              </li>
            ))}
          </ul>
        </div>
        <p className="text-sm text-brand-200">Built for Indian households · Prices in ₹</p>
      </div>
      <div className="flex flex-col items-center justify-center px-4 py-10 sm:px-6">
        <div className="mb-8 lg:hidden">
          <Brand />
        </div>
        <div className="w-full max-w-sm">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
