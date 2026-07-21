import { cn, initials } from '../../lib/utils'

export function Skeleton({ className }) {
  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-lg bg-muted/60',
        'after:absolute after:inset-0 after:-translate-x-full after:animate-shimmer',
        'after:bg-[linear-gradient(90deg,transparent,hsl(var(--foreground)/0.06),transparent)]',
        className,
      )}
    />
  )
}

export function Separator({ className, orientation = 'horizontal' }) {
  return (
    <div
      role="separator"
      className={cn('bg-border', orientation === 'vertical' ? 'h-full w-px' : 'h-px w-full', className)}
    />
  )
}

const avatarSizes = { sm: 'h-8 w-8 text-2xs', md: 'h-10 w-10 text-xs', lg: 'h-12 w-12 text-sm', xl: 'h-16 w-16 text-lg' }

export function Avatar({ name = '', size = 'md', className }) {
  return (
    <div
      className={cn(
        'inline-grid shrink-0 place-items-center rounded-full font-semibold',
        'bg-[linear-gradient(135deg,hsl(var(--primary)/0.85),hsl(var(--accent)/0.85))] text-primary-foreground',
        'ring-2 ring-background',
        avatarSizes[size],
        className,
      )}
    >
      {initials(name)}
    </div>
  )
}

export function EmptyState({ icon: Icon, title, description, action, className }) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-3 px-6 py-14 text-center', className)}>
      {Icon && (
        <div className="grid h-14 w-14 place-items-center rounded-2xl border border-border bg-secondary/50 text-muted-foreground">
          <Icon className="h-6 w-6" />
        </div>
      )}
      <div className="space-y-1">
        <p className="font-display text-base font-semibold text-foreground">{title}</p>
        {description && <p className="mx-auto max-w-sm text-sm text-muted-foreground">{description}</p>}
      </div>
      {action}
    </div>
  )
}

export function StatusDot({ tone = 'success', pulse = true, className }) {
  const color = { success: 'bg-success', warning: 'bg-warning', danger: 'bg-danger', primary: 'bg-primary' }[tone]
  return (
    <span className={cn('relative inline-flex h-2 w-2', className)}>
      {pulse && <span className={cn('absolute inline-flex h-full w-full rounded-full opacity-60 animate-ping', color)} />}
      <span className={cn('relative inline-flex h-2 w-2 rounded-full', color)} />
    </span>
  )
}
