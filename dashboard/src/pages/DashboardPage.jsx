import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { fetchMissions, fetchStats, fetchScanLogs } from '../lib/supabase'
import { ArrowUpRight, RefreshCw, TrendingUp, Zap, Target, BarChart3 } from 'lucide-react'

const STAT_ICONS = [
  { icon: Zap, gradient: 'from-blue-600 to-blue-700' },
  { icon: Target, gradient: 'from-emerald-600 to-emerald-700' },
  { icon: TrendingUp, gradient: 'from-violet-600 to-violet-700' },
  { icon: BarChart3, gradient: 'from-amber-500 to-orange-600' },
]

function StatCard({ label, value, sub, index = 0 }) {
  const { icon: Icon, gradient } = STAT_ICONS[index % STAT_ICONS.length]
  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className={`w-9 h-9 rounded-lg bg-gradient-to-br ${gradient} flex items-center justify-center shadow-sm`}>
          <Icon className="w-4 h-4 text-white" strokeWidth={2} />
        </div>
      </div>
      <p className="text-2xl font-bold text-slate-900 tabular-nums tracking-tight">{value}</p>
      <p className="text-[13px] font-medium text-slate-600 mt-0.5">{label}</p>
      {sub && <p className="text-[11px] text-slate-400 mt-1">{sub}</p>}
    </div>
  )
}

function ScoreBadge({ score }) {
  const cls = score >= 80 ? 'text-emerald-700 bg-emerald-50 ring-emerald-600/10'
    : score >= 60 ? 'text-blue-700 bg-blue-50 ring-blue-600/10'
    : score >= 40 ? 'text-amber-700 bg-amber-50 ring-amber-600/10'
    : 'text-slate-600 bg-slate-50 ring-slate-500/10'
  return <span className={`inline-flex items-center justify-center w-10 h-7 rounded-md text-[11px] font-bold tabular-nums ring-1 ${cls}`}>{score}</span>
}

function StatusBadge({ status }) {
  const map = {
    proposal_ready: { label: 'Proposition', cls: 'bg-emerald-50 text-emerald-700 ring-emerald-600/10' },
    sent: { label: 'Envoye', cls: 'bg-blue-50 text-blue-700 ring-blue-600/10' },
    won: { label: 'Gagne', cls: 'bg-emerald-100 text-emerald-800 ring-emerald-600/10' },
    lost: { label: 'Perdu', cls: 'bg-red-50 text-red-600 ring-red-600/10' },
  }
  const s = map[status] || { label: 'Nouveau', cls: 'bg-slate-50 text-slate-600 ring-slate-500/10' }
  return <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-md ring-1 ${s.cls}`}>{s.label}</span>
}

export default function DashboardPage() {
  const [stats, setStats] = useState(null)
  const [missions, setMissions] = useState([])
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)

  async function loadData() {
    setLoading(true)
    try {
      const [s, m, l] = await Promise.all([
        fetchStats(),
        fetchMissions({ limit: 10, minScore: 50 }),
        fetchScanLogs(15),
      ])
      setStats(s)
      setMissions(m.data || [])
      setLogs(l || [])
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  useEffect(() => { loadData() }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Vue d'ensemble</h2>
          <p className="text-sm text-slate-500 mt-1">Activite de l'agent et missions prioritaires</p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white border border-slate-200 text-[13px] font-semibold text-slate-700 hover:bg-slate-50 hover:border-slate-300 transition-all shadow-sm disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} strokeWidth={2} />
          Actualiser
        </button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard index={0} label="Statut agent" value={stats?.status === 'running' ? 'Actif' : 'Inactif'} sub={stats?.uptime || null} />
        <StatCard index={1} label="Missions du jour" value={stats?.missions_today ?? '—'} sub={`${Object.keys(stats?.sources || {}).length} sources actives`} />
        <StatCard index={2} label="Propositions" value={stats?.proposals_today ?? '—'} sub="Generees aujourd'hui" />
        <StatCard index={3} label="Scans realises" value={stats?.scans_total ?? '—'} sub={stats?.last_scan ? `Dernier ${new Date(stats.last_scan).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}` : null} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
            <div>
              <h3 className="text-[15px] font-bold text-slate-900">Missions prioritaires</h3>
              <p className="text-[12px] text-slate-400 mt-0.5">Score &ge; 50</p>
            </div>
            <Link to="/missions" className="text-[12px] text-blue-600 hover:text-blue-700 font-semibold inline-flex items-center gap-1 hover:gap-1.5 transition-all">
              Tout voir <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          <div className="divide-y divide-slate-100/80">
            {!loading && missions.length === 0 && (
              <p className="px-5 py-12 text-center text-sm text-slate-400">Aucune mission prioritaire pour le moment</p>
            )}
            {missions.slice(0, 8).map(m => (
              <Link key={m.id} to={`/missions/${m.id}`} className="flex items-center gap-4 px-5 py-3.5 hover:bg-slate-50/80 transition-colors group">
                <ScoreBadge score={m.score || 0} />
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] font-semibold text-slate-900 truncate group-hover:text-blue-600 transition-colors">{m.title}</p>
                  <p className="text-[12px] text-slate-500 mt-0.5">{m.company || 'Entreprise non precisee'} &middot; {m.source}</p>
                </div>
                <StatusBadge status={m.status} />
              </Link>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm">
          <div className="px-5 py-4 border-b border-slate-100">
            <h3 className="text-[15px] font-bold text-slate-900">Activite des scans</h3>
            <p className="text-[12px] text-slate-400 mt-0.5">Derniers cycles</p>
          </div>
          <div className="divide-y divide-slate-100/80 max-h-[420px] overflow-y-auto">
            {!loading && logs.length === 0 && (
              <p className="px-5 py-12 text-center text-sm text-slate-400">Aucun scan recent</p>
            )}
            {logs.slice(0, 14).map((l, i) => (
              <div key={i} className="flex items-center gap-3 px-5 py-3">
                <span className={`w-2 h-2 rounded-full shrink-0 ${l.status === 'success' ? 'bg-emerald-500' : l.status === 'running' ? 'bg-amber-400 animate-pulse' : 'bg-red-500'}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] font-medium text-slate-800 truncate">{l.source}</p>
                  <p className="text-[11px] text-slate-400">{l.missions_found ?? 0} trouvees &middot; {l.missions_new ?? 0} nouvelles</p>
                </div>
                <span className="text-[11px] text-slate-400 shrink-0 tabular-nums font-medium">
                  {l.started_at ? new Date(l.started_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : ''}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
