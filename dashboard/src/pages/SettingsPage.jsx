import { useState, useEffect } from 'react'
import { fetchStats, fetchDebug, repairAllSources, repairSource } from '../lib/supabase'
import { RefreshCw, CheckCircle2, XCircle, AlertTriangle, Wrench, Zap } from 'lucide-react'

function Field({ label, value, mono = false }) {
  return (
    <div className="flex justify-between items-center py-3.5 border-b border-slate-100 last:border-0">
      <span className="text-sm text-slate-500">{label}</span>
      <span className={`text-sm text-slate-950 font-medium ${mono ? 'font-mono text-[13px]' : ''}`}>{value}</span>
    </div>
  )
}

function StatusIcon({ ok }) {
  return ok
    ? <CheckCircle2 className="w-4 h-4 text-emerald-500" strokeWidth={2.5} />
    : <XCircle className="w-4 h-4 text-red-500" strokeWidth={2.5} />
}

export default function SettingsPage({ session }) {
  const [health, setHealth] = useState(null)
  const [debug, setDebug] = useState(null)
  const [loading, setLoading] = useState(true)
  const [repairing, setRepairing] = useState(false)
  const [repairResult, setRepairResult] = useState(null)
  const [repairingSingle, setRepairingSingle] = useState(null)

  async function loadAll() {
    setLoading(true)
    const [h, d] = await Promise.all([fetchStats(), fetchDebug()])
    setHealth(h)
    setDebug(d)
    setLoading(false)
  }

  useEffect(() => { loadAll() }, [])

  async function handleRepairAll() {
    setRepairing(true)
    setRepairResult(null)
    try {
      const res = await repairAllSources()
      setRepairResult(res)
      loadAll()
    } catch (e) {
      setRepairResult({ error: e.message })
    }
    setRepairing(false)
  }

  async function handleRepairOne(name) {
    setRepairingSingle(name)
    try {
      const res = await repairSource(name)
      setRepairResult(prev => ({
        ...prev,
        results: { ...(prev?.results || {}), [name]: res },
      }))
      loadAll()
    } catch (e) {
      console.error(e)
    }
    setRepairingSingle(null)
  }

  const isOnline = health?.status === 'running'
  const checks = debug?.checks || {}
  const sources = debug?.sources || {}
  const failedSources = Object.entries(sources).filter(([, info]) => info.last_status !== 'success')

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-950 tracking-tight">Paramètres</h2>
          <p className="text-sm text-slate-500 mt-1">Configuration, diagnostic et réparation</p>
        </div>
        <div className="flex gap-2">
          <button onClick={loadAll} disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg border border-slate-200 text-sm text-slate-700 hover:border-slate-300 transition-colors disabled:opacity-50">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Actualiser
          </button>
        </div>
      </div>

      {/* Diagnostic */}
      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-lg font-semibold text-slate-950">Diagnostic services</h3>
          {debug?.error
            ? <span className="flex items-center gap-2 text-sm text-red-600"><AlertTriangle className="w-4 h-4" /> Serveur inaccessible</span>
            : <span className="flex items-center gap-2 text-sm text-slate-600">
                <span className={`w-1.5 h-1.5 rounded-full ${isOnline ? 'bg-emerald-500' : 'bg-red-500'}`} />
                {isOnline ? 'Tous services actifs' : 'Hors ligne'}
              </span>
          }
        </div>
        {debug?.error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
            {debug.error}. Vérifie que le serveur Railway est démarré.
          </div>
        ) : (
          <div className="space-y-0">
            {[
              { label: 'Base de données Supabase', ok: checks.db_connected },
              { label: 'Clé API Anthropic (Chat IA)', ok: checks.anthropic_client_loaded },
              { label: 'Email SMTP', ok: checks.smtp_user && checks.smtp_password },
              { label: 'Telegram', ok: checks.telegram_token && checks.telegram_chat_id },
            ].map(item => (
              <div key={item.label} className="flex items-center justify-between py-3 border-b border-slate-100 last:border-0">
                <span className="text-sm text-slate-700">{item.label}</span>
                <div className="flex items-center gap-2">
                  <StatusIcon ok={item.ok} />
                  <span className={`text-sm font-medium ${item.ok ? 'text-emerald-600' : 'text-red-600'}`}>
                    {item.ok ? 'Connecté' : 'Non configuré'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
        {checks.anthropic_client_loaded === false && !debug?.error && (
          <div className="mt-4 bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-800">
            L'assistant Baptiste ne fonctionne pas car <strong>ANTHROPIC_API_KEY</strong> n'est pas définie sur Railway.
            Va dans Railway → Variables → ajoute ANTHROPIC_API_KEY avec ta clé API Anthropic.
          </div>
        )}
      </div>

      {/* Sources + Repair */}
      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-lg font-semibold text-slate-950">Sources ({Object.keys(sources).length})</h3>
          <button onClick={handleRepairAll} disabled={repairing || debug?.error}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-950 text-white text-sm font-medium hover:bg-slate-800 transition-colors disabled:opacity-50">
            {repairing
              ? <><RefreshCw className="w-4 h-4 animate-spin" /> Réparation...</>
              : <><Wrench className="w-4 h-4" /> Réparer tout</>
            }
          </button>
        </div>

        {repairResult && !repairResult.error && repairResult.results && (
          <div className="mb-4 bg-slate-50 border border-slate-200 rounded-lg p-4">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">Résultat réparation</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {Object.entries(repairResult.results).map(([name, r]) => (
                <div key={name} className="flex items-center gap-2 text-sm">
                  <span className={`w-1.5 h-1.5 rounded-full ${r.status === 'ok' ? 'bg-emerald-500' : 'bg-red-500'}`} />
                  <span className="text-slate-700">{name}</span>
                  <span className="text-slate-400 font-mono text-xs">{r.missions || 0}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {Object.keys(sources).length === 0 ? (
          <p className="text-sm text-slate-400">Aucun scan encore exécuté ou serveur inaccessible</p>
        ) : (
          <div className="space-y-0">
            {Object.entries(sources)
              .sort(([,a],[,b]) => (a.last_status === 'success' ? 0 : 1) - (b.last_status === 'success' ? 0 : 1))
              .map(([name, info]) => {
                const isFailed = info.last_status !== 'success'
                const isRepairingThis = repairingSingle === name
                return (
                  <div key={name} className="flex items-center justify-between py-3 border-b border-slate-100 last:border-0 gap-3">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                        info.last_status === 'success' ? 'bg-emerald-500'
                        : info.last_status === 'error' ? 'bg-red-500'
                        : 'bg-amber-400'
                      }`} />
                      <span className="text-sm font-medium text-slate-950">{name}</span>
                      {info.last_error && (
                        <span className="text-[11px] text-red-400 truncate max-w-[180px]">{info.last_error}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <span className="text-[13px] text-slate-400 tabular-nums">
                        {info.last_scan ? new Date(info.last_scan).toLocaleString('fr-FR', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' }) : '—'}
                      </span>
                      {isFailed && (
                        <button onClick={() => handleRepairOne(name)} disabled={isRepairingThis}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium border border-slate-200 text-slate-600 hover:border-slate-950 hover:text-slate-950 transition-colors disabled:opacity-50"
                          title={`Réparer ${name}`}>
                          {isRepairingThis
                            ? <RefreshCw className="w-3 h-3 animate-spin" />
                            : <Zap className="w-3 h-3" />
                          }
                          Réparer
                        </button>
                      )}
                    </div>
                  </div>
                )
              })}
          </div>
        )}

        {failedSources.length > 0 && (
          <p className="text-[13px] text-slate-400 mt-4">
            {failedSources.length} source{failedSources.length > 1 ? 's' : ''} en erreur — le système tente automatiquement des méthodes alternatives après 3 échecs consécutifs
          </p>
        )}
      </div>

      {/* Infrastructure */}
      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-slate-950 mb-5">Infrastructure</h3>
        <div className="grid grid-cols-2 gap-x-8">
          <Field label="Statut agent" value={isOnline ? 'En ligne' : 'Hors ligne'} />
          <Field label="Uptime" value={health?.uptime || '—'} />
          <Field label="Scans réalisés" value={health?.scans_total ?? '—'} />
          <Field label="Dernier scan" value={health?.last_scan ? new Date(health.last_scan).toLocaleString('fr-FR') : '—'} />
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-slate-950 mb-5">Session</h3>
        <Field label="Utilisateur" value={session.name} />
        <Field label="Rôle" value={session.role === 'tech' ? 'Consultant' : 'Administration'} />
        <Field label="Profil de chasse" value={session.role === 'tech' ? 'Missions tech & IA' : 'Missions admin & support'} />
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-slate-950 mb-5">Configuration de l'agent</h3>
        <Field label="Score minimum proposition" value="70 / 100" />
        <Field label="Intervalle scan rapide (Tier 1)" value="5 minutes" />
        <Field label="Intervalle scan lent (Tier 2)" value="30 minutes" />
        <Field label="Sources surveillées" value="15 scrapers" />
        <Field label="Auto-réparation" value="Après 3 échecs consécutifs" />
        <Field label="Modèle de génération" value="Claude Opus 4.7" />
        <Field label="TJM consultant" value="450 EUR/jour HT" />
      </div>
    </div>
  )
}
