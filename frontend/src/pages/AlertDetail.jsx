import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { alerts as alertsApi } from '../lib/api'
import { LabelPill, SeverityPill, ConfidenceBar } from '../components/Pills'
import { ChevronLeft, CheckCircle2, XCircle, ArrowUpRight, Clock } from 'lucide-react'

function KV({ k, v }) {
  return (
    <div>
      <div className="label">{k}</div>
      <div className="text-sm font-mono break-all">{v ?? '—'}</div>
    </div>
  )
}

function FeatureBar({ feat }) {
  const impact = feat.impact || 0
  const dir = impact >= 0 ? 'right' : 'left'
  const pct = Math.min(100, Math.round(Math.abs(impact) * 100 * 4)) // visual scale
  const color = impact >= 0 ? 'bg-soc-danger' : 'bg-soc-ok'
  return (
    <div className="grid grid-cols-[180px_1fr_60px] items-center gap-3">
      <div className="font-mono text-xs text-soc-mute truncate">{feat.feature}</div>
      <div className="relative h-2 bg-white/5 rounded">
        <div
          className={`absolute top-0 ${dir === 'right' ? 'left-1/2' : 'right-1/2'} h-full ${color} rounded`}
          style={{ width: `${pct / 2}%` }}
        />
        <div className="absolute left-1/2 top-0 h-full w-px bg-white/20" />
      </div>
      <div className="text-xs font-mono text-right">{(impact || 0).toFixed(3)}</div>
    </div>
  )
}

export default function AlertDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const [a, setA] = useState(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')

  const load = () => alertsApi.get(id).then(setA).catch((e) => setErr(String(e)))
  useEffect(() => { load() }, [id])

  if (err) return <div className="text-soc-danger">{err}</div>
  if (!a) return <div className="text-soc-mute">Loading…</div>

  const submit = async (decision) => {
    setBusy(true)
    try {
      await alertsApi.feedback(a.id, decision, '')
      await load()
    } finally { setBusy(false) }
  }

  const expl = a.prediction?.explanation || {}
  const topFeats = expl.top_features || []

  return (
    <div className="space-y-6">
      <button onClick={() => nav(-1)} className="btn-ghost"><ChevronLeft size={14} /> Back</button>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold font-display">{a.title}</h1>
          <div className="flex items-center gap-2 mt-2 text-sm text-soc-mute font-mono">
            <span>#{a.id}</span> · <span>{a.source}</span> · <span>{new Date(a.ingested_at).toLocaleString()}</span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <SeverityPill severity={a.severity} />
          <LabelPill label={a.prediction?.label} />
          <div className="w-40"><ConfidenceBar value={a.prediction?.confidence} /></div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="panel p-5 lg:col-span-2 space-y-4">
          <div>
            <h3 className="h-section">Description</h3>
            <p className="text-sm text-soc-mute mt-1">{a.description || '—'}</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 pt-2 border-t border-soc-border">
            <KV k="Event Type" v={a.event_type} />
            <KV k="Source IP" v={a.src_ip} />
            <KV k="Dest IP" v={a.dst_ip} />
            <KV k="Host" v={a.host} />
            <KV k="User" v={a.user} />
            <KV k="Failed Logins" v={a.failed_login_count} />
            <KV k="Process" v={a.process_name} />
            <KV k="Hour of Day" v={a.occurred_at ? new Date(a.occurred_at).getHours() : null} />
            <KV k="Status" v={a.status} />
          </div>
          {a.command_line && (
            <div>
              <div className="label mb-1">Command Line</div>
              <pre className="bg-black/40 border border-soc-border rounded-md p-3 text-xs font-mono overflow-x-auto whitespace-pre-wrap">{a.command_line}</pre>
            </div>
          )}
        </div>

        <div className="panel p-5 space-y-4">
          <h3 className="h-section">Analyst Actions</h3>
          <button className="btn-danger w-full" disabled={busy} onClick={() => submit('confirm_threat')}>
            <CheckCircle2 size={16} /> Confirm Threat
          </button>
          <button className="btn-ok w-full" disabled={busy} onClick={() => submit('false_positive')}>
            <XCircle size={16} /> Mark False Positive
          </button>
          <button className="btn-warn w-full" disabled={busy} onClick={() => submit('escalate')}>
            <ArrowUpRight size={16} /> Escalate
          </button>
          <button className="btn-ghost w-full" disabled={busy} onClick={() => submit('needs_review')}>
            <Clock size={16} /> Needs Review
          </button>
          <div className="text-xs text-soc-mute pt-2 border-t border-soc-border">
            Feedback is stored for retraining and audit.
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="panel p-5">
          <h3 className="h-section mb-3">AI Explanation</h3>
          <div className="text-xs text-soc-mute font-mono mb-3">
            method: {expl.method || 'unknown'} · model: {a.prediction?.model_version || '—'}
          </div>
          {topFeats.length === 0 ? (
            <div className="text-sm text-soc-mute">No feature attributions available.</div>
          ) : (
            <div className="space-y-2">
              {topFeats.map((f, i) => <FeatureBar key={i} feat={f} />)}
              <div className="flex justify-between text-xs text-soc-mute font-mono pt-2 border-t border-soc-border">
                <span>← decreases threat</span><span>increases threat →</span>
              </div>
            </div>
          )}
          {a.prediction?.recommendation && (
            <div className="mt-4 p-3 rounded-md bg-soc-accent/5 border border-soc-accent/20">
              <div className="label text-soc-accent">Recommendation</div>
              <p className="text-sm mt-1 leading-relaxed">{a.prediction.recommendation}</p>
            </div>
          )}
        </div>

        <div className="panel p-5">
          <h3 className="h-section mb-3">MITRE ATT&CK Mapping</h3>
          {(!a.mitre_mappings || a.mitre_mappings.length === 0) && (
            <div className="text-sm text-soc-mute">No MITRE mappings detected for this alert.</div>
          )}
          <div className="space-y-3">
            {a.mitre_mappings?.map((m, i) => (
              <div key={i} className="border border-soc-border rounded-md p-3 bg-soc-panel2/40">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-mono text-soc-accent text-sm">{m.technique_id}</div>
                    <div className="font-medium">{m.technique_name}</div>
                  </div>
                  <div className="text-xs font-mono text-soc-mute">{Math.round(m.confidence * 100)}%</div>
                </div>
                <div className="text-xs text-soc-mute font-mono mt-1 uppercase tracking-wider">{m.tactic}</div>
                <div className="text-sm mt-2">{m.rationale}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
