import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { logout } from '../lib/auth'
import { useState, useEffect } from 'react'
import {
  LayoutDashboard, Briefcase, FileText, FolderOpen,
  Settings, LogOut, Menu, Activity, X,
} from 'lucide-react'
import { fetchStats } from '../lib/supabase'
import ChatWidget from './ChatWidget'

const NAV = [
  { to: '/', icon: LayoutDashboard, label: 'Vue d\'ensemble' },
  { to: '/missions', icon: Briefcase, label: 'Missions' },
  { to: '/proposals', icon: FileText, label: 'Propositions' },
  { to: '/documents', icon: FolderOpen, label: 'Documents' },
  { to: '/agent', icon: Activity, label: 'Agent' },
  { to: '/settings', icon: Settings, label: 'Paramètres' },
]

export default function Layout({ session, onLogout }) {
  const [open, setOpen] = useState(false)
  const [agentStatus, setAgentStatus] = useState(null)
  const location = useLocation()

  useEffect(() => {
    let active = true
    async function poll() {
      const s = await fetchStats().catch(() => null)
      if (active) setAgentStatus(s)
    }
    poll()
    const id = setInterval(poll, 60000)
    return () => { active = false; clearInterval(id) }
  }, [])

  function handleLogout() {
    logout()
    onLogout()
  }

  const isOnline = agentStatus?.status === 'running'
  const currentPage = NAV.find(n => location.pathname === n.to || (n.to !== '/' && location.pathname.startsWith(n.to)))

  return (
    <div className="flex h-screen overflow-hidden bg-white">
      {open && <div className="fixed inset-0 bg-black/20 z-40 lg:hidden" onClick={() => setOpen(false)} />}

      <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-[240px] bg-black flex flex-col transition-transform duration-300 ease-out ${open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
        <div className="px-5 py-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded bg-white flex items-center justify-center">
              <span className="text-xs font-bold text-black leading-none">MH</span>
            </div>
            <div>
              <p className="text-sm font-medium text-white leading-none">Mission Hunter</p>
              <p className="text-[13px] text-slate-500 mt-1">{session.name}</p>
            </div>
          </div>
          <button onClick={() => setOpen(false)} className="lg:hidden text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 py-4 px-3 space-y-0.5 overflow-y-auto">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded text-[14px] transition-colors relative ${
                  isActive
                    ? 'text-white'
                    : 'text-slate-500 hover:text-slate-300'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-white rounded-full" />
                  )}
                  <Icon className="w-[18px] h-[18px] text-slate-500" strokeWidth={1.75} />
                  <span>{label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="px-5 py-5 space-y-4">
          <div className="flex items-center gap-2">
            <span className={`w-1.5 h-1.5 rounded-full ${isOnline ? 'bg-emerald-400' : 'bg-slate-600'}`} />
            <span className="text-[13px] text-slate-500">
              {isOnline ? 'En ligne' : 'Hors ligne'}
            </span>
          </div>

          <button
            onClick={handleLogout}
            className="text-[13px] text-slate-600 hover:text-slate-300 transition-colors"
          >
            Deconnexion
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-14 border-b border-slate-200 flex items-center px-4 lg:px-8 shrink-0">
          <button onClick={() => setOpen(true)} className="lg:hidden p-1.5 mr-3 -ml-1 text-slate-400 hover:text-slate-900 rounded transition-colors">
            <Menu className="w-5 h-5" strokeWidth={1.75} />
          </button>
          <span className="text-sm font-medium text-slate-950">{currentPage?.label || 'Mission Hunter'}</span>
        </header>

        <main className="flex-1 overflow-y-auto">
          <div className="px-4 lg:px-8 py-6 max-w-[1280px]">
            <Outlet />
          </div>
        </main>
      </div>
      <ChatWidget />
    </div>
  )
}
