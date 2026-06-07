import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Search, Settings, Tent } from 'lucide-react'
import clsx from 'clsx'

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/search', label: 'Search', icon: Search },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <aside className="w-56 shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col">
        <div className="flex items-center gap-2.5 px-5 py-5 border-b border-slate-800">
          <Tent className="text-green-500 size-6 shrink-0" />
          <span className="font-semibold text-sm leading-tight">
            Campsite
            <br />
            Finder
          </span>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
                  isActive
                    ? 'bg-green-500/10 text-green-400 font-medium'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800',
                )
              }
            >
              <Icon className="size-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-5 py-4 border-t border-slate-800">
          <p className="text-xs text-slate-600">Recreation.gov Monitor</p>
        </div>
      </aside>

      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  )
}
