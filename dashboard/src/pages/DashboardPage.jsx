import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { fetchMissions, fetchStats, fetchScanLogs } from '../lib/supabase'
import { ArrowUpRight, RefreshCw } from 'lucide-react'
import cleanText from '../lib/cleanText'

function StatCard({ label, value, sub }) {
  return (
    <div className="p-6 rounded-lg border border-slate-200 hover:border-slate-300 transition-colors">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="text-4xl font-bold text-slate-950 tracking-tight mt-2 tabular-nums">{value}</p>
      {sub && <p className="text-[13px] text-slate-400 mt-2">{sub}</p>}
    </div>
  )
}

function ScoreValue({ score }) {
  const color = score >= 80 ? 'text-emerald-600'
    : score >= 60 ? 'text-amber-600'
    : 'text-slate-400'
  return <span className={`text-sm font-bold tabular-nums ${color}`}>{score}</span>
}

function StatusDot({ status }) {
  const map = {
    proposal_ready: { label: 'Proposition', color: 'bg-emerald-500' },
    sent: { label: 'Envoyé', color: 'bg-blue-500' },
    won: { label: 'Gagné', color: 'bg-emerald-500' },
    lost: { label: 'Perdu', color: 'bg-red-400' },
  }
  const s = map[status] || { label: 'Nouveau', color: 'bg-slate-300' }
  return (
    <div className="flex items-center gap-2">
      <span className={`w-1.5 h-1.5 rounded-full ${s.color}`} />
      <span className="text-[13px] text-slate-500">{s.label}</span>
    </div>
  )
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
    <div className="space-y-8">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-semibold text-slate-950 tracking-tight">Vue d'ensemble</h2>
          <p className="text-sm text-slate-500 mt-1">Activité de l'agent et missions prioritaires</p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-200 text-[13px] font-medium text-slate-600 hover:border-slate-300 hover:text-slate-900 transition-colors disabled:opacity-40"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} strokeWidth={2} />
          Actualiser
        </button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Statut agent" value={stats?.status === 'running' ? 'Actif' : '—'} sub={stats?.uptime || null} />
        <StatCard label="Missions du jour" value={stats?.missions_today ?? '—'} sub={`${Object.keys(stats?.sources || {}).length} sources actives`} />
        <StatCard label="Propositions" value={stats?.proposals_today ?? '—'} sub="Générées aujourd'hui" />
        <StatCard label="Scans réalisés" value={stats?.scans_total ?? '—'} sub={stats?.last_scan ? `Dernier ${new Date(stats.last_scan).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}` : null} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-slate-500 uppercase tracking-wider">Missions prioritaires</h3>
            <Link to="/missions" className="text-[13px] text-blue-600 hover:text-blue-700 font-medium inline-flex items-center gap-1">
              Tout voir <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          <div className="border border-slate-200 rounded-lg divide-y divide-slate-100">
            {!loading && missions.length === 0 && (
              <p className="px-6 py-12 text-center text-sm text-slate-400">Aucune mission prioritaire pour le moment</p>
            )}
            {missions.slice(0, 8).map(m => (
              <Link key={m.id} to={`/missions/${m.id}`} className="flex items-center gap-5 px-6 py-4 hover:bg-slate-50 transition-colors group">
                <ScoreValue score={m.score || 0} />
                <div className="flex-1 min-w-0">
                  <p className="text-[14px] font-medium text-slate-950 truncate group-hover:text-blue-600 transition-colors">{cleanText(m.title)}</p>
                  <p className="text-[13px] text-slate-400 mt-0.5">{cleanText(m.company) || 'Entreprise non précisée'} &middot; {cleanText(m.source)}</p>
                </div>
                <StatusDot status={m.status} />
              </Link>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-slate-500 uppercase tracking-wider mb-4">Activité des scans</h3>
          <div className="border border-slate-200 rounded-lg divide-y divide-slate-100 max-h-[480px] overflow-y-auto">
            {!loading && logs.length === 0 && (
              <p className="px-6 py-12 text-center text-sm text-slate-400">Aucun scan recent</p>
            )}
            {logs.slice(0, 14).map((l, i) => (
              <div key={i} className="flex items-center gap-3 px-5 py-3.5">
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${l.status === 'success' ? 'bg-emerald-500' : l.status === 'running' ? 'bg-amber-400 animate-pulse' : 'bg-red-400'}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-[14px] text-slate-800 truncate">{l.source}</p>
                  <p className="text-[13px] text-slate-400">{l.missions_found ?? 0} trouvées &middot; {l.missions_new ?? 0} nouvelles</p>
                </div>
                <span className="text-[13px] text-slate-400 shrink-0 tabular-nums">
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
