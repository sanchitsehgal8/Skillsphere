import { Meter } from './ui/meter'
import { EmptyState } from './ui/misc'
import { HeartHandshake } from 'lucide-react'
import { scoreTone } from '../lib/utils'

export default function CultureFitPanel({ signals = [] }) {
  const evidenced = signals.filter((s) => s.score > 0 || (s.evidence || []).length)
  if (!evidenced.length) {
    return (
      <EmptyState
        icon={HeartHandshake}
        title="No observable culture signals yet"
        description="Signals come only from GitHub and resume activity — never inferred personality."
      />
    )
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {evidenced.map((s) => (
        <div key={s.key} className="rounded-xl border border-border bg-surface/40 p-4">
          <div className="mb-2.5 flex items-center justify-between gap-2">
            <span className="text-sm font-medium text-foreground">{s.label}</span>
            <span className="font-mono text-xs font-semibold text-foreground">{s.score.toFixed(0)}</span>
          </div>
          <Meter value={s.score} tone={scoreTone(s.score)} />
          {s.reasoning && <p className="mt-2.5 text-xs leading-relaxed text-muted-foreground">{s.reasoning}</p>}
        </div>
      ))}
    </div>
  )
}
