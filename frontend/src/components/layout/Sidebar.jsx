import { NavLink } from 'react-router-dom'
import { ChevronRight, Leaf } from 'lucide-react'
import Brand from '../common/Brand'
import { NAV_GROUPS } from './navItems'

export default function Sidebar({ onNavigate }) {
  return (
    <nav
      aria-label="Main navigation"
      className="flex h-full flex-col text-white"
    >

      {/* Brand */}
      <div className="flex h-20 items-center border-b border-white/10 px-6">
        <Brand to="/app" light />
      </div>

      {/* Navigation */}
      <div className="flex-1 space-y-7 overflow-y-auto px-4 py-7">

        {NAV_GROUPS.map((group) => (
          <div key={group.label}>

            <p className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[0.18em] text-emerald-200/50">
              {group.label}
            </p>

            <ul className="space-y-1">

              {group.items.map(({ to, label, icon: Icon, end }) => (
                <li key={to}>
                  <NavLink
                    to={to}
                    end={end}
                    onClick={onNavigate}
                    className={({ isActive }) =>
                      `group flex items-center gap-3 rounded-xl px-3 py-3 text-[13px] font-medium transition-all duration-200 ${
                        isActive
                          ? 'bg-emerald-400/15 text-white shadow-sm ring-1 ring-emerald-300/20'
                          : 'text-emerald-50/65 hover:bg-white/8 hover:text-white'
                      }`
                    }
                  >
                    {({ isActive }) => (
                      <>
                        <Icon
                          className={`h-[18px] w-[18px] shrink-0 ${
                            isActive
                              ? 'text-emerald-300'
                              : 'text-emerald-100/55 group-hover:text-emerald-200'
                          }`}
                        />

                        <span className="flex-1">{label}</span>

                        {isActive && (
                          <ChevronRight className="h-4 w-4 text-emerald-300" />
                        )}
                      </>
                    )}
                  </NavLink>
                </li>
              ))}

            </ul>
          </div>
        ))}

      </div>

      {/* Sidebar footer */}
      <div className="border-t border-white/10 p-4">
        <div className="rounded-xl bg-white/5 p-4">
          <div className="mb-2 flex items-center gap-2">
            <Leaf className="h-4 w-4 text-emerald-300" />
            <span className="text-xs font-semibold text-white">
              Smart shopping
            </span>
          </div>

          <p className="text-[11px] leading-relaxed text-emerald-100/55">
            Plan better, reduce waste and manage your grocery budget.
          </p>
        </div>

        <p className="mt-4 text-center text-[10px] text-emerald-100/35">
          GrocerySmart · Smart Grocery Management
        </p>
      </div>

    </nav>
  )
}