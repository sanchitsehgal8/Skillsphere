import { createContext, useCallback, useContext, useState } from 'react'
import * as ToastPrimitive from '@radix-ui/react-toast'
import { CheckCircle2, Info, TriangleAlert, X } from 'lucide-react'
import { cn } from '../../lib/utils'

const ToastContext = createContext(null)

const icons = {
  success: { Icon: CheckCircle2, cls: 'text-success' },
  error: { Icon: TriangleAlert, cls: 'text-danger' },
  info: { Icon: Info, cls: 'text-accent' },
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const toast = useCallback(({ title, description, variant = 'info', duration = 4200 }) => {
    const id = `${Date.now()}-${Math.round(performance.now())}`
    setToasts((prev) => [...prev, { id, title, description, variant, duration }])
  }, [])

  const dismiss = useCallback((id) => setToasts((prev) => prev.filter((t) => t.id !== id)), [])

  return (
    <ToastContext.Provider value={{ toast }}>
      <ToastPrimitive.Provider swipeDirection="right">
        {children}
        {toasts.map(({ id, title, description, variant, duration }) => {
          const { Icon, cls } = icons[variant] || icons.info
          return (
            <ToastPrimitive.Root
              key={id}
              duration={duration}
              onOpenChange={(open) => !open && dismiss(id)}
              className={cn(
                'group pointer-events-auto flex items-start gap-3 rounded-xl border border-border bg-popover p-4 shadow-elevated',
                'data-[state=open]:animate-fade-up data-[swipe=end]:animate-fade-in',
              )}
            >
              <Icon className={cn('mt-0.5 h-5 w-5 shrink-0', cls)} />
              <div className="flex-1">
                <ToastPrimitive.Title className="text-sm font-semibold text-foreground">{title}</ToastPrimitive.Title>
                {description && (
                  <ToastPrimitive.Description className="mt-0.5 text-xs text-muted-foreground">
                    {description}
                  </ToastPrimitive.Description>
                )}
              </div>
              <ToastPrimitive.Close className="text-muted-foreground transition-colors hover:text-foreground">
                <X className="h-4 w-4" />
              </ToastPrimitive.Close>
            </ToastPrimitive.Root>
          )
        })}
        <ToastPrimitive.Viewport className="fixed bottom-0 right-0 z-[100] flex w-[calc(100%-2rem)] max-w-sm flex-col gap-2.5 p-4 outline-none" />
      </ToastPrimitive.Provider>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}
