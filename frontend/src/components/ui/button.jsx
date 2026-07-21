import { forwardRef } from 'react'
import { cva } from 'class-variance-authority'
import { Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98] select-none',
  {
    variants: {
      variant: {
        primary:
          'bg-primary text-primary-foreground shadow-[0_1px_0_hsl(var(--foreground)/0.1)_inset,0_8px_24px_-10px_hsl(var(--primary)/0.7)] hover:brightness-110 hover:-translate-y-0.5',
        secondary:
          'bg-secondary text-secondary-foreground border border-border hover:bg-secondary/70',
        outline:
          'border border-border bg-transparent hover:bg-secondary/60 hover:border-foreground/20',
        ghost: 'hover:bg-secondary/70 text-foreground/80 hover:text-foreground',
        subtle: 'bg-muted/60 text-foreground hover:bg-muted',
        danger: 'bg-danger text-danger-foreground hover:brightness-110',
        gradient:
          'text-primary-foreground bg-primary bg-[linear-gradient(180deg,hsl(0_0%_100%/0.16),transparent_60%)] shadow-[0_1px_0_hsl(0_0%_100%/0.2)_inset,0_10px_22px_-12px_hsl(var(--primary)/0.85)] hover:brightness-[1.07] hover:-translate-y-0.5',
        link: 'text-primary underline-offset-4 hover:underline px-0',
      },
      size: {
        sm: 'h-8 px-3 text-xs',
        md: 'h-10 px-4 text-sm',
        lg: 'h-12 px-6 text-[0.95rem]',
        icon: 'h-10 w-10',
        'icon-sm': 'h-8 w-8',
      },
    },
    defaultVariants: { variant: 'primary', size: 'md' },
  },
)

export const Button = forwardRef(function Button(
  { className, variant, size, loading = false, children, disabled, ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      className={cn(buttonVariants({ variant, size }), className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" />}
      {children}
    </button>
  )
})

export { buttonVariants }
