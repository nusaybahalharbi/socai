import { useEffect, useState } from 'react'
import { mitre } from '../lib/api'

const TACTIC_ORDER = [
  'Initial Access', 'Execution', 'Persistence', 'Privilege Escalation',
  'Defense Evasion', 'Credential Access', 'Discovery', 'Lateral Movement',
  'Collection', 'Command and Control', 'Exfiltration', 'Impact',
]

export default function Mitre() {
  const [data, setData] = useState([])
  useEffect(() => { mitre.heatmap().then(setData).catch(() => {}) }, [])

  const max = Math.max(1, ...data.map((d) => d.count))
  const byTactic = TACTIC_ORDER.map((t) => ({
    tactic: t,
    items: data.filter((d) => d.tactic === t).sort((a, b) => b.count - a.count),
  }))

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold font-display">MITRE ATT&CK Coverage</h1>
        <p className="text-sm text-soc-mute">Hits across all ingested alerts. Heatmap shows where adversaries are most active.</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {byTactic.map((col) => (
          <div key={col.tactic} className="panel p-4">
            <div className="label mb-2">{col.tactic}</div>
            {col.items.length === 0 ? (
              <div className="text-xs text-soc-mute">No hits</div>
            ) : (
              <div className="space-y-2">
                {col.items.map((it) => {
                  const intensity = it.count / max
                  const bg = `rgba(34,211,238,${0.15 + 0.5 * intensity})`
                  return (
                    <div key={it.technique_id}
                         className="flex items-center justify-between gap-2 px-3 py-2 rounded-md border border-soc-accent/20"
                         style={{ background: bg }}>
                      <div>
                        <div className="font-mono text-xs text-soc-accent">{it.technique_id}</div>
                        <div className="text-sm">{it.technique_name}</div>
                      </div>
                      <div className="font-display font-bold">{it.count}</div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
