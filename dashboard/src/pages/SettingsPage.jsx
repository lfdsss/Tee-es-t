import { useState, useEffect } from 'react'
import { fetchStats } from '../lib/supabase'
import { RefreshCw, CheckCircle2, XCircle, Server, User2, Cog } from 'lucide-react'

function Field({ label, value, mono = false }) {
  return (
    <div className="flex justify-between items-center py-3 border-b border-slate-100 last:border-0">
      <span className="text-[13px] text-slate-500 font-medium">{label}</span>
      <span className={`text-[13px] text-slate-900 font-semibold ${mono ? 'font-mono text-[12px]' : ''}`}>{value}</span>
    </div>
  )
}

export default function SettingsPage({ session }) {
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { fetchStats().then(d => { setHealth(d); setLoading(false) }) }, [])

  async function refresh() {
    setLoading(true)
    const d = await fetchStats()
    setHealth(d)
    setLoading(false)
  }

  const isOnline = health?.status === 'running'

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Parametres</h2>
          <p className="text-sm text-slate-500 mt-1">Configuration de l'agent et services connectes</p>
        </div>
        <button onClick={refresh} disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white border border-slate-200 text-[13px] font-semibold text-slate-700 hover:bg-slate-50 hover:border-slate-300 transition-all shadow-sm disabled:opacity-50">
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} strokeWidth={2} />
          Actualiser
        </button>
      </div>

      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center shadow-sm">
              <Server className="w-4 h-4 text-white" strokeWidth={2} />
            </div>
            <h3 className="text-[15px] font-bold text-slate-900">Infrastructure</h3>
          </div>
          <span className={`inline-flex items-center gap-2 text-[12px] font-semibold px-3 py-1.5 rounded-lg ring-1 ${
            isOnline ? 'bg-emerald-50 text-emerald-700 ring-emerald-200' : 'bg-slate-100 text-slate-500 ring-slate-200'
          }`}>
            {isOnline ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
            {isOnline ? 'Tous services actifs' : 'Hors ligne'}
          </span>
        </div>
        <div className="grid grid-cols-2 gap-x-8">
          <Field label="Statut agent" value={isOnline ? 'En ligne' : 'Hors ligne'} />
          <Field label="Uptime" value={health?.uptime || '—'} />
          <Field label="Scans realises" value={health?.scans_total ?? '—'} />
          <Field label="Dernier scan" value={health?.last_scan ? new Date(health.last_scan).toLocaleString('fr-FR') : '—'} />
        </div>
      </div>

      {health?.sources && Object.keys(health.sources).length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
          <h3 className="text-[15px] font-bold text-slate-900 mb-4">Sources actives</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {Object.entries(health.sources).map(([name, info]) => (
              <div key={name} className="flex items-center justify-between py-2.5 px-4 rounded-xl bg-slate-50 ring-1 ring-slate-200 hover:ring-slate-300 transition-all">
                <div className="flex items-center gap-2.5">
                  <span className={`w-2 h-2 rounded-full ${info.status === 'success' ? 'bg-emerald-500' : 'bg-red-500'}`} />
                  <span className="text-[13px] text-slate-700 font-semibold">{name}</span>
                </div>
                <span className="text-[12px] text-slate-500 tabular-nums font-medium">{info.missions_found || 0}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-600 to-blue-700 flex items-center justify-center shadow-sm">
            <User2 className="w-4 h-4 text-white" strokeWidth={2} />
          </div>
          <h3 className="text-[15px] font-bold text-slate-900">Session</h3>
        </div>
        <Field label="Utilisateur" value={session.name} />
        <Field label="Role" value={session.role === 'tech' ? 'Consultant' : 'Administration'} />
        <Field label="Profil de chasse" value={session.role === 'tech' ? 'Missions tech & IA' : 'Missions admin & support'} />
      </div>

      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-violet-600 to-violet-700 flex items-center justify-center shadow-sm">
            <Cog className="w-4 h-4 text-white" strokeWidth={2} />
          </div>
          <h3 className="text-[15px] font-bold text-slate-900">Configuration de l'agent</h3>
        </div>
        <Field label="Score minimum proposition" value="70 / 100" />
        <Field label="Intervalle scan rapide (Tier 1)" value="5 minutes" />
        <Field label="Intervalle scan lent (Tier 2)" value="30 minutes" />
        <Field label="Sources surveillees" value="14 scrapers" />
        <Field label="Modele de generation" value="Claude Sonnet 4" />
        <Field label="TJM consultant" value="450 EUR/jour HT" />
        <Field label="Penalite CDI" value="-15 points" />
      </div>
    </div>
  )
}
