import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { alerts as alertsApi } from '../lib/api'
import { LabelPill, SeverityPill, ConfidenceBar } from '../components/Pills'
import { Filter, RefreshCw } from 'lucide-react'

export default function Alerts() {
  const [data, setData] = useState({ total: 0, items: [] })
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({ status: '', label: '', severity: '', min_confidence: '' })

  const fetch = async () => {
    setLoading(true)
    const params = {}
    Object.entries(filters).forEach(([k, v]) => { if (v !== '') params[k] = v })
    params.limit = 100
    try { setData(await alertsApi.list(params)) } finally { setLoading(false) }
  }

  useEffect(() => { fetch() }, [])  // initial
  useEffect(() => {
    const t = setInterval(fetch, 15000); return () => clearInterval(t)
  }, [filters])

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold font-display tracking-wide">Alert Queue</h1>
          <p className="text-sm text-soc-mute">{data.total} matching alerts</p>
        </div>
        <button onClick={fetch} className="btn-ghost"><RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh</button>
      </div>

      <div className="panel p-4 grid grid-cols-2 md:grid-cols-5 gap-3">
        <div>
          <div className="label flex items-center gap-1"><Filter size={12} /> Status</div>
          <select className="input mt-1" value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
            <option value="">all</option><option>new</option><option>triaged</option><option>escalated</option><option>closed</option>
          </select>
        </div>
        <div>
          <div className="label">AI Label</div>
          <select className="input mt-1" value={filters.label} onChange={(e) => setFilters({ ...filters, label: e.target.value })}>
            <option value="">all</option><option value="threat">threat</option><option value="false_positive">false positive</option>
          </select>
        </div>
        <div>
          <div className="label">Severity</div>
          <select className="input mt-1" value={filters.severity} onChange={(e) => setFilters({ ...filters, severity: e.target.value })}>
            <option value="">all</option><option>critical</option><option>high</option><option>medium</option><option>low</option><option>info</option>
          </select>
        </div>
        <div>
          <div className="label">Min Confidence</div>
          <select className="input mt-1" value={filters.min_confidence} onChange={(e) => setFilters({ ...filters, min_confidence: e.target.value })}>
            <option value="">any</option><option value="0.5">≥ 50%</option><option value="0.7">≥ 70%</option><option value="0.85">≥ 85%</option>
          </select>
        </div>
        <div className="flex items-end"><button className="btn-primary w-full" onClick={fetch}>Apply</button></div>
      </div>

      <div className="panel overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-soc-panel2/60">
            <tr className="text-left label">
              <th className="py-3 px-4">When</th>
              <th className="py-3 px-4">Title</th>
              <th className="py-3 px-4">Sev</th>
              <th className="py-3 px-4">AI</th>
              <th className="py-3 px-4">Confidence</th>
              <th className="py-3 px-4">MITRE</th>
              <th className="py-3 px-4">Host / User</th>
              <th className="py-3 px-4">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((a) => (
              <tr key={a.id} className="border-t border-soc-border/60 hover:bg-white/5">
                <td className="py-3 px-4 font-mono text-xs text-soc-mute">{new Date(a.ingested_at).toLocaleString()}</td>
                <td className="py-3 px-4"><Link to={`/alerts/${a.id}`} className="hover:text-soc-accent">{a.title}</Link></td>
                <td className="py-3 px-4"><SeverityPill severity={a.severity} /></td>
                <td className="py-3 px-4"><LabelPill label={a.prediction?.label} /></td>
                <td className="py-3 px-4"><ConfidenceBar value={a.prediction?.confidence} /></td>
                <td className="py-3 px-4 font-mono text-xs">
                  {a.mitre_mappings?.slice(0, 2).map((m) => (
                    <span key={m.technique_id} className="pill border border-soc-accent/30 bg-soc-accent/10 text-soc-accent mr-1">
                      {m.technique_id}
                    </span>
                  )) || '—'}
                </td>
                <td className="py-3 px-4 font-mono text-xs">{a.host || '—'} / {a.user || '—'}</td>
                <td className="py-3 px-4">
                  <span className="pill border border-soc-border text-soc-mute">{a.status}</span>
                </td>
              </tr>
            ))}
            {data.items.length === 0 && (
              <tr><td colSpan="8" className="py-12 text-center text-soc-mute">No alerts match these filters.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
