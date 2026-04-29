import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { fetchMissions } from '../lib/supabase'
import { Search, ChevronLeft, ChevronRight, Clock, SlidersHorizontal } from 'lucide-react'

function ScoreBadge({ score }) {
  const cls = score >= 80 ? 'text-emerald-700 bg-emerald-50 ring-emerald-600/10'
    : score >= 60 ? 'text-blue-700 bg-blue-50 ring-blue-600/10'
    : score >= 40 ? 'text-amber-700 bg-amber-50 ring-amber-600/10'
    : 'text-slate-600 bg-slate-50 ring-slate-500/10'
  return <span className={`inline-flex items-center justify-center w-10 h-7 rounded-md text-[11px] font-bold tabular-nums ring-1 ${cls}`}>{score}</span>
}

const TYPE_LABELS = {
  ia: { label: 'IA', cls: 'bg-violet-50 text-violet-700 ring-violet-600/10' },
  web: { label: 'Web', cls: 'bg-blue-50 text-blue-700 ring-blue-600/10' },
  data: { label: 'Data', cls: 'bg-cyan-50 text-cyan-700 ring-cyan-600/10' },
  consulting: { label: 'Conseil', cls: 'bg-amber-50 text-amber-700 ring-amber-600/10' },
  design: { label: 'Design', cls: 'bg-pink-50 text-pink-700 ring-pink-600/10' },
  other: { label: 'Autre', cls: 'bg-slate-50 text-slate-600 ring-slate-500/10' },
}

const STATUS_LABELS = { new: 'Nouveau', proposal_ready: 'Proposition', sent: 'Envoye', won: 'Gagne', lost: 'Perdu' }
const STATUS_CLS = {
  new: 'bg-slate-50 text-slate-600 ring-slate-500/10',
  proposal_ready: 'bg-emerald-50 text-emerald-700 ring-emerald-600/10',
  sent: 'bg-blue-50 text-blue-700 ring-blue-600/10',
  won: 'bg-emerald-100 text-emerald-800 ring-emerald-600/10',
  lost: 'bg-red-50 text-red-600 ring-red-600/10',
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
  const sel = "px-3 py-2 rounded-lg border border-slate-200 text-[13px] bg-white font-medium text-slate-700 focus:ring-2 focus:ring-blue-600 focus:border-blue-600 transition-shadow cursor-pointer"

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Missions</h2>
        <p className="text-sm text-slate-500 mt-1">{total} missions analysees par l'agent</p>
      </div>

      <div className="bg-white rounded-xl border border-slate-200/80 p-3 flex flex-wrap gap-2.5 items-center shadow-sm">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input type="text" value={search} onChange={e => { setSearch(e.target.value); setPage(0) }}
            placeholder="Rechercher une mission..."
            className="w-full pl-10 pr-3 py-2 rounded-lg border border-slate-200 text-[13px] focus:ring-2 focus:ring-blue-600 focus:border-blue-600 transition-shadow placeholder:text-slate-400" />
        </div>
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="w-4 h-4 text-slate-400 hidden sm:block" />
          <select value={status} onChange={e => { setStatus(e.target.value); setPage(0) }} className={sel}>
            <option value="all">Tous statuts</option>
            <option value="new">Nouveau</option><option value="proposal_ready">Proposition</option>
            <option value="sent">Envoye</option><option value="won">Gagne</option><option value="lost">Perdu</option>
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
      </div>

      <div className="bg-white rounded-xl border border-slate-200/80 overflow-hidden shadow-sm">
        {loading && <div className="px-5 py-16 text-center text-sm text-slate-400">Chargement...</div>}
        {!loading && missions.length === 0 && <div className="px-5 py-16 text-center text-sm text-slate-400">Aucune mission trouvee avec ces filtres</div>}
        <div className="divide-y divide-slate-100/80">
          {missions.map(m => {
            const t = TYPE_LABELS[m.type] || TYPE_LABELS.other
            return (
              <Link key={m.id} to={`/missions/${m.id}`} className="flex items-center gap-4 px-5 py-3.5 hover:bg-slate-50/80 transition-colors group">
                <ScoreBadge score={m.score || 0} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <p className="text-[13px] font-semibold text-slate-900 truncate group-hover:text-blue-600 transition-colors">{m.title}</p>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-md ring-1 ${t.cls}`}>{t.label}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1 text-[12px] text-slate-500">
                    <span>{m.company || 'Non precise'}</span>
                    <span className="text-slate-300">&middot;</span>
                    <span>{m.source}</span>
                    {m.budget_raw && <><span className="text-slate-300">&middot;</span><span className="text-slate-700 font-semibold">{m.budget_raw}</span></>}
                    {m.remote && <span className="text-[10px] text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded font-medium">Remote</span>}
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-md ring-1 ${STATUS_CLS[m.status] || STATUS_CLS.new}`}>{STATUS_LABELS[m.status] || m.status}</span>
                  <span className="text-[11px] text-slate-400 inline-flex items-center gap-1 tabular-nums w-10 justify-end font-medium">
                    <Clock className="w-3 h-3" /> {timeAgo(m.found_at || m.posted_at)}
                  </span>
                </div>
              </Link>
            )
          })}
        </div>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between bg-white rounded-xl border border-slate-200/80 px-5 py-3 shadow-sm">
          <span className="text-[13px] text-slate-500 font-medium">Page {page + 1} sur {totalPages} &middot; {total} missions</span>
          <div className="flex gap-1.5">
            <button disabled={page === 0} onClick={() => setPage(p => p - 1)} className="p-2 rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50 disabled:opacity-30 disabled:cursor-not-allowed transition-all"><ChevronLeft className="w-4 h-4" /></button>
            <button disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)} className="p-2 rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50 disabled:opacity-30 disabled:cursor-not-allowed transition-all"><ChevronRight className="w-4 h-4" /></button>
          </div>
        </div>
      )}
    </div>
  )
}
