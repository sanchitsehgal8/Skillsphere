import { forwardRef } from 'react'
import { cn } from '../../lib/utils'

export const Card = forwardRef(function Card({ className, interactive = false, ...props }, ref) {
  return (
    <div
      ref={ref}
      className={cn(
        'rounded-2xl border border-border bg-card text-card-foreground shadow-card',
        interactive &&
          'transition-all duration-300 hover:-translate-y-1 hover:shadow-elevated hover:border-foreground/15',
        className,
      )}
      {...props}
    />
  )
})

export function CardHeader({ className, ...props }) {
  return <div className={cn('flex flex-col gap-1.5 p-6', className)} {...props} />
}

export function CardTitle({ className, ...props }) {
  return (
    <h3
      className={cn('font-display text-lg font-semibold tracking-tight text-foreground', className)}
      {...props}
    />
  )
}

export function CardDescription({ className, ...props }) {
  return <p className={cn('text-sm text-muted-foreground', className)} {...props} />
}

export function CardContent({ className, ...props }) {
  return <div className={cn('p-6 pt-0', className)} {...props} />
}

export function CardFooter({ className, ...props }) {
  return <div className={cn('flex items-center p-6 pt-0', className)} {...props} />
}
