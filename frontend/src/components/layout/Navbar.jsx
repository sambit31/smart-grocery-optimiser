import { LogOut, Menu, Home } from 'lucide-react'
import { useLocation, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { useAuth } from '../../context/AuthContext'

const PAGE_TITLES = {
  '/app': 'Dashboard',
  '/app/household': 'Household',
  '/app/groceries': 'Grocery Catalogue',
  '/app/inventory': 'Inventory',
  '/app/purchases': 'Purchase History',
  '/app/consumption': 'Consumption',
  '/app/predictions': 'Predictions',
  '/app/budget': 'Budget Optimisation',
  '/app/shopping-list': 'Shopping List',
  '/app/reports': 'Reports',
  '/app/feedback': 'Feedback',
}

export default function Navbar({ onMenuClick }) {
  const { user, household, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const pageTitle = PAGE_TITLES[location.pathname] || 'GrocerySmart'

  const handleLogout = async () => {
    try {
      await logout()
      toast.success('Logged out successfully.')
      navigate('/login')
    } catch {
      toast.error('Unable to log out. Please try again.')
    }
  }

  const initials = (user?.name || '?')
    .split(' ')
    .filter(Boolean)
    .map((part) => part[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/95 backdrop-blur-xl">

      <div className="flex h-[76px] items-center gap-4 px-4 sm:px-6 lg:px-8">

        {/* Mobile menu */}
        <button
          type="button"
          onClick={onMenuClick}
          className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 text-slate-600 transition hover:bg-slate-50 lg:hidden"
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Page title */}
        <div className="min-w-0">
          <h1 className="truncate text-lg font-bold tracking-tight text-slate-900 sm:text-xl">
            {pageTitle}
          </h1>

          <p className="hidden text-xs text-slate-500 sm:block">
            Manage your groceries smarter.
          </p>
        </div>

        <div className="ml-auto flex items-center gap-3">

          {/* Household information */}
          <div className="hidden items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 md:flex">
            <Home className="h-4 w-4 text-emerald-700" />

            <div className="max-w-40">
              <p className="truncate text-xs font-semibold text-slate-800">
                {household?.household_name || 'My Household'}
              </p>
              <p className="text-[10px] text-slate-500">
                Active household
              </p>
            </div>
          </div>

          {/* User profile */}
          <div className="flex items-center gap-2.5 border-l border-slate-200 pl-3 sm:pl-4">

            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-sm font-bold text-emerald-800 ring-2 ring-emerald-50">
              {initials}
            </div>

            <div className="hidden min-w-0 sm:block">
              <p className="max-w-32 truncate text-sm font-semibold text-slate-800">
                {user?.name || 'User'}
              </p>
              <p className="max-w-36 truncate text-[11px] text-slate-500">
                {user?.email}
              </p>
            </div>
          </div>

          {/* Logout */}
          <button
            type="button"
            onClick={handleLogout}
            title="Log out"
            className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 text-slate-500 transition hover:border-red-200 hover:bg-red-50 hover:text-red-600 sm:w-auto sm:gap-2 sm:px-3"
          >
            <LogOut className="h-4 w-4" />
            <span className="hidden text-xs font-semibold sm:inline">
              Logout
            </span>
          </button>

        </div>
      </div>
    </header>
  )
}