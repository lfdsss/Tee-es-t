import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { fetchProposals } from '../lib/supabase'
import {
  FileText, Copy, Check, ExternalLink, Search,
  Calendar, Package, ChevronRight, ChevronDown,
} from 'lucide-react'

function parsePackage(text) {
  if (!text) return null
  const match = text.match(/<!--PACKAGE_JSON:(.+?)-->/s)
  if (!match) return null
  try { return JSON.parse(match[1]) } catch { return null }
}

function PackagingView({ pkg }) {
  return (
    <div className="space-y-6">
      {pkg.intro && <p className="text-[15px] leading-relaxed text-slate-800 font-medium">{pkg.intro}</p>}

      {pkg.comprehension && (
        <div>
          <p className="text-[11px] font-bold tracking-wider text-slate-400 uppercase mb-2">Votre besoin</p>
          <p className="text-[14px] leading-relaxed text-slate-700">{pkg.comprehension}</p>
        </div>
      )}

      {pkg.approach && (
        <div>
          <p className="text-[11px] font-bold tracking-wider text-slate-400 uppercase mb-2">Approche</p>
          <p className="text-[14px] leading-relaxed text-slate-700">{pkg.approach}</p>
        </div>
      )}

      {pkg.phases && pkg.phases.length > 0 && (
        <div>
          <p className="text-[11px] font-bold tracking-wider text-slate-400 uppercase mb-3">Phases</p>
          <div className="space-y-3">
            {pkg.phases.map((p, i) => (
              <div key={i} className="border border-slate-200 rounded-xl p-4 hover:border-slate-300 transition-colors">
                <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                  <p className="text-[14px] font-bold text-slate-900">{p.name}</p>
                  {p.duration && (
                    <span className="inline-flex items-center gap-1.5 text-[11px] text-slate-500 bg-slate-50 px-2.5 py-1 rounded-lg font-medium ring-1 ring-slate-200">
                      <Calendar className="w-3 h-3" /> {p.duration}
                    </span>
                  )}
                </div>
                {p.tasks && p.tasks.length > 0 && (
                  <ul className="text-[13px] text-slate-600 space-y-1 mt-2">
                    {p.tasks.map((t, j) => (
                      <li key={j} className="flex gap-2.5"><span className="text-slate-300 mt-0.5">&#8226;</span><span>{t}</span></li>
                    ))}
                  </ul>
                )}
                {p.deliverable && (
                  <p className="text-[12px] text-slate-500 mt-3 pt-3 border-t border-slate-100">
                    <span className="font-bold text-slate-700">Livrable :</span> {p.deliverable}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {pkg.timeline && (
          <div className="bg-slate-50 rounded-xl p-4 ring-1 ring-slate-200">
            <p className="text-[11px] font-bold tracking-wider text-slate-400 uppercase">Duree totale</p>
            <p className="text-[15px] font-bold text-slate-900 mt-1.5">{pkg.timeline}</p>
          </div>
        )}
        {pkg.pricing && (
          <div className="bg-blue-50/60 rounded-xl p-4 ring-1 ring-blue-200">
            <p className="text-[11px] font-bold tracking-wider text-blue-500 uppercase">Tarification</p>
            <p className="text-[15px] font-bold text-slate-900 mt-1.5">{pkg.pricing.amount}</p>
            <p className="text-[12px] text-slate-600 mt-0.5">{pkg.pricing.model} &middot; {pkg.pricing.payment}</p>
          </div>
        )}
      </div>

      {pkg.deliverables && pkg.deliverables.length > 0 && (
        <div>
          <p className="text-[11px] font-bold tracking-wider text-slate-400 uppercase mb-2.5">Livrables finaux</p>
          <ul className="space-y-1.5">
            {pkg.deliverables.map((d, i) => (
              <li key={i} className="flex items-start gap-2.5 text-[14px] text-slate-700">
                <Check className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" strokeWidth={2.5} />
                <span>{d}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {pkg.expected_outcome && (
        <div className="border-l-[3px] border-blue-500 bg-blue-50/50 rounded-r-lg pl-4 pr-4 py-3">
          <p className="text-[11px] font-bold tracking-wider text-blue-600 uppercase mb-1">Resultat attendu</p>
          <p className="text-[14px] text-slate-800 leading-relaxed">{pkg.expected_outcome}</p>
        </div>
      )}

      {pkg.next_step && (
        <div>
          <p className="text-[11px] font-bold tracking-wider text-slate-400 uppercase mb-2">Prochaine etape</p>
          <p className="text-[14px] text-slate-700">{pkg.next_step}</p>
        </div>
      )}

      {pkg.signature && (
        <p className="text-[14px] text-slate-500 pt-4 border-t border-slate-100 font-medium">{pkg.signature}</p>
      )}
    </div>
  )
}

export default function ProposalsPage() {
  const [proposals, setProposals] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [copiedId, setCopiedId] = useState(null)
  const [expanded, setExpanded] = useState({})

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const data = await fetchProposals({ limit: 50 })
        setProposals(data || [])
      } catch (e) { console.error(e) }
      setLoading(false)
    }
    load()
  }, [])

  function copyText(text, id) {
    const cleanText = text.replace(/<!--PACKAGE_JSON:.+?-->/s, '').trim()
    navigator.clipboard.writeText(cleanText)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  function toggle(id) { setExpanded(e => ({ ...e, [id]: !e[id] })) }

  const filtered = useMemo(() => {
    if (!search) return proposals
    const q = search.toLowerCase()
    return proposals.filter(p => {
      const m = p.missions
      return m?.title?.toLowerCase().includes(q) || m?.company?.toLowerCase().includes(q) || p.text?.toLowerCase().includes(q)
    })
  }, [proposals, search])

  return (
    <div className="space-y-5">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Propositions</h2>
          <p className="text-sm text-slate-500 mt-1">{proposals.length} packages generes par l'agent</p>
        </div>
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input type="text" value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Rechercher..."
            className="w-full pl-10 pr-3 py-2 rounded-lg border border-slate-200 text-[13px] bg-white focus:ring-2 focus:ring-blue-600 focus:border-blue-600 transition-shadow shadow-sm placeholder:text-slate-400" />
        </div>
      </div>

      {loading && <div className="text-center py-16 text-sm text-slate-400">Chargement...</div>}

      <div className="space-y-3">
        {filtered.map(p => {
          const mission = p.missions
          const pkg = parsePackage(p.text)
          const isOpen = expanded[p.id]
          return (
            <div key={p.id} className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden">
              <button onClick={() => toggle(p.id)}
                className="w-full flex items-center gap-4 px-5 py-4 text-left hover:bg-slate-50/80 transition-colors">
                <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-violet-500 to-violet-600 flex items-center justify-center shrink-0 shadow-sm">
                  <Package className="w-4 h-4 text-white" strokeWidth={2} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[14px] font-bold text-slate-900 truncate">{mission?.title || 'Mission'}</p>
                  <p className="text-[12px] text-slate-500 mt-0.5">
                    {mission?.company || 'Non precise'} &middot; {mission?.source || ''}
                    {mission?.score && ` &middot; Score ${mission.score}/100`}
                  </p>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-md ring-1 ${
                    p.status === 'ready' ? 'bg-emerald-50 text-emerald-700 ring-emerald-600/10' :
                    p.status === 'sent' ? 'bg-blue-50 text-blue-700 ring-blue-600/10' :
                    'bg-slate-50 text-slate-500 ring-slate-400/10'
                  }`}>
                    {p.status === 'ready' ? 'Prete' : p.status === 'sent' ? 'Envoyee' : 'Brouillon'}
                  </span>
                  {isOpen ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                </div>
              </button>

              {isOpen && (
                <div className="px-5 pb-6 border-t border-slate-100 pt-6">
                  {pkg ? <PackagingView pkg={pkg} /> : (
                    <pre className="text-[14px] text-slate-700 leading-relaxed whitespace-pre-wrap font-sans">
                      {p.text?.replace(/<!--PACKAGE_JSON:.+?-->/s, '').trim()}
                    </pre>
                  )}
                  <div className="flex items-center gap-2.5 mt-6 pt-5 border-t border-slate-100">
                    <button onClick={(e) => { e.stopPropagation(); copyText(p.text, p.id) }}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 shadow-sm transition-all">
                      {copiedId === p.id ? <><Check className="w-3.5 h-3.5 text-emerald-600" /> Copie</> : <><Copy className="w-3.5 h-3.5" /> Copier le texte</>}
                    </button>
                    {p.mission_id && (
                      <Link to={`/missions/${p.mission_id}`}
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 shadow-sm transition-all">
                        <ExternalLink className="w-3.5 h-3.5" /> Voir la mission
                      </Link>
                    )}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {!loading && filtered.length === 0 && (
        <div className="bg-white rounded-xl border border-slate-200/80 p-16 text-center shadow-sm">
          <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto mb-4">
            <Package className="w-7 h-7 text-slate-400" strokeWidth={1.5} />
          </div>
          <p className="text-[15px] font-semibold text-slate-700">Aucune proposition</p>
          <p className="text-[13px] text-slate-400 mt-1">L'agent genere des packages pour les missions a fort score</p>
        </div>
      )}
    </div>
  )
}
