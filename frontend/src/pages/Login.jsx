import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ShieldAlert, Loader2 } from 'lucide-react'

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('analyst')
  const [password, setPassword] = useState('analyst123')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const nav = useNavigate()

  const submit = async (e) => {
    e.preventDefault()
    setErr(''); setBusy(true)
    try {
      await onLogin(username, password)
      nav('/')
    } catch (ex) {
      setErr(ex?.response?.data?.detail || 'Login failed')
    } finally { setBusy(false) }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="panel w-full max-w-md p-8 shadow-glow">
        <div className="flex items-center gap-3 mb-6">
          <ShieldAlert className="text-soc-accent" size={28} />
          <div>
            <div className="font-display text-xl font-bold tracking-wider">SOC<span className="text-soc-accent">.AI</span></div>
            <div className="text-xs text-soc-mute font-mono">Analyst augmentation console</div>
          </div>
        </div>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="label">Username</label>
            <input className="input mt-1" value={username} onChange={(e) => setUsername(e.target.value)} />
          </div>
          <div>
            <label className="label">Password</label>
            <input type="password" className="input mt-1" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          {err && <div className="text-sm text-soc-danger">{err}</div>}
          <button className="btn-primary w-full justify-center" disabled={busy}>
            {busy ? <Loader2 className="animate-spin" size={16} /> : null}
            {busy ? 'Authenticating...' : 'Sign in'}
          </button>
        </form>
        <div className="mt-6 text-xs text-soc-mute font-mono">
          demo creds: <span className="text-soc-text">analyst / analyst123</span> &middot; <span className="text-soc-text">admin / admin123</span>
        </div>
      </div>
    </div>
  )
}
