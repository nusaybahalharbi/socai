import { useEffect, useState } from 'react'
import { metrics } from '../lib/api'

export default function Metrics() {
  const [m, setM] = useState(null)
  const [hours, setHours] = useState(24)
  useEffect(() => { metrics.overview(hours).then(setM) }, [hours])

  if (!m) return <div className="text-soc-mute">Loading…</div>

  const triagedSavingsHrs = ((m.false_positives * 6) / 60).toFixed(1) // assume 6 min saved per auto-triaged FP

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold font-display">SOC Metrics</h1>
          <p className="text-sm text-soc-mute">Operational efficiency and impact KPIs</p>
        </div>
        <select className="input max-w-[200px]" value={hours} onChange={(e) => setHours(Number(e.target.value))}>
          <option value={1}>Last 1 hour</option>
          <option value={24}>Last 24 hours</option>
          <option value={168}>Last 7 days</option>
          <option value={720}>Last 30 days</option>
        </select>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="panel p-5">
          <div className="label">Auto-triage rate</div>
          <div className="text-3xl font-display font-bold mt-2">{m.fp_reduction_estimate_pct}%</div>
          <div className="text-xs text-soc-mute mt-1">Share of alerts the AI marked as false positive</div>
        </div>
        <div className="panel p-5">
          <div className="label">Estimated analyst hours saved</div>
          <div className="text-3xl font-display font-bold mt-2">{triagedSavingsHrs}h</div>
          <div className="text-xs text-soc-mute mt-1">Assuming 6 min saved per auto-triaged FP</div>
        </div>
        <div className="panel p-5">
          <div className="label">Open alerts</div>
          <div className="text-3xl font-display font-bold mt-2">{m.open_alerts}</div>
          <div className="text-xs text-soc-mute mt-1">Awaiting analyst review</div>
        </div>
      </div>
      <div className="panel p-5">
        <h3 className="h-section mb-3">By severity</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {Object.entries(m.by_severity || {}).map(([k, v]) => (
            <div key={k} className="border border-soc-border rounded-md p-3 text-center">
              <div className="label">{k}</div>
              <div className="text-2xl font-display font-bold mt-1">{v}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
