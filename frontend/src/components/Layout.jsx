import { NavLink, useNavigate } from 'react-router-dom'
import { Activity, Bell, ShieldAlert, Cpu, Settings, LogOut, Layers } from 'lucide-react'
import clsx from 'clsx'

const items = [
  { to: '/', label: 'Overview', icon: Activity, end: true },
  { to: '/alerts', label: 'Alert Queue', icon: Bell },
  { to: '/mitre', label: 'MITRE ATT&CK', icon: Layers },
  { to: '/metrics', label: 'SOC Metrics', icon: Cpu },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export default function Layout({ user, onLogout, children }) {
  const nav = useNavigate()
  return (
    <div className="min-h-screen flex">
      <aside className="w-60 shrink-0 border-r border-soc-border bg-soc-panel/60 backdrop-blur p-4 flex flex-col">
        <div className="flex items-center gap-2 px-2 py-3 mb-2">
          <ShieldAlert className="text-soc-accent" size={22} />
          <div className="font-display font-bold tracking-wider text-soc-text">SOC<span className="text-soc-accent">.AI</span></div>
        </div>
        <nav className="flex-1 space-y-1">
          {items.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to} to={to} end={end}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2 rounded-md text-sm transition',
                  isActive
                    ? 'bg-soc-accent/10 text-soc-accent border border-soc-accent/30'
                    : 'text-soc-mute hover:text-soc-text hover:bg-white/5'
                )
              }
            >
              <Icon size={16} /> {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-soc-border pt-3">
          <div className="px-2 mb-2">
            <div className="label">Signed in as</div>
            <div className="text-sm font-medium">{user?.username}</div>
            <div className="text-xs text-soc-mute uppercase tracking-wider font-mono">{user?.role}</div>
          </div>
          <button className="btn-ghost w-full justify-start" onClick={() => { onLogout(); nav('/login') }}>
            <LogOut size={16} /> Logout
          </button>
        </div>
      </aside>
      <main className="flex-1 p-8 max-w-[1500px]">{children}</main>
    </div>
  )
}
