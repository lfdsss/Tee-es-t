import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchMission, fetchProposals, updateMission, getDevisUrl } from '../lib/supabase'
import {
  ArrowLeft, ExternalLink, Download, Send,
  CheckCircle2, XCircle, Clock, FileText,
  Building2, MapPin, Tag, Globe,
} from 'lucide-react'

function parsePackage(text) {
  if (!text) return null
  const match = text.match(/<!--PACKAGE_JSON:(.+?)-->/s)
  if (!match) return null
  try { return JSON.parse(match[1]) } catch { return null }
}

const STATUS_FLOW = [
  { key: 'new', label: 'Nouveau', icon: Clock },
  { key: 'proposal_ready', label: 'Proposition', icon: FileText },
  { key: 'sent', label: 'Envoye', icon: Send },
  { key: 'won', label: 'Gagne', icon: CheckCircle2 },
]

export default function MissionDetailPage() {
  const { id } = useParams()
  const [mission, setMission] = useState(null)
  const [proposals, setProposals] = useState([])
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(false)

  useEffect(() => {
    async function load() {
      setLoading(true)
      const [m, p] = await Promise.all([fetchMission(id), fetchProposals({ missionId: id })])
      setMission(m)
      setProposals(p || [])
      setLoading(false)
    }
    load()
  }, [id])

  async function setStatus(status) {
    if (updating) return
    setUpdating(true)
    try {
      await updateMission(id, { status })
      setMission(prev => ({ ...prev, status }))
    } finally { setUpdating(false) }
  }

  if (loading) return <div className="text-center py-20 text-sm text-slate-400">Chargement...</div>
  if (!mission) return <div className="text-center py-20 text-sm text-slate-400">Mission introuvable</div>

  const currentStep = STATUS_FLOW.findIndex(s => s.key === mission.status)
  const score = mission.score || 0
  const scoreCls = score >= 80 ? 'text-emerald-700 bg-emerald-50 ring-emerald-600/10'
    : score >= 60 ? 'text-blue-700 bg-blue-50 ring-blue-600/10'
    : score >= 40 ? 'text-amber-700 bg-amber-50 ring-amber-600/10'
    : 'text-slate-600 bg-slate-50 ring-slate-500/10'

  const proposal = proposals[0]
  const pkg = proposal ? parsePackage(proposal.text) : null

  return (
    <div className="space-y-5 max-w-5xl">
      <Link to="/missions" className="inline-flex items-center gap-1.5 text-[13px] text-slate-500 hover:text-slate-900 font-medium transition-colors">
        <ArrowLeft className="w-4 h-4" /> Retour aux missions
      </Link>

      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2.5 mb-3 flex-wrap">
              <span className={`inline-flex items-center px-3 py-1.5 rounded-lg text-[13px] font-bold ring-1 tabular-nums ${scoreCls}`}>
                Score {score}/100
              </span>
              {mission.type && <span className="text-[11px] font-semibold px-2.5 py-1 rounded-md bg-slate-50 ring-1 ring-slate-200 text-slate-600 capitalize">{mission.type}</span>}
              {mission.remote && <span className="text-[11px] font-semibold px-2.5 py-1 rounded-md bg-emerald-50 ring-1 ring-emerald-200 text-emerald-700">Remote</span>}
            </div>
            <h2 className="text-xl font-bold text-slate-900 leading-tight tracking-tight">{mission.title}</h2>
            <div className="flex flex-wrap items-center gap-4 mt-3 text-[13px] text-slate-500">
              <span className="inline-flex items-center gap-1.5 font-medium"><Building2 className="w-3.5 h-3.5 text-slate-400" /> {mission.company || 'Non precise'}</span>
              <span className="inline-flex items-center gap-1.5"><Globe className="w-3.5 h-3.5 text-slate-400" /> {mission.source}</span>
              {mission.budget_raw && <span className="font-bold text-slate-800">{mission.budget_raw}</span>}
            </div>
          </div>
          <div className="flex flex-wrap gap-2 shrink-0">
            {mission.source_url && (
              <a href={mission.source_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 text-white text-[13px] font-semibold hover:bg-blue-700 transition-all shadow-sm shadow-blue-600/25">
                <ExternalLink className="w-3.5 h-3.5" /> Voir l'offre
              </a>
            )}
            <a href={getDevisUrl(mission.id)} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-white border border-slate-200 text-[13px] font-semibold text-slate-700 hover:bg-slate-50 transition-all shadow-sm">
              <Download className="w-3.5 h-3.5" /> Devis
            </a>
          </div>
        </div>

        <div className="pt-5 border-t border-slate-100">
          <p className="text-[11px] font-bold tracking-wider text-slate-400 uppercase mb-3">Pipeline</p>
          <div className="flex items-center gap-2 flex-wrap">
            {STATUS_FLOW.map((step, i) => {
              const Icon = step.icon
              const isActive = step.key === mission.status
              const isPast = i <= currentStep
              return (
                <button key={step.key} onClick={() => setStatus(step.key)} disabled={updating}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-[13px] font-semibold transition-all disabled:opacity-50 ${
                    isActive ? 'bg-slate-900 text-white shadow-sm' :
                    isPast ? 'bg-slate-100 text-slate-700' :
                    'bg-white text-slate-400 border border-slate-200 hover:bg-slate-50 hover:text-slate-600'
                  }`}>
                  <Icon className="w-3.5 h-3.5" strokeWidth={2} /> {step.label}
                </button>
              )
            })}
            <button onClick={() => setStatus('lost')} disabled={updating}
              className={`ml-auto flex items-center gap-2 px-3.5 py-2 rounded-lg text-[13px] font-semibold transition-all disabled:opacity-50 ${
                mission.status === 'lost' ? 'bg-red-600 text-white shadow-sm' :
                'bg-white text-slate-400 border border-slate-200 hover:bg-red-50 hover:text-red-600 hover:border-red-200'
              }`}>
              <XCircle className="w-3.5 h-3.5" /> Perdu
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
        <h3 className="text-[15px] font-bold text-slate-900 mb-4">Description du besoin</h3>
        <div className="text-[14px] text-slate-700 leading-relaxed whitespace-pre-wrap max-h-[400px] overflow-y-auto">
          {mission.description || 'Pas de description disponible.'}
        </div>
        {mission.tags && mission.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-5 pt-5 border-t border-slate-100">
            {mission.tags.map((tag, i) => (
              <span key={i} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-50 ring-1 ring-slate-200 text-[11px] font-medium text-slate-600">
                <Tag className="w-2.5 h-2.5" /> {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {proposal && (
        <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-[15px] font-bold text-slate-900">Package de proposition</h3>
            <Link to="/proposals" className="text-[12px] text-blue-600 hover:text-blue-700 font-semibold inline-flex items-center gap-1">
              Toutes les propositions <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
          {pkg ? (
            <div className="space-y-5">
              {pkg.intro && <p className="text-[15px] leading-relaxed text-slate-800 font-medium">{pkg.intro}</p>}
              {pkg.phases && pkg.phases.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {pkg.phases.map((p, i) => (
                    <div key={i} className="border border-slate-200 rounded-xl p-4 hover:border-slate-300 transition-colors">
                      <p className="text-[13px] font-bold text-slate-900">{p.name}</p>
                      <p className="text-[11px] text-slate-400 mt-0.5 font-medium">{p.duration}</p>
                    </div>
                  ))}
                </div>
              )}
              {pkg.expected_outcome && (
                <div className="border-l-[3px] border-blue-500 bg-blue-50/50 rounded-r-lg pl-4 pr-4 py-3">
                  <p className="text-[11px] font-bold tracking-wider text-blue-600 uppercase mb-1">Resultat attendu</p>
                  <p className="text-[14px] text-slate-800 leading-relaxed">{pkg.expected_outcome}</p>
                </div>
              )}
              <Link to="/proposals" className="inline-flex items-center gap-2 text-[13px] font-semibold text-blue-600 hover:text-blue-700 transition-colors">
                Voir le package complet <ExternalLink className="w-3.5 h-3.5" />
              </Link>
            </div>
          ) : (
            <pre className="text-[14px] text-slate-700 leading-relaxed whitespace-pre-wrap font-sans max-h-[300px] overflow-y-auto">
              {proposal.text?.replace(/<!--PACKAGE_JSON:.+?-->/s, '').trim()}
            </pre>
          )}
        </div>
      )}
    </div>
  )
}
