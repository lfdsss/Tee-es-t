import { useState, useEffect, lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { getSession } from './lib/auth'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import MissionsPage from './pages/MissionsPage'
import MissionDetailPage from './pages/MissionDetailPage'

const ProposalsPage = lazy(() => import('./pages/ProposalsPage'))
const DocumentsPage = lazy(() => import('./pages/DocumentsPage'))
const AgentPage = lazy(() => import('./pages/AgentPage'))
const SettingsPage = lazy(() => import('./pages/SettingsPage'))

function ProtectedRoute({ children }) {
  const session = getSession()
  if (!session) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  const [session, setSession] = useState(getSession())

  useEffect(() => {
    const onStorage = () => setSession(getSession())
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [])

  if (!session) {
    return <Routes>
      <Route path="/login" element={<LoginPage onLogin={setSession} />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage onLogin={setSession} />} />
      <Route element={<ProtectedRoute><Layout session={session} onLogout={() => { setSession(null) }} /></ProtectedRoute>}>
        <Route index element={<DashboardPage session={session} />} />
        <Route path="missions" element={<MissionsPage session={session} />} />
        <Route path="missions/:id" element={<MissionDetailPage session={session} />} />
        <Route path="proposals" element={<Suspense fallback={null}><ProposalsPage session={session} /></Suspense>} />
        <Route path="documents" element={<Suspense fallback={null}><DocumentsPage session={session} /></Suspense>} />
        <Route path="agent" element={<Suspense fallback={null}><AgentPage session={session} /></Suspense>} />
        <Route path="settings" element={<Suspense fallback={null}><SettingsPage session={session} /></Suspense>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
