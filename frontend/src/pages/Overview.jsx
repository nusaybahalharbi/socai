import { useEffect, useState } from 'react'
import { metrics, alerts as alertsApi } from '../lib/api'
import { Activity, Bell, ShieldCheck, AlertTriangle } from 'lucide-react'
import { LabelPill, SeverityPill, ConfidenceBar } from '../components/Pills'
import { Link } from 'react-router-dom'
import {
  PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid,
} from 'recharts'

const SEV_COLORS = {
  critical: '#ef4444', high: '#f59e0b', medium: '#22d3ee', low: '#10b981', info: '#7d8aaa',
}

function StatCard({ icon: Icon, label, value, accent = 'text-soc-accent' }) {
  return (
    <div className="panel p-5">
      <div className="flex items-center gap-3 mb-3">
        <div className={`p-2 rounded-md bg-white/5 ${accent}`}><Icon size={18} /></div>
        <div className="label">{label}</div>
      </div>
      <div className="text-3xl font-display font-bold">{value}</div>
    </div>
  )
}

export default function Overview() {
  const [m, setM] = useState(null)
  const [recent, setRecent] = useState([])

  useEffect(() => {
    metrics.overview(24).then(setM).catch(() => {})
    alertsApi.list({ limit: 8 }).then((d) => setRecent(d.items)).catch(() => {})
    const t = setInterval(() => {
      metrics.overview(24).then(setM).catch(() => {})
      alertsApi.list({ limit: 8 }).then((d) => setRecent(d.items)).catch(() => {})
    }, 15000)
    return () => clearInterval(t)
  }, [])

  if (!m) return <div className="text-soc-mute">Loading metrics…</div>

  const sevData = Object.entries(m.by_severity || {}).map(([k, v]) => ({ name: k, value: v }))
  const etData = Object.entries(m.by_event_type || {}).map(([k, v]) => ({ name: k, count: v }))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold font-display tracking-wide">SOC Overview</h1>
        <p className="text-sm text-soc-mute">Last 24 hours · auto-refresh 15s</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Bell} label="Total Alerts" value={m.total_alerts} />
        <StatCard icon={AlertTriangle} label="Threats" value={m.threats} accent="text-soc-danger" />
        <StatCard icon={ShieldCheck} label="False Positives" value={m.false_positives} accent="text-soc-ok" />
        <StatCard icon={Activity} label="Avg Confidence" value={`${Math.round((m.avg_confidence || 0) * 100)}%`} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="panel p-5 lg:col-span-1">
          <h3 className="h-section mb-4">By Severity</h3>
          <div className="h-56">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={sevData} dataKey="value" nameKey="name" innerRadius={48} outerRadius={80}>
                  {sevData.map((d, i) => (
                    <Cell key={i} fill={SEV_COLORS[d.name] || '#7d8aaa'} />
                  ))}
                </Pie>
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel p-5 lg:col-span-2">
          <h3 className="h-section mb-4">By Event Type</h3>
          <div className="h-56">
            <ResponsiveContainer>
              <BarChart data={etData}>
                <CartesianGrid stroke="#1f2940" strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fill: '#7d8aaa', fontSize: 11 }} interval={0} angle={-20} textAnchor="end" height={60} />
                <YAxis tick={{ fill: '#7d8aaa', fontSize: 11 }} allowDecimals={false} />
                <Tooltip contentStyle={{ background: '#11172a', border: '1px solid #1f2940' }} />
                <Bar dataKey="count" fill="#22d3ee" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="panel p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="h-section">Latest Alerts</h3>
          <Link to="/alerts" className="text-sm text-soc-accent hover:underline">View all →</Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left label border-b border-soc-border">
                <th className="py-2 pr-4">Time</th>
                <th className="py-2 pr-4">Title</th>
                <th className="py-2 pr-4">Severity</th>
                <th className="py-2 pr-4">AI</th>
                <th className="py-2 pr-4">Confidence</th>
                <th className="py-2 pr-4">Host</th>
                <th className="py-2 pr-4">User</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((a) => (
                <tr key={a.id} className="border-b border-soc-border/60 hover:bg-white/5">
                  <td className="py-2 pr-4 font-mono text-xs text-soc-mute">{new Date(a.ingested_at).toLocaleTimeString()}</td>
                  <td className="py-2 pr-4">
                    <Link to={`/alerts/${a.id}`} className="text-soc-text hover:text-soc-accent">{a.title}</Link>
                  </td>
                  <td className="py-2 pr-4"><SeverityPill severity={a.severity} /></td>
                  <td className="py-2 pr-4"><LabelPill label={a.prediction?.label} /></td>
                  <td className="py-2 pr-4"><ConfidenceBar value={a.prediction?.confidence} /></td>
                  <td className="py-2 pr-4 font-mono text-xs">{a.host || '—'}</td>
                  <td className="py-2 pr-4 font-mono text-xs">{a.user || '—'}</td>
                </tr>
              ))}
              {recent.length === 0 && (
                <tr><td colSpan="7" className="py-6 text-center text-soc-mute">No alerts yet — the poller will populate shortly.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
