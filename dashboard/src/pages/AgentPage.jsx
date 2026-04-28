import { useState, useEffect, useMemo } from 'react'
import { fetchStats, fetchScanLogs, fetchMissions } from '../lib/supabase'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts'
import {
  Activity, Cpu, Zap, Target, TrendingUp, Database,
  CheckCircle2, AlertCircle,
} from 'lucide-react'

const TYPE_COLORS = { ia: '#7c3aed', web: '#2563eb', data: '#0891b2', consulting: '#d97706', design: '#db2777', other: '#64748b' }

function MetricCard({ icon: Icon, label, value, sub, gradient = 'from-slate-600 to-slate-700' }) {
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

export default function AgentPage() {
  const [stats, setStats] = useState(null)
  const [logs, setLogs] = useState([])
  const [missions, setMissions] = useState([])
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    try {
      const [s, l, m] = await Promise.all([fetchStats(), fetchScanLogs(50), fetchMissions({ limit: 200 })])
      setStats(s); setLogs(l || []); setMissions(m.data || [])
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  useEffect(() => { load(); const id = setInterval(load, 60000); return () => clearInterval(id) }, [])

  const sourceStats = useMemo(() => {
    const map = {}
    logs.forEach(l => {
      const s = l.source || 'unknown'
      if (!map[s]) map[s] = { source: s, total: 0, success: 0, missions: 0 }
      map[s].total += 1
      if (l.status === 'success') map[s].success += 1
      map[s].missions += l.missions_found || 0
    })
    return Object.values(map).map(s => ({ ...s, successRate: s.total ? Math.round((s.success / s.total) * 100) : 0 })).sort((a, b) => b.missions - a.missions)
  }, [logs])

  const typeDistribution = useMemo(() => {
    const map = {}
    missions.forEach(m => { const t = m.type || 'other'; map[t] = (map[t] || 0) + 1 })
    return Object.entries(map).map(([name, value]) => ({ name, value, fill: TYPE_COLORS[name] || '#64748b' }))
  }, [missions])

  const scoreDistribution = useMemo(() => {
    const b = [
      { range: '0-20', count: 0, fill: '#e2e8f0' }, { range: '20-40', count: 0, fill: '#94a3b8' },
      { range: '40-60', count: 0, fill: '#fbbf24' }, { range: '60-80', count: 0, fill: '#3b82f6' },
      { range: '80-100', count: 0, fill: '#10b981' },
    ]
    missions.forEach(m => { const s = m.score || 0; b[s < 20 ? 0 : s < 40 ? 1 : s < 60 ? 2 : s < 80 ? 3 : 4].count++ })
    return b
  }, [missions])

  const dailyActivity = useMemo(() => {
    const map = {}
    missions.forEach(m => {
      const d = m.found_at?.slice(0, 10)
      if (!d) return
      if (!map[d]) map[d] = { date: d, missions: 0, proposals: 0 }
      map[d].missions++
      if (m.status === 'proposal_ready' || m.status === 'sent') map[d].proposals++
    })
    return Object.values(map).sort((a, b) => a.date.localeCompare(b.date)).slice(-14)
  }, [missions])

  const metrics = useMemo(() => {
    const t = missions.length || 1
    const highScore = missions.filter(m => (m.score || 0) >= 70).length
    const proposed = missions.filter(m => m.status === 'proposal_ready' || m.status === 'sent' || m.status === 'won').length
    const won = missions.filter(m => m.status === 'won').length
    return {
      relevance: Math.round((highScore / t) * 100),
      proposal: Math.round((proposed / t) * 100),
      conversion: proposed ? Math.round((won / proposed) * 100) : 0,
      avg: Math.round(missions.reduce((s, m) => s + (m.score || 0), 0) / t),
    }
  }, [missions])

  const tooltipStyle = { borderRadius: 10, border: '1px solid #e2e8f0', fontSize: 12, boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' }

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Agent</h2>
          <p className="text-sm text-slate-500 mt-1">Performance, apprentissage et activite</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-[13px] font-semibold ${
            stats?.status === 'running'
              ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200'
              : 'bg-slate-100 text-slate-500 ring-1 ring-slate-200'
          }`}>
            <span className={`w-2 h-2 rounded-full ${stats?.status === 'running' ? 'bg-emerald-500 shadow-[0_0_6px_rgba(52,211,153,0.5)]' : 'bg-slate-400'}`} />
            {stats?.status === 'running' ? 'En activite' : 'Inactif'}
          </span>
          {stats?.uptime && <span className="text-[12px] text-slate-400 font-medium">{stats.uptime}</span>}
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard icon={Database} gradient="from-slate-700 to-slate-800" label="Missions analysees" value={missions.length} sub="Total en base" />
        <MetricCard icon={Target} gradient="from-blue-600 to-blue-700" label="Score moyen" value={metrics.avg} sub={`${metrics.relevance}% pertinentes`} />
        <MetricCard icon={Zap} gradient="from-violet-600 to-violet-700" label="Taux de proposition" value={`${metrics.proposal}%`} sub={`${stats?.proposals_today ?? 0} aujourd'hui`} />
        <MetricCard icon={TrendingUp} gradient="from-emerald-600 to-emerald-700" label="Conversion" value={`${metrics.conversion}%`} sub="Propositions gagnees" />
      </div>

      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
        <h3 className="text-[15px] font-bold text-slate-900 mb-1">Activite quotidienne</h3>
        <p className="text-[12px] text-slate-400 mb-5">14 derniers jours</p>
        <div className="h-64">
          {dailyActivity.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={dailyActivity}>
                <CartesianGrid stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickFormatter={d => d.slice(5)} />
                <YAxis stroke="#94a3b8" fontSize={11} />
                <Tooltip contentStyle={tooltipStyle} />
                <Line type="monotone" dataKey="missions" stroke="#2563eb" strokeWidth={2.5} dot={{ r: 3, fill: '#2563eb' }} name="Missions" />
                <Line type="monotone" dataKey="proposals" stroke="#7c3aed" strokeWidth={2.5} dot={{ r: 3, fill: '#7c3aed' }} name="Propositions" />
              </LineChart>
            </ResponsiveContainer>
          ) : <div className="h-full flex items-center justify-center text-sm text-slate-400">Pas encore de donnees</div>}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
          <h3 className="text-[15px] font-bold text-slate-900 mb-1">Distribution des scores</h3>
          <p className="text-[12px] text-slate-400 mb-5">Qualite du pipeline</p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scoreDistribution}>
                <CartesianGrid stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="range" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" fontSize={11} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="count" radius={[8, 8, 0, 0]}>{scoreDistribution.map((b, i) => <Cell key={i} fill={b.fill} />)}</Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
          <h3 className="text-[15px] font-bold text-slate-900 mb-1">Types de missions</h3>
          <p className="text-[12px] text-slate-400 mb-5">Repartition par categorie</p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={typeDistribution} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={3}
                  label={({ name, value }) => `${name} (${value})`} labelLine={false} fontSize={11}>
                  {typeDistribution.map((d, i) => <Cell key={i} fill={d.fill} />)}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm">
        <div className="px-5 py-4 border-b border-slate-100">
          <h3 className="text-[15px] font-bold text-slate-900">Performance par source</h3>
          <p className="text-[12px] text-slate-400 mt-0.5">L'agent privilegie les sources les plus fiables</p>
        </div>
        <div className="divide-y divide-slate-100/80">
          {sourceStats.length === 0 && <p className="px-5 py-12 text-center text-sm text-slate-400">Pas encore de donnees</p>}
          {sourceStats.map(s => (
            <div key={s.source} className="px-5 py-3.5 grid grid-cols-12 items-center gap-3 hover:bg-slate-50/80 transition-colors">
              <div className="col-span-3">
                <p className="text-[13px] font-bold text-slate-900">{s.source}</p>
                <p className="text-[11px] text-slate-400">{s.total} scans</p>
              </div>
              <div className="col-span-3">
                <div className="flex items-center gap-2.5">
                  <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 rounded-full transition-all" style={{ width: `${s.successRate}%` }} />
                  </div>
                  <span className="text-[12px] font-bold text-slate-700 tabular-nums w-10 text-right">{s.successRate}%</span>
                </div>
              </div>
              <div className="col-span-2">
                <p className="text-[14px] font-bold text-slate-900 tabular-nums">{s.missions}</p>
                <p className="text-[11px] text-slate-400">missions</p>
              </div>
              <div className="col-span-4 flex justify-end">
                {s.successRate >= 90 ? (
                  <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md ring-1 ring-emerald-600/10">
                    <CheckCircle2 className="w-3 h-3" /> Excellent
                  </span>
                ) : s.successRate >= 60 ? (
                  <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-blue-700 bg-blue-50 px-2.5 py-1 rounded-md ring-1 ring-blue-600/10">Stable</span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-amber-700 bg-amber-50 px-2.5 py-1 rounded-md ring-1 ring-amber-600/10">
                    <AlertCircle className="w-3 h-3" /> A surveiller
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
        <h3 className="text-[15px] font-bold text-slate-900 mb-1">Apprentissage</h3>
        <p className="text-[12px] text-slate-400 mb-5">L'agent affine son modele a chaque cycle</p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            { icon: Cpu, label: 'Pertinence', value: `${metrics.relevance}%`, desc: 'des missions matchent le profil', gradient: 'from-blue-600 to-blue-700' },
            { icon: Activity, label: 'Activation', value: `${metrics.proposal}%`, desc: 'declenchent une proposition', gradient: 'from-violet-600 to-violet-700' },
            { icon: TrendingUp, label: 'Conversion', value: `${metrics.conversion}%`, desc: 'des propositions gagnees', gradient: 'from-emerald-600 to-emerald-700' },
          ].map(({ icon: Icon, label, value, desc, gradient }) => (
            <div key={label} className="p-5 rounded-xl bg-slate-50/80 ring-1 ring-slate-200">
              <div className="flex items-center gap-2.5 mb-3">
                <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${gradient} flex items-center justify-center shadow-sm`}>
                  <Icon className="w-4 h-4 text-white" strokeWidth={2} />
                </div>
                <p className="text-[13px] font-bold text-slate-700">{label}</p>
              </div>
              <p className="text-2xl font-bold text-slate-900 tabular-nums tracking-tight">{value}</p>
              <p className="text-[11px] text-slate-400 mt-1">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
