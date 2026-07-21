import { motion } from 'framer-motion'
import { cn } from '../../lib/utils'

const toneBar = {
  primary: 'bg-primary',
  accent: 'bg-accent',
  success: 'bg-success',
  warning: 'bg-warning',
  danger: 'bg-danger',
  gradient: 'bg-[linear-gradient(90deg,hsl(var(--primary)),hsl(var(--accent)))]',
}

/** Animated horizontal progress meter (0–100). */
export function Meter({ value = 0, tone = 'primary', className, trackClassName, animate = true }) {
  const pct = Math.max(0, Math.min(100, value))
  return (
    <div className={cn('h-2 w-full overflow-hidden rounded-full bg-muted/70', trackClassName)}>
      <motion.div
        className={cn('h-full rounded-full', toneBar[tone] || toneBar.primary, className)}
        initial={animate ? { width: 0 } : false}
        whileInView={animate ? { width: `${pct}%` } : undefined}
        animate={animate ? undefined : { width: `${pct}%` }}
        viewport={{ once: true, margin: '-40px' }}
        transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
        style={animate ? undefined : { width: `${pct}%` }}
      />
    </div>
  )
}

/** Circular confidence / score ring. */
export function Ring({ value = 0, size = 56, stroke = 5, tone = 'primary', label, className }) {
  const pct = Math.max(0, Math.min(100, value))
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const toneColor = {
    primary: 'hsl(var(--primary))',
    accent: 'hsl(var(--accent))',
    success: 'hsl(var(--success))',
    warning: 'hsl(var(--warning))',
    danger: 'hsl(var(--danger))',
  }[tone]
  return (
    <div className={cn('relative inline-grid place-items-center', className)} style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="hsl(var(--muted))" strokeWidth={stroke} />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={toneColor}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          whileInView={{ strokeDashoffset: c - (c * pct) / 100 }}
          viewport={{ once: true }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
        />
      </svg>
      <span className="absolute font-mono text-xs font-semibold text-foreground">
        {label ?? `${Math.round(pct)}`}
      </span>
    </div>
  )
}
