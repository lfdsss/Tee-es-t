import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { fetchMissions } from '../lib/supabase'
import { Search, ChevronLeft, ChevronRight } from 'lucide-react'

const TYPE_LABELS = {
  ia: 'IA', web: 'Web', data: 'Data',
  consulting: 'Conseil', design: 'Design', other: 'Autre',
}

const STATUS_LABELS = { new: 'Nouveau', proposal_ready: 'Proposition', sent: 'Envoyé', won: 'Gagné', lost: 'Perdu' }
const STATUS_DOT = {
  new: 'bg-slate-400',
  proposal_ready: 'bg-emerald-500',
  sent: 'bg-blue-500',
  won: 'bg-emerald-600',
  lost: 'bg-red-500',
}

function scoreColor(score) {
  if (score >= 80) return 'text-emerald-600'
  if (score >= 60) return 'text-blue-600'
  if (score >= 40) return 'text-amber-600'
  return 'text-slate-400'
}

function timeAgo(date) {
  if (!date) return ''
  const diff = (Date.now() - new Date(date).getTime()) / 1000
  if (diff < 3600) return `${Math.floor(diff / 60)}min`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`
  return `${Math.floor(diff / 86400)}j`
}

export default function MissionsPage() {
  const [missions, setMissions] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(0)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('all')
  const [type, setType] = useState('all')
  const [minScore, setMinScore] = useState('')
  const limit = 25

  const loadMissions = useCallback(async () => {
    setLoading(true)
    try {
      const { data, total: t } = await fetchMissions({
        limit, offset: page * limit,
        status: status !== 'all' ? status : undefined,
        minScore: minScore || undefined,
        search: search || undefined,
        type: type !== 'all' ? type : undefined,
      })
      setMissions(data || [])
      setTotal(t)
    } catch (e) { console.error(e) }
    setLoading(false)
  }, [page, status, type, minScore, search])

  useEffect(() => { loadMissions() }, [loadMissions])

  const totalPages = Math.ceil(total / limit)
  const sel = "px-3 py-2.5 border border-slate-200 rounded-lg text-sm bg-white text-slate-700 focus:outline-none focus:border-slate-400 transition-colors cursor-pointer"

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-950 tracking-tight">Missions</h2>
        <p className="text-sm text-slate-500 mt-1">{total} missions analysées par l'agent</p>
      </div>

      <div className="flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input type="text" value={search} onChange={e => { setSearch(e.target.value); setPage(0) }}
            placeholder="Rechercher une mission..."
            className="w-full pl-10 pr-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-slate-400 transition-colors placeholder:text-slate-400" />
        </div>
        <select value={status} onChange={e => { setStatus(e.target.value); setPage(0) }} className={sel}>
          <option value="all">Tous statuts</option>
          <option value="new">Nouveau</option><option value="proposal_ready">Proposition</option>
          <option value="sent">Envoyé</option><option value="won">Gagné</option><option value="lost">Perdu</option>
        </select>
        <select value={type} onChange={e => { setType(e.target.value); setPage(0) }} className={sel}>
          <option value="all">Tous types</option>
          <option value="ia">IA</option><option value="web">Web</option><option value="data">Data</option>
          <option value="consulting">Conseil</option><option value="design">Design</option>
        </select>
        <select value={minScore} onChange={e => { setMinScore(e.target.value); setPage(0) }} className={sel}>
          <option value="">Score min</option>
          <option value="80">&ge; 80</option><option value="60">&ge; 60</option><option value="40">&ge; 40</option><option value="20">&ge; 20</option>
        </select>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
        <div className="grid grid-cols-[56px_1fr_100px_100px_120px_64px] px-6 py-3 border-b border-slate-200 text-xs font-medium text-slate-400 uppercase tracking-wider">
          <span>Score</span>
          <span>Mission</span>
          <span>Type</span>
          <span>Statut</span>
          <span>Budget</span>
          <span className="text-right">Age</span>
        </div>
        {loading && <div className="px-6 py-16 text-center text-sm text-slate-400">Chargement...</div>}
        {!loading && missions.length === 0 && <div className="px-6 py-16 text-center text-sm text-slate-400">Aucune mission trouvée avec ces filtres</div>}
        {missions.map(m => {
          const t = TYPE_LABELS[m.type] || TYPE_LABELS.other
          return (
            <Link key={m.id} to={`/missions/${m.id}`} className="grid grid-cols-[56px_1fr_100px_100px_120px_64px] px-6 py-4 items-center border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors group">
              <span className={`text-sm font-bold tabular-nums ${scoreColor(m.score || 0)}`}>{m.score || 0}</span>
              <div className="min-w-0 pr-4">
                <p className="text-sm font-semibold text-slate-950 truncate group-hover:text-blue-600 transition-colors">{m.title}</p>
                <p className="text-[13px] text-slate-500 mt-0.5 truncate">{m.company || 'Non précisé'} · {m.source}</p>
              </div>
              <span className="text-sm text-slate-600">{t}</span>
              <span className="flex items-center gap-2 text-sm text-slate-600">
                <span className={`w-1.5 h-1.5 rounded-full ${STATUS_DOT[m.status] || STATUS_DOT.new}`} />
                {STATUS_LABELS[m.status] || m.status}
              </span>
              <span className="text-sm text-slate-600 font-medium">{m.budget_raw || '—'}</span>
              <span className="text-[13px] text-slate-400 tabular-nums text-right">{timeAgo(m.found_at || m.posted_at)}</span>
            </Link>
          )
        })}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2">
          <span className="text-[13px] text-slate-500">Page {page + 1} sur {totalPages} · {total} missions</span>
          <div className="flex gap-2">
            <button disabled={page === 0} onClick={() => setPage(p => p - 1)}
              className="text-sm text-slate-600 hover:text-slate-950 disabled:text-slate-300 disabled:cursor-not-allowed transition-colors">
              <ChevronLeft className="w-4 h-4 inline -mt-px" /> Précédent
            </button>
            <button disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)}
              className="text-sm text-slate-600 hover:text-slate-950 disabled:text-slate-300 disabled:cursor-not-allowed transition-colors">
              Suivant <ChevronRight className="w-4 h-4 inline -mt-px" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
