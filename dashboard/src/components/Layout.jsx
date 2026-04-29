import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { logout } from '../lib/auth'
import { useState, useEffect } from 'react'
import {
  LayoutDashboard, Briefcase, FileText, FolderOpen,
  Settings, LogOut, Menu, Activity, ChevronRight, X,
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
    <div className="flex h-screen overflow-hidden bg-[#f8fafc]">
      {open && <div className="fixed inset-0 bg-black/30 z-40 lg:hidden backdrop-blur-sm" onClick={() => setOpen(false)} />}

      <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-[260px] bg-slate-900 flex flex-col transition-transform duration-300 ease-out ${open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
        <div className="px-5 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
              <Briefcase className="w-4 h-4 text-white" strokeWidth={2} />
            </div>
            <div>
              <p className="text-[13px] font-semibold text-white leading-none">Mission Hunter</p>
              <p className="text-[11px] text-slate-500 mt-0.5">{session.name}</p>
            </div>
          </div>
          <button onClick={() => setOpen(false)} className="lg:hidden text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-3 mb-1">
          <div className="h-px bg-slate-800" />
        </div>

        <nav className="flex-1 py-2 px-3 space-y-0.5 overflow-y-auto">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-white/10 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`
              }
            >
              <Icon className="w-[18px] h-[18px]" strokeWidth={1.75} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="px-3 py-4">
          <div className="px-3 py-2.5 rounded-lg bg-white/5 mb-3">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${isOnline ? 'bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.5)]' : 'bg-slate-600'}`} />
              <span className="text-[12px] font-medium text-slate-300">
                {isOnline ? 'Agent en ligne' : 'Agent hors ligne'}
              </span>
            </div>
            {agentStatus && isOnline && (
              <p className="text-[11px] text-slate-500 mt-1 ml-4">
                {agentStatus.missions_today ?? 0} missions · {agentStatus.proposals_today ?? 0} propositions
              </p>
            )}
          </div>

          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] text-slate-500 hover:bg-white/5 hover:text-slate-300 w-full transition-all duration-150"
          >
            <LogOut className="w-[18px] h-[18px]" strokeWidth={1.75} />
            Deconnexion
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-14 bg-white border-b border-slate-200/80 flex items-center px-4 lg:px-8 shrink-0 shadow-[0_1px_2px_rgba(0,0,0,0.03)]">
          <button onClick={() => setOpen(true)} className="lg:hidden p-1.5 mr-3 -ml-1 text-slate-500 hover:text-slate-900 rounded-lg hover:bg-slate-100 transition-colors">
            <Menu className="w-5 h-5" strokeWidth={1.75} />
          </button>
          <div className="flex items-center gap-2 text-[13px]">
            <span className="text-slate-400 font-medium">SNB</span>
            <ChevronRight className="w-3.5 h-3.5 text-slate-300" strokeWidth={2} />
            <span className="font-semibold text-slate-900">{currentPage?.label || 'Mission Hunter'}</span>
          </div>
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
