import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchMission, fetchProposals, updateMission, getDevisUrl } from '../lib/supabase'
import { ArrowLeft, ExternalLink, Download } from 'lucide-react'

function cleanText(text) {
  if (!text) return ''
  return text
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, ' ')
    .replace(/<[^>]*>/g, '')
}

function parsePackage(text) {
  if (!text) return null
  const match = text.match(/<!--PACKAGE_JSON:(.+?)-->/s)
  if (!match) return null
  try { return JSON.parse(match[1]) } catch { return null }
}

const STATUS_FLOW = [
  { key: 'new', label: 'Nouveau' },
  { key: 'proposal_ready', label: 'Proposition' },
  { key: 'sent', label: 'Envoyé' },
  { key: 'won', label: 'Gagné' },
]

function scoreColor(score) {
  if (score >= 80) return 'text-emerald-600'
  if (score >= 60) return 'text-blue-600'
  if (score >= 40) return 'text-amber-600'
  return 'text-slate-400'
}

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
  const proposal = proposals[0]
  const pkg = proposal ? parsePackage(proposal.text) : null

  return (
    <div className="space-y-6 max-w-4xl">
      <Link to="/missions" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-blue-600 transition-colors">
        <ArrowLeft className="w-4 h-4" /> Missions
      </Link>

      <div>
        <h2 className="text-2xl font-bold text-slate-950 tracking-tight">{mission.title}</h2>
        <div className="flex flex-wrap items-center gap-4 mt-2 text-sm text-slate-500">
          <span>{mission.company || 'Non précisé'}</span>
          <span className="text-slate-300">·</span>
          <span>{mission.source}</span>
          {mission.type && <>
            <span className="text-slate-300">·</span>
            <span className="capitalize">{mission.type}</span>
          </>}
          {mission.remote && <>
            <span className="text-slate-300">·</span>
            <span>Remote</span>
          </>}
          {mission.budget_raw && <>
            <span className="text-slate-300">·</span>
            <span className="text-slate-950 font-medium">{mission.budget_raw}</span>
          </>}
          <span className="text-slate-300">·</span>
          <span className={`font-bold tabular-nums ${scoreColor(score)}`}>{score}/100</span>
        </div>
      </div>

      {/* Pipeline */}
      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-5">Pipeline</p>
        <div className="flex items-center gap-0">
          {STATUS_FLOW.map((step, i) => {
            const isActive = step.key === mission.status
            const isPast = i <= currentStep
            return (
              <div key={step.key} className="flex items-center">
                {i > 0 && <div className={`w-12 h-px ${isPast ? 'bg-slate-950' : 'bg-slate-200'}`} />}
                <button onClick={() => setStatus(step.key)} disabled={updating}
                  className="flex items-center gap-2.5 disabled:opacity-50 group">
                  <div className={`w-3 h-3 rounded-full border-2 transition-colors ${
                    isActive ? 'bg-slate-950 border-slate-950' :
                    isPast ? 'bg-slate-950 border-slate-950' :
                    'bg-white border-slate-300 group-hover:border-slate-400'
                  }`} />
                  <span className={`text-sm transition-colors ${
                    isActive ? 'font-semibold text-slate-950' :
                    isPast ? 'text-slate-600' :
                    'text-slate-400 group-hover:text-slate-600'
                  }`}>{step.label}</span>
                </button>
              </div>
            )
          })}
          <div className="ml-auto">
            <button onClick={() => setStatus('lost')} disabled={updating}
              className={`text-sm transition-colors disabled:opacity-50 ${
                mission.status === 'lost' ? 'font-semibold text-red-600' :
                'text-slate-400 hover:text-red-600'
              }`}>
              {mission.status === 'lost' && <span className="w-1.5 h-1.5 rounded-full bg-red-500 inline-block mr-2" />}
              Perdu
            </button>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap gap-3">
        {mission.source_url && (
          <a href={mission.source_url} target="_blank" rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-slate-950 text-white text-sm font-medium hover:bg-slate-800 transition-colors">
            <ExternalLink className="w-4 h-4" /> Voir l'offre
          </a>
        )}
        <a href={getDevisUrl(mission.id)} target="_blank" rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border border-slate-200 text-sm font-medium text-slate-700 hover:border-slate-300 transition-colors">
          <Download className="w-4 h-4" /> Devis
        </a>
      </div>

      {/* Info grid */}
      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-4">Informations</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-y-5 gap-x-8">
          <div>
            <p className="text-[13px] text-slate-500">Entreprise</p>
            <p className="text-sm font-medium text-slate-950 mt-0.5">{mission.company || 'Non précisé'}</p>
          </div>
          <div>
            <p className="text-[13px] text-slate-500">Source</p>
            <p className="text-sm font-medium text-slate-950 mt-0.5">{mission.source}</p>
          </div>
          <div>
            <p className="text-[13px] text-slate-500">Type</p>
            <p className="text-sm font-medium text-slate-950 mt-0.5 capitalize">{mission.type || '—'}</p>
          </div>
          <div>
            <p className="text-[13px] text-slate-500">Budget</p>
            <p className="text-sm font-medium text-slate-950 mt-0.5">{mission.budget_raw || '—'}</p>
          </div>
        </div>
      </div>

      {/* Description */}
      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-4">Description</p>
        <div className="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap max-h-[400px] overflow-y-auto">
          {cleanText(mission.description) || 'Pas de description disponible.'}
        </div>
        {mission.tags && mission.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-5 pt-5 border-t border-slate-100">
            {mission.tags.map((tag, i) => (
              <span key={i} className="text-[13px] text-slate-500">{tag}{i < mission.tags.length - 1 ? ',' : ''}</span>
            ))}
          </div>
        )}
      </div>

      {/* Proposal */}
      {proposal && (
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-5">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Proposition</p>
            <Link to="/proposals" className="text-sm text-blue-600 hover:text-blue-700 transition-colors">
              Toutes les propositions
            </Link>
          </div>
          {pkg ? (
            <div className="space-y-5">
              {pkg.intro && <p className="text-sm leading-relaxed text-slate-700">{pkg.intro}</p>}
              {pkg.phases && pkg.phases.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {pkg.phases.map((p, i) => (
                    <div key={i} className="border border-slate-200 rounded-lg p-4">
                      <p className="text-sm font-semibold text-slate-950">{p.name}</p>
                      <p className="text-[13px] text-slate-500 mt-1">{p.duration}</p>
                    </div>
                  ))}
                </div>
              )}
              {pkg.expected_outcome && (
                <div className="border-l-2 border-slate-300 pl-4 py-1">
                  <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Résultat attendu</p>
                  <p className="text-sm text-slate-600 leading-relaxed">{pkg.expected_outcome}</p>
                </div>
              )}
              <Link to="/proposals" className="inline-flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-700 transition-colors">
                Voir le package complet <ExternalLink className="w-3.5 h-3.5" />
              </Link>
            </div>
          ) : (
            <pre className="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap font-sans max-h-[300px] overflow-y-auto">
              {proposal.text?.replace(/<!--PACKAGE_JSON:.+?-->/s, '').trim()}
            </pre>
          )}
        </div>
      )}
    </div>
  )
}
