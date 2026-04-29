import { useState, useEffect, useMemo } from 'react'
import { fetchStats, fetchScanLogs, fetchMissions } from '../lib/supabase'
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts'

const TYPE_COLORS = { ia: '#0f172a', web: '#475569', data: '#64748b', consulting: '#94a3b8', design: '#cbd5e1', other: '#e2e8f0' }

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
    return Object.entries(map).map(([name, value]) => ({ name, value, fill: TYPE_COLORS[name] || '#94a3b8' }))
  }, [missions])

  const scoreDistribution = useMemo(() => {
    const b = [
      { range: '0-20', count: 0, fill: '#e2e8f0' }, { range: '20-40', count: 0, fill: '#cbd5e1' },
      { range: '40-60', count: 0, fill: '#94a3b8' }, { range: '60-80', count: 0, fill: '#475569' },
      { range: '80-100', count: 0, fill: '#0f172a' },
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

  const tooltipStyle = { borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 13, boxShadow: 'none' }

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-950 tracking-tight">Agent</h2>
          <p className="text-sm text-slate-500 mt-1">Performance, apprentissage et activite</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-2 text-sm text-slate-600">
            <span className={`w-1.5 h-1.5 rounded-full ${stats?.status === 'running' ? 'bg-emerald-500' : 'bg-slate-400'}`} />
            {stats?.status === 'running' ? 'En activite' : 'Inactif'}
          </span>
          {stats?.uptime && <span className="text-[13px] text-slate-400">{stats.uptime}</span>}
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Missions analysees', value: missions.length, sub: 'Total en base' },
          { label: 'Score moyen', value: metrics.avg, sub: `${metrics.relevance}% pertinentes` },
          { label: 'Taux de proposition', value: `${metrics.proposal}%`, sub: `${stats?.proposals_today ?? 0} aujourd'hui` },
          { label: 'Conversion', value: `${metrics.conversion}%`, sub: 'Propositions gagnees' },
        ].map(card => (
          <div key={card.label} className="bg-white border border-slate-200 rounded-lg p-6">
            <p className="text-3xl font-bold text-slate-950 tabular-nums tracking-tight">{card.value}</p>
            <p className="text-sm text-slate-500 mt-1">{card.label}</p>
            {card.sub && <p className="text-[13px] text-slate-400 mt-0.5">{card.sub}</p>}
          </div>
        ))}
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Activite quotidienne</p>
        <p className="text-[13px] text-slate-500 mb-6">14 derniers jours</p>
        <div className="h-64">
          {dailyActivity.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={dailyActivity}>
                <CartesianGrid stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="date" stroke="#cbd5e1" fontSize={12} tickFormatter={d => d.slice(5)} />
                <YAxis stroke="#cbd5e1" fontSize={12} />
                <Tooltip contentStyle={tooltipStyle} />
                <Line type="monotone" dataKey="missions" stroke="#0f172a" strokeWidth={1.5} dot={{ r: 2.5, fill: '#0f172a' }} name="Missions" />
                <Line type="monotone" dataKey="proposals" stroke="#94a3b8" strokeWidth={1.5} dot={{ r: 2.5, fill: '#94a3b8' }} name="Propositions" />
              </LineChart>
            </ResponsiveContainer>
          ) : <div className="h-full flex items-center justify-center text-sm text-slate-400">Pas encore de donnees</div>}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Distribution des scores</p>
          <p className="text-[13px] text-slate-500 mb-6">Qualite du pipeline</p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scoreDistribution}>
                <CartesianGrid stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="range" stroke="#cbd5e1" fontSize={12} />
                <YAxis stroke="#cbd5e1" fontSize={12} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>{scoreDistribution.map((b, i) => <Cell key={i} fill={b.fill} />)}</Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Types de missions</p>
          <p className="text-[13px] text-slate-500 mb-6">Repartition par categorie</p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={typeDistribution} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={2}
                  label={({ name, value }) => `${name} (${value})`} labelLine={false} fontSize={12}>
                  {typeDistribution.map((d, i) => <Cell key={i} fill={d.fill} />)}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg">
        <div className="px-6 py-5 border-b border-slate-200">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Performance par source</p>
          <p className="text-[13px] text-slate-500">L'agent privilegie les sources les plus fiables</p>
        </div>
        {sourceStats.length === 0 && <p className="px-6 py-12 text-center text-sm text-slate-400">Pas encore de donnees</p>}
        {sourceStats.map((s, i) => (
          <div key={s.source} className={`px-6 py-4 grid grid-cols-12 items-center gap-4 ${i % 2 === 1 ? 'bg-slate-50' : ''}`}>
            <div className="col-span-3">
              <p className="text-sm font-medium text-slate-950">{s.source}</p>
              <p className="text-[13px] text-slate-400">{s.total} scans</p>
            </div>
            <div className="col-span-4">
              <div className="flex items-center gap-3">
                <div className="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                  <div className="h-full bg-slate-900 rounded-full transition-all" style={{ width: `${s.successRate}%` }} />
                </div>
                <span className="text-sm font-medium text-slate-600 tabular-nums w-10 text-right">{s.successRate}%</span>
              </div>
            </div>
            <div className="col-span-2">
              <p className="text-sm font-bold text-slate-950 tabular-nums">{s.missions}</p>
              <p className="text-[13px] text-slate-400">missions</p>
            </div>
            <div className="col-span-3 flex justify-end">
              <span className="flex items-center gap-2 text-sm text-slate-500">
                <span className={`w-1.5 h-1.5 rounded-full ${s.successRate >= 90 ? 'bg-emerald-500' : s.successRate >= 60 ? 'bg-blue-500' : 'bg-amber-500'}`} />
                {s.successRate >= 90 ? 'Excellent' : s.successRate >= 60 ? 'Stable' : 'A surveiller'}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Apprentissage</p>
        <p className="text-[13px] text-slate-500 mb-6">L'agent affine son modele a chaque cycle</p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            { label: 'Pertinence', value: `${metrics.relevance}%`, desc: 'des missions matchent le profil' },
            { label: 'Activation', value: `${metrics.proposal}%`, desc: 'declenchent une proposition' },
            { label: 'Conversion', value: `${metrics.conversion}%`, desc: 'des propositions gagnees' },
          ].map(({ label, value, desc }) => (
            <div key={label} className="p-5 border border-slate-200 rounded-lg">
              <p className="text-[13px] text-slate-500 mb-2">{label}</p>
              <p className="text-3xl font-bold text-slate-950 tabular-nums tracking-tight">{value}</p>
              <p className="text-[13px] text-slate-400 mt-1">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
