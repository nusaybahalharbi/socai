import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const api = axios.create({ baseURL, timeout: 20000 })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('soc_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('soc_token')
      if (!location.pathname.startsWith('/login')) location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export const auth = {
  login: (username, password) =>
    api.post('/auth/login', { username, password }).then((r) => r.data),
  me: () => api.get('/auth/me').then((r) => r.data),
}

export const alerts = {
  list: (params) => api.get('/alerts', { params }).then((r) => r.data),
  get: (id) => api.get(`/alerts/${id}`).then((r) => r.data),
  feedback: (id, decision, notes) =>
    api.post(`/alerts/${id}/feedback`, { decision, notes }).then((r) => r.data),
}

export const metrics = {
  overview: (window_hours = 24) =>
    api.get('/metrics/overview', { params: { window_hours } }).then((r) => r.data),
}

export const mitre = {
  techniques: () => api.get('/mitre/techniques').then((r) => r.data),
  heatmap: () => api.get('/mitre/heatmap').then((r) => r.data),
}
