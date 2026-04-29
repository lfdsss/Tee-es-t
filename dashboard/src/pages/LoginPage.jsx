import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../lib/auth'
import { Eye, EyeOff, ArrowRight } from 'lucide-react'

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
      <div className="hidden lg:flex lg:w-[480px] bg-black flex-col justify-between p-14 relative">
        <div>
          <div className="w-8 h-px bg-white mb-10" />
          <h1 className="text-3xl font-semibold text-white tracking-tight leading-tight">
            Mission<br />Hunter
          </h1>
          <p className="text-sm text-slate-400 mt-4 leading-relaxed max-w-[280px]">
            Plateforme de chasse aux missions freelance.
          </p>
        </div>
        <p className="text-[13px] text-slate-600">Baptiste Thevenot — Consultant Web & IA</p>
      </div>

      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-[380px]">
          <div className="lg:hidden mb-12">
            <div className="w-8 h-px bg-slate-950 mb-6" />
            <h1 className="text-xl font-semibold text-slate-950 tracking-tight">Mission Hunter</h1>
          </div>

          <div className="mb-10">
            <h2 className="text-2xl font-semibold text-slate-950 tracking-tight">Connexion</h2>
            <p className="text-sm text-slate-500 mt-2">Accedez a votre espace consultant</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-4 py-3">{error}</div>
            )}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Identifiant</label>
              <input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                className="w-full px-4 py-3 rounded-lg border border-slate-200 text-sm bg-white focus:border-slate-950 transition-colors placeholder:text-slate-400"
                placeholder="Votre identifiant"
                autoFocus
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Mot de passe</label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full px-4 py-3 rounded-lg border border-slate-200 text-sm bg-white focus:border-slate-950 transition-colors pr-11 placeholder:text-slate-400"
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
              className="w-full flex items-center justify-center gap-2 py-3 bg-black hover:bg-slate-800 active:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
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
