import { cva } from 'class-variance-authority'
import { cn } from '../../lib/utils'

const badgeVariants = cva(
  'inline-flex items-center gap-1.5 rounded-full border font-medium transition-colors whitespace-nowrap',
  {
    variants: {
      variant: {
        default: 'border-border bg-secondary/60 text-secondary-foreground',
        primary: 'border-primary/25 bg-primary/12 text-primary',
        accent: 'border-accent/25 bg-accent/12 text-accent',
        success: 'border-success/25 bg-success/12 text-success',
        warning: 'border-warning/30 bg-warning/15 text-warning',
        danger: 'border-danger/25 bg-danger/12 text-danger',
        outline: 'border-border bg-transparent text-muted-foreground',
      },
      size: {
        sm: 'px-2 py-0.5 text-2xs',
        md: 'px-2.5 py-1 text-xs',
      },
    },
    defaultVariants: { variant: 'default', size: 'md' },
  },
)

const toneToVariant = { success: 'success', warning: 'warning', danger: 'danger' }

export function Badge({ className, variant, size, tone, ...props }) {
  const resolved = tone ? toneToVariant[tone] || 'default' : variant
  return <span className={cn(badgeVariants({ variant: resolved, size }), className)} {...props} />
}

export { badgeVariants }
