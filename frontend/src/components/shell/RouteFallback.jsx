import { LogoMark } from '../brand/Logo'

export function RouteFallback() {
  return (
    <div className="grid min-h-screen place-items-center bg-background">
      <div className="flex flex-col items-center gap-4">
        <div className="animate-pulse">
          <LogoMark size={44} />
        </div>
        <div className="h-1 w-32 overflow-hidden rounded-full bg-muted">
          <div className="h-full w-1/2 animate-marquee rounded-full bg-[linear-gradient(90deg,hsl(var(--primary)),hsl(var(--accent)))]" />
        </div>
      </div>
    </div>
  )
}
