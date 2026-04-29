import { useState, useEffect } from 'react'
import { fetchMissions, getDevisUrl } from '../lib/supabase'
import { Download, ExternalLink, Search } from 'lucide-react'
import cleanText from '../lib/cleanText'

export default function DocumentsPage() {
  const [missions, setMissions] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const { data } = await fetchMissions({ limit: 100 })
        setMissions((data || []).filter(m => m.status === 'proposal_ready' || m.status === 'sent' || m.status === 'won'))
      } catch (e) { console.error(e) }
      setLoading(false)
    }
    load()
  }, [])

  const filtered = search
    ? missions.filter(m => m.title?.toLowerCase().includes(search.toLowerCase()) || m.company?.toLowerCase().includes(search.toLowerCase()))
    : missions

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-950 tracking-tight">Documents</h2>
        <p className="text-sm text-slate-500 mt-1">Devis, profil et documents légaux</p>
      </div>

      {/* Profils & Plateformes */}
      <div>
        <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">Mes profils</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            { name: 'Malt', url: 'https://www.malt.fr/profile/baptistethevenot1', desc: 'Profil, avis clients, références' },
            { name: 'Codeur.com', url: 'https://www.codeur.com/-baptistethevenot', desc: 'Missions freelance, devis' },
            { name: 'LinkedIn', url: 'https://www.linkedin.com/in/baptiste-thevenot/', desc: 'Réseau professionnel' },
            { name: 'Crème de la Crème', url: 'https://www.cremedelacreme.io', desc: 'Missions premium tech' },
          ].map(p => (
            <a key={p.name} href={p.url} target="_blank" rel="noopener noreferrer"
              className="group flex items-start gap-3 p-4 bg-white border border-slate-200 rounded-lg hover:border-slate-950 transition-colors">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-slate-950 group-hover:text-blue-600 transition-colors">{p.name}</p>
                <p className="text-[12px] text-slate-400 mt-0.5">{p.desc}</p>
              </div>
              <ExternalLink className="w-3.5 h-3.5 text-slate-300 group-hover:text-slate-950 transition-colors shrink-0 mt-0.5" />
            </a>
          ))}
        </div>
      </div>

      {/* Info cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-4">Tarifs</p>
          <p className="text-sm font-semibold text-slate-950">Devis types</p>
          <p className="text-[13px] text-slate-500 mt-1">TJM 450 EUR/jour HT · Forfait 9 000 EUR/mois</p>
          <p className="text-[13px] text-slate-400 mt-2">Générés automatiquement par mission</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-6">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-4">Legal</p>
          <p className="text-sm font-semibold text-slate-950">Mentions légales</p>
          <div className="text-[13px] text-slate-500 space-y-0.5 mt-2 leading-relaxed">
            <p>Baptiste Thevenot</p>
            <p>SIRET 849 022 058</p>
            <p>10 chemin de Catala, 31100 Toulouse</p>
            <p>TVA non applicable — art. 293B du CGI</p>
          </div>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg">
        <div className="px-6 py-5 border-b border-slate-200 flex items-center justify-between gap-4 flex-wrap">
          <div>
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">Devis par mission</p>
            <p className="text-[13px] text-slate-500">{missions.length} devis disponibles</p>
          </div>
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input type="text" value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Rechercher..."
              className="w-full pl-10 pr-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-slate-400 transition-colors placeholder:text-slate-400" />
          </div>
        </div>
        {loading && <div className="px-6 py-16 text-center text-sm text-slate-400">Chargement...</div>}
        {!loading && filtered.length === 0 && (
          <p className="px-6 py-16 text-center text-sm text-slate-400">Aucun devis disponible.</p>
        )}
        {filtered.map((m, i) => (
          <div key={m.id} className={`flex items-center justify-between px-6 py-4 border-b border-slate-100 last:border-0 ${i % 2 === 1 ? 'bg-slate-50' : ''}`}>
            <div className="min-w-0">
              <p className="text-sm font-medium text-slate-950 truncate">{cleanText(m.title)}</p>
              <p className="text-[13px] text-slate-500 mt-0.5">{cleanText(m.company) || 'Non précisé'} · Score {m.score}/100</p>
            </div>
            <a href={getDevisUrl(m.id)} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-200 text-sm text-slate-700 hover:border-slate-300 transition-colors shrink-0 ml-4">
              <Download className="w-4 h-4" /> Ouvrir
            </a>
          </div>
        ))}
      </div>
    </div>
  )
}
