import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { fetchProposals, getProposalPdfUrl, getProposalPptxUrl } from '../lib/supabase'
import {
  FileText, Copy, Check, ExternalLink, Search,
  Calendar, Package, ChevronRight, ChevronDown,
  Download, Presentation, Target, Shield, Wrench,
  Clock, DollarSign, ArrowRight, Sparkles, BarChart3,
  CheckCircle2,
} from 'lucide-react'

function parsePackage(text) {
  if (!text) return null
  const match = text.match(/<!--PACKAGE_JSON:(.+?)-->/s)
  if (!match) return null
  try { return JSON.parse(match[1]) } catch { return null }
}

function SectionHeader({ icon: Icon, title, gradient = 'from-blue-500 to-blue-600' }) {
  return (
    <div className="flex items-center gap-3 mb-4">
      <div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${gradient} flex items-center justify-center shadow-sm`}>
        <Icon className="w-4.5 h-4.5 text-white" strokeWidth={2} />
      </div>
      <h3 className="text-[16px] font-bold text-slate-900 tracking-tight">{title}</h3>
    </div>
  )
}

function ToolBadge({ name }) {
  return (
    <span className="inline-flex items-center gap-1 text-[11px] font-medium bg-blue-50 text-blue-700 px-2.5 py-1 rounded-lg ring-1 ring-blue-200">
      <Wrench className="w-3 h-3" />
      {name}
    </span>
  )
}

function ProposalPreview({ pkg, proposal }) {
  const mission = proposal.missions
  const dateStr = proposal.created_at
    ? new Date(proposal.created_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
    : null

  return (
    <div className="space-y-6">
      {/* Hero Banner */}
      <div className="rounded-xl bg-gradient-to-r from-blue-600 to-violet-600 p-8 text-white shadow-md">
        <p className="text-[12px] font-medium text-blue-100 uppercase tracking-wider mb-2">Proposition de mission freelance</p>
        <h2 className="text-[22px] font-bold leading-tight">{mission?.title || pkg.title || 'Mission'}</h2>
        {(mission?.company || pkg.company) && (
          <p className="text-[14px] text-blue-100 mt-2">{mission?.company || pkg.company}</p>
        )}
        {dateStr && (
          <div className="flex items-center gap-2 mt-4 text-[12px] text-blue-200">
            <Calendar className="w-3.5 h-3.5" />
            <span>{dateStr}</span>
          </div>
        )}
      </div>

      {/* Executive Summary / Intro */}
      {pkg.intro && (
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-6">
          <SectionHeader icon={Sparkles} title="Resume executif" gradient="from-violet-500 to-violet-600" />
          <p className="text-[15px] leading-relaxed text-slate-800 font-medium">{pkg.intro}</p>
        </div>
      )}

      {/* Votre Besoin */}
      {pkg.comprehension && (
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-6">
          <SectionHeader icon={Target} title="Votre Besoin" gradient="from-rose-500 to-rose-600" />
          <p className="text-[14px] leading-relaxed text-slate-700">{pkg.comprehension}</p>
        </div>
      )}

      {/* Notre Approche */}
      {(pkg.approach || pkg.methodology) && (
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-6">
          <SectionHeader icon={ArrowRight} title="Notre Approche" gradient="from-teal-500 to-teal-600" />
          {pkg.approach && <p className="text-[14px] leading-relaxed text-slate-700 mb-3">{pkg.approach}</p>}
          {pkg.methodology && <p className="text-[14px] leading-relaxed text-slate-600">{pkg.methodology}</p>}
          {pkg.tools && pkg.tools.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-4">
              {pkg.tools.map((t, i) => <ToolBadge key={i} name={t} />)}
            </div>
          )}
        </div>
      )}

      {/* Phases - Visual Timeline */}
      {pkg.phases && pkg.phases.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-6">
          <SectionHeader icon={Clock} title="Phases du projet" gradient="from-amber-500 to-amber-600" />
          <div className="space-y-4">
            {pkg.phases.map((phase, i) => (
              <div key={i} className="relative flex gap-4">
                {/* Phase number circle */}
                <div className="flex flex-col items-center shrink-0">
                  <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white text-[14px] font-bold shadow-sm">
                    {i + 1}
                  </div>
                  {i < pkg.phases.length - 1 && (
                    <div className="w-0.5 flex-1 bg-blue-200 mt-2 mb-0" />
                  )}
                </div>
                {/* Phase content card */}
                <div className="flex-1 bg-slate-50 rounded-xl p-5 ring-1 ring-slate-200 mb-1">
                  <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                    <p className="text-[15px] font-bold text-slate-900">{phase.name}</p>
                    {phase.duration && (
                      <span className="inline-flex items-center gap-1.5 text-[11px] text-slate-500 bg-white px-2.5 py-1 rounded-lg font-medium ring-1 ring-slate-200">
                        <Calendar className="w-3 h-3" /> {phase.duration}
                      </span>
                    )}
                  </div>
                  {phase.tasks && phase.tasks.length > 0 && (
                    <ul className="text-[13px] text-slate-600 space-y-1.5 mt-2">
                      {phase.tasks.map((t, j) => (
                        <li key={j} className="flex gap-2.5">
                          <CheckCircle2 className="w-4 h-4 text-blue-500 mt-0.5 shrink-0" strokeWidth={2} />
                          <span>{t}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                  {phase.deliverable && (
                    <p className="text-[12px] text-slate-500 mt-3 pt-3 border-t border-slate-200">
                      <span className="font-bold text-slate-700">Livrable :</span> {phase.deliverable}
                    </p>
                  )}
                  {phase.tools && phase.tools.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-3">
                      {phase.tools.map((t, j) => <ToolBadge key={j} name={t} />)}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Architecture */}
      {pkg.architecture && (
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-6">
          <SectionHeader icon={Package} title="Architecture" gradient="from-indigo-500 to-indigo-600" />
          <div className="border-l-4 border-indigo-400 bg-indigo-50/60 rounded-r-xl pl-5 pr-5 py-4">
            <p className="text-[14px] leading-relaxed text-slate-800 italic">{pkg.architecture}</p>
          </div>
        </div>
      )}

      {/* Livrables */}
      {pkg.deliverables && pkg.deliverables.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-6">
          <SectionHeader icon={FileText} title="Livrables" gradient="from-emerald-500 to-emerald-600" />
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {pkg.deliverables.map((d, i) => {
              const isObject = typeof d === 'object' && d !== null
              const name = isObject ? d.name : d
              const description = isObject ? d.description : null
              const format = isObject ? d.format : null
              return (
                <div key={i} className="bg-slate-50 rounded-xl p-4 ring-1 ring-slate-200">
                  <div className="flex items-start gap-2.5">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 mt-0.5 shrink-0" strokeWidth={2} />
                    <div className="min-w-0">
                      <p className="text-[14px] font-semibold text-slate-900">{name}</p>
                      {description && <p className="text-[12px] text-slate-500 mt-1">{description}</p>}
                      {format && (
                        <span className="inline-block mt-2 text-[10px] font-medium bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-md ring-1 ring-emerald-200 uppercase">
                          {format}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* KPIs */}
      {pkg.kpis && pkg.kpis.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-6">
          <SectionHeader icon={BarChart3} title="Indicateurs de performance" gradient="from-cyan-500 to-cyan-600" />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {pkg.kpis.map((kpi, i) => {
              const isObject = typeof kpi === 'object' && kpi !== null
              const label = isObject ? (kpi.name || kpi.label) : kpi
              const value = isObject ? kpi.value : null
              const target = isObject ? kpi.target : null
              return (
                <div key={i} className="bg-cyan-50/60 rounded-xl p-4 ring-1 ring-cyan-200 text-center">
                  <BarChart3 className="w-5 h-5 text-cyan-600 mx-auto mb-2" />
                  <p className="text-[13px] font-bold text-slate-900">{label}</p>
                  {value && <p className="text-[12px] text-cyan-700 font-medium mt-1">{value}</p>}
                  {target && <p className="text-[11px] text-slate-500 mt-0.5">Cible : {target}</p>}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Investissement / Pricing */}
      {pkg.pricing && (
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-6">
          <SectionHeader icon={DollarSign} title="Investissement" gradient="from-blue-600 to-blue-700" />

          {/* Pricing breakdown table */}
          {pkg.pricing.breakdown && pkg.pricing.breakdown.length > 0 && (
            <div className="rounded-xl overflow-hidden ring-1 ring-slate-200 mb-4">
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="bg-slate-50">
                    <th className="text-left py-2.5 px-4 font-semibold text-slate-600">Poste</th>
                    <th className="text-right py-2.5 px-4 font-semibold text-slate-600">Montant</th>
                  </tr>
                </thead>
                <tbody>
                  {pkg.pricing.breakdown.map((item, i) => {
                    const isObject = typeof item === 'object' && item !== null
                    const label = isObject ? (item.label || item.name || item.phase) : item
                    const amount = isObject ? (item.amount || item.cost || item.price) : null
                    return (
                      <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}>
                        <td className="py-2.5 px-4 text-slate-700">{label}</td>
                        <td className="py-2.5 px-4 text-right font-medium text-slate-900">{amount || ''}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Total amount highlight */}
          <div className="bg-blue-50/80 rounded-xl p-5 ring-1 ring-blue-200">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div>
                <p className="text-[11px] font-bold tracking-wider text-blue-600 uppercase">Total</p>
                <p className="text-[22px] font-bold text-slate-900 mt-1">{pkg.pricing.amount || pkg.pricing.total}</p>
              </div>
              <div className="text-right">
                {pkg.pricing.model && <p className="text-[13px] text-slate-600">{pkg.pricing.model}</p>}
                {pkg.pricing.payment && <p className="text-[12px] text-slate-500 mt-0.5">{pkg.pricing.payment}</p>}
              </div>
            </div>
          </div>

          {pkg.pricing.terms && (
            <p className="text-[13px] text-slate-600 mt-3">{pkg.pricing.terms}</p>
          )}
        </div>
      )}

      {/* Timeline total */}
      {pkg.timeline && !pkg.pricing && (
        <div className="bg-slate-50 rounded-xl p-5 ring-1 ring-slate-200">
          <p className="text-[11px] font-bold tracking-wider text-slate-400 uppercase">Duree totale</p>
          <p className="text-[15px] font-bold text-slate-900 mt-1.5">{pkg.timeline}</p>
        </div>
      )}

      {/* Garanties */}
      {pkg.guarantees && pkg.guarantees.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-6">
          <SectionHeader icon={Shield} title="Garanties" gradient="from-green-500 to-green-600" />
          <ul className="space-y-2.5">
            {pkg.guarantees.map((g, i) => (
              <li key={i} className="flex items-start gap-3 text-[14px] text-slate-700">
                <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5 shrink-0" strokeWidth={2} />
                <span>{typeof g === 'object' ? g.name || g.label || JSON.stringify(g) : g}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Expected Outcome */}
      {pkg.expected_outcome && (
        <div className="border-l-[3px] border-blue-500 bg-blue-50/50 rounded-r-xl pl-5 pr-5 py-4">
          <p className="text-[11px] font-bold tracking-wider text-blue-600 uppercase mb-1">Resultat attendu</p>
          <p className="text-[14px] text-slate-800 leading-relaxed">{pkg.expected_outcome}</p>
        </div>
      )}

      {/* Prochaines Etapes */}
      {(pkg.next_step || pkg.next_steps) && (
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-6">
          <SectionHeader icon={ArrowRight} title="Prochaines Etapes" gradient="from-violet-500 to-violet-600" />
          <p className="text-[14px] leading-relaxed text-slate-700">{pkg.next_step || pkg.next_steps}</p>
        </div>
      )}

      {/* Signature */}
      {pkg.signature && (
        <div className="pt-4 border-t border-slate-200">
          <p className="text-[14px] text-slate-500 font-medium">{pkg.signature}</p>
        </div>
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
          <p className="text-sm text-slate-500 mt-1">{proposals.length} propositions generees par l'agent</p>
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
                    {mission?.score != null && <span> &middot; Score {mission.score}/100</span>}
                  </p>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  {mission?.score != null && (
                    <span className={`text-[11px] font-bold px-2 py-0.5 rounded-md ${
                      mission.score >= 80 ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200' :
                      mission.score >= 60 ? 'bg-amber-50 text-amber-700 ring-1 ring-amber-200' :
                      'bg-slate-50 text-slate-500 ring-1 ring-slate-200'
                    }`}>
                      {mission.score}
                    </span>
                  )}
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
                <div className="border-t border-slate-100">
                  <div className="px-5 pb-6 pt-6">
                    {pkg ? <ProposalPreview pkg={pkg} proposal={p} /> : (
                      <pre className="text-[14px] text-slate-700 leading-relaxed whitespace-pre-wrap font-sans">
                        {p.text?.replace(/<!--PACKAGE_JSON:.+?-->/s, '').trim()}
                      </pre>
                    )}
                  </div>

                  {/* Sticky action bar */}
                  <div className="sticky bottom-0 bg-white/95 backdrop-blur-sm border-t border-slate-200 px-5 py-3">
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <a
                        href={getProposalPdfUrl(p.id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-semibold bg-blue-600 text-white hover:bg-blue-700 shadow-sm transition-all"
                      >
                        <Download className="w-3.5 h-3.5" /> Telecharger PDF
                      </a>
                      <a
                        href={getProposalPptxUrl(p.id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-semibold bg-amber-600 text-white hover:bg-amber-700 shadow-sm transition-all"
                      >
                        <Presentation className="w-3.5 h-3.5" /> Telecharger PowerPoint
                      </a>
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
          <p className="text-[13px] text-slate-400 mt-1">L'agent genere des propositions pour les missions a fort score</p>
        </div>
      )}
    </div>
  )
}
