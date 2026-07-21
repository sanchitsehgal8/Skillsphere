import { motion } from 'framer-motion'
import { Card } from '../ui/card'
import { cn } from '../../lib/utils'

const toneStyles = {
  primary: 'text-primary',
  accent: 'text-accent',
  success: 'text-success',
  warning: 'text-warning',
}

export function StatCard({ icon: Icon, label, value, suffix, hint, tone = 'primary', delay = 0, loading }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      <Card className="relative overflow-hidden p-5">
        <div
          className={cn(
            'absolute -right-6 -top-6 h-24 w-24 rounded-full opacity-[0.07] blur-2xl',
            tone === 'primary' && 'bg-primary',
            tone === 'accent' && 'bg-accent',
            tone === 'success' && 'bg-success',
            tone === 'warning' && 'bg-warning',
          )}
        />
        <div className="mb-4 flex items-center justify-between">
          <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</span>
          {Icon && (
            <span className={cn('grid h-9 w-9 place-items-center rounded-xl bg-secondary/60', toneStyles[tone])}>
              <Icon className="h-4.5 w-4.5" />
            </span>
          )}
        </div>
        <div className="flex items-baseline gap-1">
          <span className="font-display text-3xl font-bold tracking-tight text-foreground">
            {loading ? '—' : value}
          </span>
          {suffix && !loading && <span className="text-sm text-muted-foreground">{suffix}</span>}
        </div>
        {hint && <p className="mt-1.5 text-xs text-muted-foreground">{hint}</p>}
      </Card>
    </motion.div>
  )
}
