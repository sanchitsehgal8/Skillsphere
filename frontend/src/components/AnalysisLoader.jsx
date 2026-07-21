import { motion } from 'framer-motion'
import { Check, Loader2 } from 'lucide-react'
import { LogoMark } from './brand/Logo'
import { Meter } from './ui/meter'
import { cn } from '../lib/utils'

/**
 * Full-panel animated "working" state shown between clicking Analyze and
 * landing on the results page. Steps progress through pending -> active ->
 * done based on `activeIndex`; `detail` renders live sub-status text
 * (e.g. "Candidate 2 of 3") beneath the active step.
 */
export default function AnalysisLoader({ steps, activeIndex, detail }) {
  const progressPct = steps.length ? Math.min(100, (activeIndex / steps.length) * 100 + 100 / steps.length / 2) : 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className="flex flex-col items-center gap-8 rounded-2xl border border-border bg-surface/40 px-6 py-16 text-center sm:px-10"
    >
      <div className="relative grid h-24 w-24 place-items-center">
        <motion.span
          className="absolute inset-0 rounded-full bg-[linear-gradient(135deg,hsl(var(--primary)/0.35),hsl(var(--accent)/0.25))] blur-xl"
          animate={{ scale: [1, 1.25, 1], opacity: [0.6, 1, 0.6] }}
          transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut' }}
        />
        <motion.div
          className="absolute inset-0 rounded-full border-2 border-dashed border-primary/40"
          animate={{ rotate: 360 }}
          transition={{ duration: 6, repeat: Infinity, ease: 'linear' }}
        />
        <motion.div
          animate={{ scale: [1, 1.08, 1] }}
          transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
          className="relative grid h-16 w-16 place-items-center rounded-full bg-surface shadow-lg ring-1 ring-border"
        >
          <LogoMark size={34} />
        </motion.div>
      </div>

      <div className="space-y-2">
        <h3 className="font-display text-xl font-semibold text-foreground">Analyzing candidates…</h3>
        <p className="mx-auto max-w-sm text-sm text-muted-foreground">
          Mining GitHub, parsing résumé evidence, and scoring fit — every number will cite its source.
        </p>
      </div>

      <div className="w-full max-w-sm">
        <Meter value={progressPct} tone="gradient" animate={false} />
      </div>

      <ol className="w-full max-w-sm space-y-3 text-left">
        {steps.map((step, i) => {
          const state = i < activeIndex ? 'done' : i === activeIndex ? 'active' : 'pending'
          return (
            <li key={step} className="flex items-start gap-3">
              <span
                className={cn(
                  'mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full border transition-colors duration-300',
                  state === 'done' && 'border-success bg-success text-success-foreground',
                  state === 'active' && 'border-primary bg-primary/10 text-primary',
                  state === 'pending' && 'border-border text-muted-foreground/50',
                )}
              >
                {state === 'done' && <Check className="h-3.5 w-3.5" />}
                {state === 'active' && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              </span>
              <div className="min-w-0 flex-1">
                <p
                  className={cn(
                    'text-sm font-medium transition-colors duration-300',
                    state === 'pending' ? 'text-muted-foreground/60' : 'text-foreground',
                  )}
                >
                  {step}
                </p>
                {state === 'active' && detail && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="mt-0.5 truncate text-xs text-muted-foreground"
                  >
                    {detail}
                  </motion.p>
                )}
              </div>
            </li>
          )
        })}
      </ol>
    </motion.div>
  )
}
