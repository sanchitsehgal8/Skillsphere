import * as DropdownPrimitive from '@radix-ui/react-dropdown-menu'
import { cn } from '../../lib/utils'

export const DropdownMenu = DropdownPrimitive.Root
export const DropdownMenuTrigger = DropdownPrimitive.Trigger

export function DropdownMenuContent({ className, align = 'end', sideOffset = 8, ...props }) {
  return (
    <DropdownPrimitive.Portal>
      <DropdownPrimitive.Content
        align={align}
        sideOffset={sideOffset}
        className={cn(
          'z-50 min-w-[13rem] overflow-hidden rounded-xl border border-border bg-popover p-1.5 text-popover-foreground shadow-elevated',
          'data-[state=open]:animate-fade-up',
          className,
        )}
        {...props}
      />
    </DropdownPrimitive.Portal>
  )
}

export function DropdownMenuItem({ className, inset, ...props }) {
  return (
    <DropdownPrimitive.Item
      className={cn(
        'relative flex cursor-pointer select-none items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-foreground/90 outline-none transition-colors',
        'focus:bg-secondary focus:text-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50',
        inset && 'pl-9',
        className,
      )}
      {...props}
    />
  )
}

export function DropdownMenuLabel({ className, ...props }) {
  return <DropdownPrimitive.Label className={cn('px-3 py-1.5 text-2xs font-semibold uppercase tracking-wide text-muted-foreground', className)} {...props} />
}

export function DropdownMenuSeparator({ className, ...props }) {
  return <DropdownPrimitive.Separator className={cn('my-1.5 h-px bg-border', className)} {...props} />
}
