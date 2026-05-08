import clsx from 'clsx'

export function SeverityPill({ severity }) {
  const map = {
    critical: 'bg-soc-danger/15 text-soc-danger border-soc-danger/40',
    high:     'bg-soc-warn/15 text-soc-warn border-soc-warn/40',
    medium:   'bg-soc-accent/15 text-soc-accent border-soc-accent/40',
    low:      'bg-soc-ok/15 text-soc-ok border-soc-ok/40',
    info:     'bg-soc-mute/10 text-soc-mute border-soc-mute/30',
  }
  return (
    <span className={clsx('pill border', map[severity] || map.info)}>{severity}</span>
  )
}

export function LabelPill({ label }) {
  if (!label) return <span className="pill border border-soc-border text-soc-mute">unscored</span>
  return label === 'threat' ? (
    <span className="pill border border-soc-danger/40 bg-soc-danger/15 text-soc-danger">threat</span>
  ) : (
    <span className="pill border border-soc-ok/40 bg-soc-ok/15 text-soc-ok">false positive</span>
  )
}

export function ConfidenceBar({ value }) {
  const pct = Math.round((value || 0) * 100)
  const color = pct >= 80 ? 'bg-soc-danger' : pct >= 60 ? 'bg-soc-warn' : 'bg-soc-accent'
  return (
    <div className="flex items-center gap-2 min-w-[120px]">
      <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div className={clsx('h-full', color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-mono text-soc-mute w-10 text-right">{pct}%</span>
    </div>
  )
}
