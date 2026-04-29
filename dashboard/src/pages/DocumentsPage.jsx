import { useState, useEffect } from 'react'
import { fetchMissions, getDevisUrl } from '../lib/supabase'
import { FileText, Download, ExternalLink, User, Receipt, Search } from 'lucide-react'

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
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Documents</h2>
        <p className="text-sm text-slate-500 mt-1">Devis, profil et documents legaux</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <a href="https://www.malt.fr/profile/baptistethevenot1" target="_blank" rel="noopener noreferrer"
          className="block bg-white rounded-xl border border-slate-200/80 p-5 hover:border-blue-300 hover:shadow-md transition-all group shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-sm">
              <User className="w-5 h-5 text-white" strokeWidth={1.75} />
            </div>
            <ExternalLink className="w-4 h-4 text-slate-300 group-hover:text-blue-600 transition-colors" />
          </div>
          <p className="text-[14px] font-bold text-slate-900">Profil Malt</p>
          <p className="text-[12px] text-slate-500 mt-1 leading-relaxed">CV en ligne, references et avis clients</p>
        </a>

        <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm">
          <div className="mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center shadow-sm">
              <Receipt className="w-5 h-5 text-white" strokeWidth={1.75} />
            </div>
          </div>
          <p className="text-[14px] font-bold text-slate-900">Devis types</p>
          <p className="text-[12px] text-slate-500 mt-1">TJM 450 EUR/jour HT &middot; Forfait 9 000 EUR/mois</p>
          <p className="text-[11px] text-slate-400 mt-2 font-medium">Generes automatiquement par mission</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm">
          <div className="mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-slate-600 to-slate-700 flex items-center justify-center shadow-sm">
              <FileText className="w-5 h-5 text-white" strokeWidth={1.75} />
            </div>
          </div>
          <p className="text-[14px] font-bold text-slate-900">Mentions legales</p>
          <div className="text-[12px] text-slate-500 space-y-0.5 mt-2 leading-relaxed">
            <p>Baptiste Thevenot</p>
            <p>SIRET 849 022 058</p>
            <p>10 chemin de Catala, 31100 Toulouse</p>
            <p>TVA non applicable — art. 293B du CGI</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h3 className="text-[15px] font-bold text-slate-900">Devis par mission</h3>
            <p className="text-[12px] text-slate-400 mt-0.5">{missions.length} devis disponibles</p>
          </div>
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input type="text" value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Rechercher..."
              className="w-full pl-10 pr-3 py-2 rounded-lg border border-slate-200 text-[13px] focus:ring-2 focus:ring-blue-600 focus:border-blue-600 transition-shadow placeholder:text-slate-400" />
          </div>
        </div>
        {loading && <div className="px-5 py-16 text-center text-sm text-slate-400">Chargement...</div>}
        {!loading && filtered.length === 0 && (
          <p className="px-5 py-16 text-center text-sm text-slate-400">Aucun devis disponible.</p>
        )}
        <div className="divide-y divide-slate-100/80">
          {filtered.map(m => (
            <div key={m.id} className="flex items-center justify-between px-5 py-3.5 hover:bg-slate-50/80 transition-colors">
              <div className="flex items-center gap-3 min-w-0">
                <Receipt className="w-4 h-4 text-slate-400 shrink-0" strokeWidth={1.75} />
                <div className="min-w-0">
                  <p className="text-[13px] font-semibold text-slate-900 truncate">{m.title}</p>
                  <p className="text-[12px] text-slate-500">{m.company || 'Non precise'} &middot; Score {m.score}/100</p>
                </div>
              </div>
              <a href={getDevisUrl(m.id)} target="_blank" rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 shadow-sm transition-all shrink-0">
                <Download className="w-3.5 h-3.5" /> Ouvrir
              </a>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
