import { useEffect, useState } from 'react'
import { auth } from '../lib/api'

export function useAuth() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('soc_token')
    if (!token) { setLoading(false); return }
    auth.me()
      .then(setUser)
      .catch(() => localStorage.removeItem('soc_token'))
      .finally(() => setLoading(false))
  }, [])

  const login = async (u, p) => {
    const data = await auth.login(u, p)
    localStorage.setItem('soc_token', data.access_token)
    const me = await auth.me()
    setUser(me)
    return me
  }

  const logout = () => {
    localStorage.removeItem('soc_token')
    setUser(null)
  }

  return { user, loading, login, logout }
}
