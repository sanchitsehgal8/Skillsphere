import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { ChevronDown, Lightbulb } from 'lucide-react'
import { Meter } from './ui/meter'
import { Badge } from './ui/badge'
import { scoreTone, cn } from '../lib/utils'

function DimensionRow({ dimension }) {
  const [open, setOpen] = useState(false)
  const hasDetail = (dimension.evidence || []).length > 0 || (dimension.suggestions || []).length > 0
  const tone = scoreTone(dimension.score)

  return (
    <div className="rounded-xl border border-border bg-surface/40 transition-colors hover:border-foreground/10">
      <button
        type="button"
        onClick={() => hasDetail && setOpen((o) => !o)}
        className={cn('flex w-full items-center gap-4 p-3.5 text-left', hasDetail && 'cursor-pointer')}
      >
        <div className="min-w-0 flex-1">
          <div className="mb-2 flex items-center justify-between gap-3">
            <span className="truncate text-sm font-medium text-foreground">{dimension.label}</span>
            <span className="flex items-center gap-2 font-mono text-xs text-muted-foreground">
              <span className="font-semibold text-foreground">{dimension.score.toFixed(0)}</span>
              <span className="text-muted-foreground/60">·</span>
              {Math.round((dimension.confidence || 0) * 100)}% conf
            </span>
          </div>
          <Meter value={dimension.score} tone={tone} />
        </div>
        {hasDetail && (
          <ChevronDown
            className={cn('h-4 w-4 shrink-0 text-muted-foreground transition-transform', open && 'rotate-180')}
          />
        )}
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
            className="overflow-hidden"
          >
            <div className="space-y-3 border-t border-border/60 p-3.5">
              {dimension.reasoning && <p className="text-xs leading-relaxed text-muted-foreground">{dimension.reasoning}</p>}
              {!!(dimension.evidence || []).length && (
                <ul className="space-y-1.5">
                  {dimension.evidence.map((e, i) => (
                    <li key={`${dimension.key}-ev-${i}`} className="flex gap-2 text-xs text-foreground/80">
                      <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-accent" />
                      {e.detail}
                    </li>
                  ))}
                </ul>
              )}
              {!!(dimension.suggestions || []).length && (
                <div className="flex items-start gap-2 rounded-lg bg-primary/8 p-2.5 text-xs text-primary">
                  <Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                  <span>{dimension.suggestions[0]}</span>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default function ScorecardBreakdown({ dimensions = [] }) {
  const evidenced = dimensions.filter((d) => d.score > 0 || (d.evidence || []).length > 0)
  const unevidenced = dimensions.filter((d) => !evidenced.includes(d))
  const sorted = evidenced.slice().sort((a, b) => b.score - a.score)

  return (
    <div className="space-y-2.5">
      {sorted.map((d) => (
        <DimensionRow key={d.key} dimension={d} />
      ))}
      {!!unevidenced.length && (
        <div className="flex flex-wrap items-center gap-2 rounded-xl border border-dashed border-border p-3.5">
          <span className="text-xs text-muted-foreground">Awaiting evidence:</span>
          {unevidenced.map((d) => (
            <Badge key={d.key} variant="outline" size="sm">
              {d.label}
            </Badge>
          ))}
        </div>
      )}
    </div>
  )
}
