import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../lib/auth'
import { Eye, EyeOff, ArrowRight, Briefcase } from 'lucide-react'

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    await new Promise(r => setTimeout(r, 400))
    const session = login(username, password)
    if (session) {
      onLogin(session)
      navigate('/')
    } else {
      setError('Identifiants incorrects')
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen flex bg-white">
      <div className="hidden lg:flex lg:w-[480px] bg-slate-900 flex-col justify-between p-12 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600/20 via-transparent to-violet-600/10" />
        <div className="relative">
          <div className="w-10 h-10 rounded-xl bg-white/10 backdrop-blur flex items-center justify-center mb-8">
            <Briefcase className="w-5 h-5 text-white" strokeWidth={1.5} />
          </div>
          <h1 className="text-2xl font-semibold text-white leading-tight">Mission Hunter</h1>
          <p className="text-sm text-slate-400 mt-2 leading-relaxed max-w-xs">
            Plateforme de chasse aux missions freelance. Scoring IA, propositions automatiques, pipeline CRM.
          </p>
        </div>
        <div className="relative space-y-4">
          <div className="p-4 rounded-xl bg-white/5 backdrop-blur border border-white/10">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-2 h-2 rounded-full bg-emerald-400" />
              <span className="text-xs font-medium text-emerald-400">Agent actif</span>
            </div>
            <p className="text-[13px] text-slate-300">14 sources surveillees en continu</p>
          </div>
          <p className="text-[11px] text-slate-500">Baptiste Thevenot — Consultant Web & IA</p>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-[380px]">
          <div className="lg:hidden mb-10">
            <div className="w-10 h-10 rounded-xl bg-slate-900 flex items-center justify-center mb-4">
              <Briefcase className="w-5 h-5 text-white" strokeWidth={1.5} />
            </div>
            <h1 className="text-xl font-semibold text-slate-900">Mission Hunter</h1>
          </div>

          <div className="mb-8">
            <h2 className="text-lg font-semibold text-slate-900">Connexion</h2>
            <p className="text-sm text-slate-500 mt-1">Accedez a votre espace consultant</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-4 py-3 font-medium">{error}</div>
            )}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Identifiant</label>
              <input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                className="w-full px-4 py-2.5 rounded-lg border border-slate-200 text-sm bg-white focus:ring-2 focus:ring-blue-600 focus:border-blue-600 transition-shadow placeholder:text-slate-400"
                placeholder="Votre identifiant"
                autoFocus
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Mot de passe</label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-lg border border-slate-200 text-sm bg-white focus:ring-2 focus:ring-blue-600 focus:border-blue-600 transition-shadow pr-11 placeholder:text-slate-400"
                  placeholder="Votre mot de passe"
                />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors">
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <button
              type="submit"
              disabled={loading || !username || !password}
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-semibold transition-all shadow-sm shadow-blue-600/25"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>Se connecter <ArrowRight className="w-4 h-4" /></>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
