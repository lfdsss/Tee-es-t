import { useState, useEffect } from 'react'
import { fetchStats } from '../lib/supabase'
import { RefreshCw } from 'lucide-react'

function Field({ label, value, mono = false }) {
  return (
    <div className="flex justify-between items-center py-3.5 border-b border-slate-100 last:border-0">
      <span className="text-sm text-slate-500">{label}</span>
      <span className={`text-sm text-slate-950 font-medium ${mono ? 'font-mono text-[13px]' : ''}`}>{value}</span>
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
          <h2 className="text-2xl font-bold text-slate-950 tracking-tight">Parametres</h2>
          <p className="text-sm text-slate-500 mt-1">Configuration de l'agent et services connectes</p>
        </div>
        <button onClick={refresh} disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg border border-slate-200 text-sm text-slate-700 hover:border-slate-300 transition-colors disabled:opacity-50">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Actualiser
        </button>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-lg font-semibold text-slate-950">Infrastructure</h3>
          <span className="flex items-center gap-2 text-sm text-slate-600">
            <span className={`w-1.5 h-1.5 rounded-full ${isOnline ? 'bg-emerald-500' : 'bg-red-500'}`} />
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
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-slate-950 mb-5">Sources actives</h3>
          <div className="space-y-0">
            {Object.entries(health.sources).map(([name, info]) => (
              <div key={name} className="flex items-center justify-between py-3.5 border-b border-slate-100 last:border-0">
                <div className="flex items-center gap-2.5">
                  <span className={`w-1.5 h-1.5 rounded-full ${info.status === 'success' ? 'bg-emerald-500' : 'bg-red-500'}`} />
                  <span className="text-sm text-slate-950 font-medium">{name}</span>
                </div>
                <span className="text-sm text-slate-500 tabular-nums">{info.missions_found || 0} missions</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-slate-950 mb-5">Session</h3>
        <Field label="Utilisateur" value={session.name} />
        <Field label="Role" value={session.role === 'tech' ? 'Consultant' : 'Administration'} />
        <Field label="Profil de chasse" value={session.role === 'tech' ? 'Missions tech & IA' : 'Missions admin & support'} />
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-slate-950 mb-5">Configuration de l'agent</h3>
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
