import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import Layout from './components/Layout'
import Login from './pages/Login'
import Overview from './pages/Overview'
import Alerts from './pages/Alerts'
import AlertDetail from './pages/AlertDetail'
import Mitre from './pages/Mitre'
import Metrics from './pages/Metrics'
import Settings from './pages/Settings'

export default function App() {
  const { user, loading, login, logout } = useAuth()

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-soc-mute">Loading…</div>
  }

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<Login onLogin={login} />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    )
  }

  return (
    <Layout user={user} onLogout={logout}>
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/alerts/:id" element={<AlertDetail />} />
        <Route path="/mitre" element={<Mitre />} />
        <Route path="/metrics" element={<Metrics />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/login" element={<Navigate to="/" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}
