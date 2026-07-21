import { cn } from '../../lib/utils'

/** SkillSphere mark — an orbital sphere of intelligence nodes. */
export function LogoMark({ className, size = 32 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      className={cn('shrink-0', className)}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="ss-grad" x1="4" y1="4" x2="36" y2="36" gradientUnits="userSpaceOnUse">
          <stop stopColor="hsl(var(--primary))" />
          <stop offset="1" stopColor="hsl(var(--accent))" />
        </linearGradient>
      </defs>
      <rect x="1" y="1" width="38" height="38" rx="11" fill="url(#ss-grad)" opacity="0.14" />
      <rect x="1" y="1" width="38" height="38" rx="11" stroke="url(#ss-grad)" strokeWidth="1.2" opacity="0.5" />
      <circle cx="20" cy="20" r="10.5" stroke="url(#ss-grad)" strokeWidth="1.6" />
      <ellipse cx="20" cy="20" rx="10.5" ry="4.4" stroke="url(#ss-grad)" strokeWidth="1.4" opacity="0.75" />
      <circle cx="20" cy="20" r="3.1" fill="url(#ss-grad)" />
      <circle cx="30.5" cy="20" r="1.9" fill="hsl(var(--accent))" />
      <circle cx="12.4" cy="12.4" r="1.7" fill="hsl(var(--primary))" />
      <circle cx="27" cy="28.5" r="1.5" fill="hsl(var(--primary))" />
    </svg>
  )
}

export function Logo({ className, textClassName, size = 32, showText = true }) {
  return (
    <span className={cn('inline-flex items-center gap-2.5', className)}>
      <LogoMark size={size} />
      {showText && (
        <span className={cn('font-display text-lg font-bold tracking-tightest text-foreground', textClassName)}>
          SkillSphere
        </span>
      )}
    </span>
  )
}
