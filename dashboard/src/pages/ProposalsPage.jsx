import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { fetchProposals, getProposalPdfUrl, getProposalPptxUrl } from '../lib/supabase'
import {
  FileText, Copy, Check, ExternalLink, Search,
  ChevronRight, ChevronDown, Download, ArrowRight,
  CheckCircle2, Clock, File,
} from 'lucide-react'
import cleanText from '../lib/cleanText'

function parsePackage(text) {
  if (!text) return null
  const match = text.match(/<!--PACKAGE_JSON:(.+?)-->/s)
  if (!match) return null
  try { return JSON.parse(match[1]) } catch { return null }
}

function ProposalPreview({ pkg, proposal }) {
  const mission = proposal.missions
  const dateStr = proposal.created_at
    ? new Date(proposal.created_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
    : null

  return (
    <div className="space-y-8">
      {/* Download bar — FIRST, unmissable */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <a href={getProposalPdfUrl(proposal.id)} target="_blank" rel="noopener noreferrer"
          className="group flex items-center gap-4 p-5 border border-slate-200 rounded-lg hover:border-slate-950 transition-colors">
          <div className="w-12 h-12 rounded-lg bg-red-50 flex items-center justify-center shrink-0">
            <span className="text-sm font-bold font-mono text-red-600">PDF</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-slate-950">Proposition complète</p>
            <p className="text-xs text-slate-400 mt-0.5">Document formel avec devis</p>
          </div>
          <Download className="w-4 h-4 text-slate-300 group-hover:text-slate-950 transition-colors shrink-0" />
        </a>
        <a href={getProposalPptxUrl(proposal.id)} target="_blank" rel="noopener noreferrer"
          className="group flex items-center gap-4 p-5 border border-slate-200 rounded-lg hover:border-slate-950 transition-colors">
          <div className="w-12 h-12 rounded-lg bg-orange-50 flex items-center justify-center shrink-0">
            <span className="text-sm font-bold font-mono text-orange-600">PPTX</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-slate-950">Présentation 10 pages</p>
            <p className="text-xs text-slate-400 mt-0.5">PowerPoint client</p>
          </div>
          <Download className="w-4 h-4 text-slate-300 group-hover:text-slate-950 transition-colors shrink-0" />
        </a>
        {proposal.mission_id && (
          <Link to={`/missions/${proposal.mission_id}`}
            className="group flex items-center gap-4 p-5 border border-slate-200 rounded-lg hover:border-slate-950 transition-colors">
            <div className="w-12 h-12 rounded-lg bg-slate-50 flex items-center justify-center shrink-0">
              <ExternalLink className="w-5 h-5 text-slate-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-slate-950">Voir la mission</p>
              <p className="text-xs text-slate-400 mt-0.5">Détails et pipeline</p>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-slate-950 transition-colors shrink-0" />
          </Link>
        )}
      </div>

      {/* Header */}
      <div className="border-b border-slate-200 pb-6">
        <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Proposition de mission</p>
        <h2 className="text-xl font-bold text-slate-950 mt-2 leading-tight">{cleanText(mission?.title) || 'Mission'}</h2>
        <div className="flex items-center gap-3 mt-2 text-sm text-slate-500">
          {(mission?.company) && <span>{cleanText(mission.company)}</span>}
          {dateStr && <><span className="text-slate-300">—</span><span>{dateStr}</span></>}
        </div>
      </div>

      {/* Executive summary */}
      {(pkg.executive_summary || pkg.intro) && (
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">Résumé</p>
          <p className="text-base leading-relaxed text-slate-700">{pkg.executive_summary || pkg.intro}</p>
        </div>
      )}

      {/* Two-column: Besoin + Approche */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {pkg.comprehension && (
          <div className="border-l-2 border-slate-200 pl-5">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">Votre besoin</p>
            <p className="text-sm leading-relaxed text-slate-700">{pkg.comprehension}</p>
          </div>
        )}
        {pkg.approach && (
          <div className="border-l-2 border-slate-950 pl-5">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">Notre approche</p>
            <p className="text-sm leading-relaxed text-slate-700">{pkg.approach}</p>
            {pkg.methodology && <p className="text-sm text-slate-500 mt-2">{pkg.methodology}</p>}
          </div>
        )}
      </div>

      {/* Tools */}
      {pkg.tools_used && pkg.tools_used.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {pkg.tools_used.map((t, i) => (
            <span key={i} className="text-xs font-mono font-medium text-slate-500 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded">{t}</span>
          ))}
        </div>
      )}

      {/* Phases */}
      {pkg.phases && pkg.phases.length > 0 && (
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-4">Phases</p>
          <div className="space-y-0">
            {pkg.phases.map((phase, i) => (
              <div key={i} className="flex gap-5 group">
                {/* Timeline indicator */}
                <div className="flex flex-col items-center shrink-0 pt-1">
                  <div className="w-8 h-8 rounded-full border-2 border-slate-950 flex items-center justify-center text-xs font-bold font-mono text-slate-950">
                    {i + 1}
                  </div>
                  {i < pkg.phases.length - 1 && <div className="w-px flex-1 bg-slate-200 mt-1" />}
                </div>
                {/* Content */}
                <div className="flex-1 pb-8">
                  <div className="flex items-baseline justify-between gap-3 flex-wrap">
                    <h4 className="text-sm font-bold text-slate-950">{phase.name}</h4>
                    {phase.duration && <span className="text-xs font-mono text-slate-400">{phase.duration}</span>}
                  </div>
                  {phase.objective && <p className="text-sm text-slate-600 mt-1">{phase.objective}</p>}
                  {phase.tasks && phase.tasks.length > 0 && (
                    <ul className="mt-3 space-y-1.5">
                      {phase.tasks.map((t, j) => (
                        <li key={j} className="flex gap-2 text-sm text-slate-600">
                          <span className="text-slate-300 mt-0.5 shrink-0">—</span>
                          <span>{t}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                  {phase.deliverable && (
                    <p className="text-xs text-slate-400 mt-3">
                      Livrable : <span className="text-slate-600">{phase.deliverable}</span>
                    </p>
                  )}
                  {phase.tools && phase.tools.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {phase.tools.map((t, j) => (
                        <span key={j} className="text-[11px] font-mono text-slate-400 bg-slate-50 px-2 py-0.5 rounded">{t}</span>
                      ))}
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
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-6">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">Architecture</p>
          <p className="text-sm leading-relaxed text-slate-700">{pkg.architecture}</p>
        </div>
      )}

      {/* Livrables */}
      {pkg.deliverables && pkg.deliverables.length > 0 && (
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-4">Livrables</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {pkg.deliverables.map((d, i) => {
              const isObj = typeof d === 'object' && d !== null
              const name = isObj ? d.name : d
              const desc = isObj ? d.description : null
              const fmt = isObj ? d.format : null
              return (
                <div key={i} className="flex items-start gap-3 p-4 border border-slate-200 rounded-lg">
                  <CheckCircle2 className="w-4 h-4 text-slate-950 mt-0.5 shrink-0" strokeWidth={2.5} />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-slate-950">{name}</p>
                    {desc && <p className="text-xs text-slate-500 mt-1">{desc}</p>}
                    {fmt && <span className="inline-block mt-1.5 text-[10px] font-mono font-medium text-slate-400 uppercase">{fmt}</span>}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* KPIs + Timeline row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {pkg.timeline && (
          <div className="p-4 border border-slate-200 rounded-lg">
            <p className="text-[10px] font-medium text-slate-400 uppercase tracking-wider">Durée</p>
            <p className="text-lg font-bold font-mono text-slate-950 mt-1">{pkg.timeline}</p>
          </div>
        )}
        {pkg.kpis && pkg.kpis.map((kpi, i) => (
          <div key={i} className="p-4 border border-slate-200 rounded-lg">
            <p className="text-[10px] font-medium text-slate-400 uppercase tracking-wider">KPI {i + 1}</p>
            <p className="text-sm font-medium text-slate-950 mt-1">{typeof kpi === 'object' ? (kpi.name || kpi.label) : kpi}</p>
          </div>
        ))}
      </div>

      {/* Pricing */}
      {pkg.pricing && (
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-4">Investissement</p>
          {pkg.pricing.detail && pkg.pricing.detail.length > 0 && (
            <div className="border border-slate-200 rounded-lg overflow-hidden mb-4">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-3 px-4 font-medium text-slate-400 text-xs uppercase tracking-wider">Poste</th>
                    <th className="text-right py-3 px-4 font-medium text-slate-400 text-xs uppercase tracking-wider">Jours</th>
                    <th className="text-right py-3 px-4 font-medium text-slate-400 text-xs uppercase tracking-wider">Montant</th>
                  </tr>
                </thead>
                <tbody>
                  {pkg.pricing.detail.map((item, i) => (
                    <tr key={i} className="border-b border-slate-100 last:border-0">
                      <td className="py-3 px-4 text-slate-700">{item.item}</td>
                      <td className="py-3 px-4 text-right font-mono text-slate-500">{item.days}</td>
                      <td className="py-3 px-4 text-right font-mono font-medium text-slate-950">{item.amount}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="flex items-baseline justify-between p-5 bg-slate-950 rounded-lg text-white">
            <div>
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total</p>
              <p className="text-2xl font-bold font-mono mt-1">{pkg.pricing.amount}</p>
            </div>
            <div className="text-right">
              {pkg.pricing.model && <p className="text-sm text-slate-400">{pkg.pricing.model}</p>}
              {pkg.pricing.payment && <p className="text-xs text-slate-500 mt-1">{pkg.pricing.payment}</p>}
            </div>
          </div>
        </div>
      )}

      {/* Garanties */}
      {pkg.guarantees && pkg.guarantees.length > 0 && (
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">Garanties</p>
          <div className="space-y-2">
            {pkg.guarantees.map((g, i) => (
              <div key={i} className="flex items-start gap-3 text-sm text-slate-700">
                <Check className="w-4 h-4 text-slate-950 mt-0.5 shrink-0" strokeWidth={2.5} />
                <span>{typeof g === 'object' ? g.name || g.label : g}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Expected outcome */}
      {pkg.expected_outcome && (
        <div className="border-l-2 border-slate-950 pl-5 py-1">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">Résultat attendu</p>
          <p className="text-sm leading-relaxed text-slate-700">{pkg.expected_outcome}</p>
        </div>
      )}

      {/* Next step */}
      {pkg.next_step && (
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-5">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">Prochaine étape</p>
          <p className="text-sm text-slate-700">{pkg.next_step}</p>
        </div>
      )}

      {/* Signature */}
      {pkg.signature && (
        <p className="text-sm text-slate-400 pt-4 border-t border-slate-200">{pkg.signature}</p>
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
    <div className="space-y-8">
      <div className="flex items-baseline justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-950 tracking-tight">Propositions</h2>
          <p className="text-sm text-slate-400 mt-1 font-mono">{proposals.length} générées</p>
        </div>
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-300" />
          <input type="text" value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Rechercher..."
            className="w-full pl-10 pr-3 py-2.5 rounded-lg border border-slate-200 text-sm bg-white focus:border-slate-950 transition-colors placeholder:text-slate-300" />
        </div>
      </div>

      {loading && <div className="text-center py-20 text-sm text-slate-300">Chargement...</div>}

      <div className="space-y-4">
        {filtered.map(p => {
          const mission = p.missions
          const pkg = parsePackage(p.text)
          const isOpen = expanded[p.id]
          return (
            <div key={p.id} className="border border-slate-200 rounded-lg overflow-hidden">
              {/* Collapsed header */}
              <button onClick={() => toggle(p.id)}
                className="w-full flex items-center gap-5 px-6 py-5 text-left hover:bg-slate-50 transition-colors">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-slate-950 truncate">{cleanText(mission?.title) || 'Mission'}</p>
                  <p className="text-xs text-slate-400 mt-1">
                    {cleanText(mission?.company) || '—'} <span className="text-slate-200 mx-1">|</span> {cleanText(mission?.source) || ''}
                  </p>
                </div>
                <div className="flex items-center gap-4 shrink-0">
                  {mission?.score != null && (
                    <span className={`text-sm font-bold font-mono ${
                      mission.score >= 80 ? 'text-emerald-600' : mission.score >= 60 ? 'text-amber-600' : 'text-slate-400'
                    }`}>{mission.score}</span>
                  )}
                  <span className="flex items-center gap-1.5 text-xs text-slate-400">
                    <span className={`w-1.5 h-1.5 rounded-full ${
                      p.status === 'ready' ? 'bg-emerald-500' : p.status === 'sent' ? 'bg-blue-500' : 'bg-slate-300'
                    }`} />
                    {p.status === 'ready' ? 'Prête' : p.status === 'sent' ? 'Envoyée' : 'Brouillon'}
                  </span>
                  {isOpen
                    ? <ChevronDown className="w-4 h-4 text-slate-300" />
                    : <ChevronRight className="w-4 h-4 text-slate-300" />
                  }
                </div>
              </button>

              {/* Expanded content */}
              {isOpen && (
                <div className="border-t border-slate-200 px-6 py-8">
                  {pkg ? <ProposalPreview pkg={pkg} proposal={p} /> : (
                    <pre className="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap font-sans">
                      {p.text?.replace(/<!--PACKAGE_JSON:.+?-->/s, '').trim()}
                    </pre>
                  )}

                  {/* Bottom copy button */}
                  <div className="mt-8 pt-6 border-t border-slate-200">
                    <button onClick={(e) => { e.stopPropagation(); copyText(p.text, p.id) }}
                      className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-500 hover:text-slate-950 transition-colors">
                      {copiedId === p.id ? <><Check className="w-4 h-4 text-emerald-600" /> Copié dans le presse-papier</> : <><Copy className="w-4 h-4" /> Copier le texte brut</>}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {!loading && filtered.length === 0 && (
        <div className="py-20 text-center">
          <p className="text-sm text-slate-400">Aucune proposition</p>
          <p className="text-xs text-slate-300 mt-1">L'agent génère des propositions pour les missions à fort score</p>
        </div>
      )}
    </div>
  )
}
