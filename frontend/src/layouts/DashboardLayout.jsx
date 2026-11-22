import { useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { X } from 'lucide-react'
import Navbar from '../components/layout/Navbar'
import Sidebar from '../components/layout/Sidebar'

export default function DashboardLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()

  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  return (
    <div className="min-h-screen bg-slate-50">

      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 bg-[#123c2d] lg:block">
        <Sidebar />
      </aside>

      {/* Mobile sidebar */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">

          <button
            type="button"
            className="absolute inset-0 h-full w-full bg-slate-950/60"
            onClick={() => setMobileOpen(false)}
            aria-label="Close navigation"
          />

          <aside className="relative h-full w-72 max-w-[85%] bg-[#123c2d] shadow-2xl">
            <button
              type="button"
              className="absolute right-3 top-4 z-10 flex h-8 w-8 items-center justify-center rounded-lg text-white/70 hover:bg-white/10 hover:text-white"
              onClick={() => setMobileOpen(false)}
              aria-label="Close menu"
            >
              <X className="h-5 w-5" />
            </button>

            <Sidebar onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}

      {/* Main application */}
      <div className="lg:pl-64">
        <Navbar onMenuClick={() => setMobileOpen(true)} />

        <main className="mx-auto max-w-[1600px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>
      </div>

    </div>
  )
}