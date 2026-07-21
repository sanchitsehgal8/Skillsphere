import { PolarAngleAxis, PolarGrid, Radar, RadarChart, ResponsiveContainer } from 'recharts'

const MAX_SPOKES = 7
const MIN_SPOKES = 3

function buildMetrics(dimensions = []) {
  const evidenced = dimensions.filter((d) => d.score > 0 || (d.evidence || []).length)
  const ranked = evidenced.slice().sort((a, b) => b.score - a.score).slice(0, MAX_SPOKES)
  if (ranked.length < MIN_SPOKES) return null
  return ranked.map((d) => ({ label: d.label, value: Math.round(d.score) }))
}

export default function SkillRadarChart({ dimensions }) {
  const metrics = buildMetrics(dimensions)
  if (!metrics) {
    return (
      <p className="rounded-xl border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
        Not enough evidenced dimensions yet for a radar view — add GitHub or resume evidence.
      </p>
    )
  }

  return (
    <div className="grid items-center gap-4 sm:grid-cols-[1fr_auto]">
      <div className="h-[280px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={metrics} outerRadius="72%">
            <defs>
              <linearGradient id="radar-fill" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.55} />
                <stop offset="100%" stopColor="hsl(var(--accent))" stopOpacity={0.35} />
              </linearGradient>
            </defs>
            <PolarGrid stroke="hsl(var(--border))" />
            <PolarAngleAxis
              dataKey="label"
              tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
            />
            <Radar
              dataKey="value"
              stroke="hsl(var(--primary))"
              strokeWidth={2}
              fill="url(#radar-fill)"
              fillOpacity={1}
              isAnimationActive
              animationDuration={900}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-2 gap-x-5 gap-y-2 sm:grid-cols-1">
        {metrics.map((m) => (
          <div key={m.label} className="flex items-center justify-between gap-3 text-sm">
            <span className="truncate text-muted-foreground">{m.label}</span>
            <span className="font-mono text-xs font-semibold text-foreground">{m.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
