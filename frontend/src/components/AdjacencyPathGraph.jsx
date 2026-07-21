import { motion } from 'framer-motion'

function shortLabel(text) {
  if (!text) return ''
  return text.length > 22 ? `${text.slice(0, 22)}…` : text
}

export default function AdjacencyPathGraph({ coverage = [] }) {
  const links = coverage
    .filter((c) => c.status === 'adjacent' && c.evidence_skill)
    .map((c) => ({ from: c.evidence_skill, to: c.requirement, distance: c.distance ?? 2 }))

  if (!links.length) {
    return (
      <p className="rounded-xl border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
        No adjacency transfer paths — every requirement is directly matched or missing.
      </p>
    )
  }

  const fromNodes = [...new Set(links.map((l) => l.from))]
  const toNodes = [...new Set(links.map((l) => l.to))]

  const width = 560
  const rowGap = 52
  const rows = Math.max(fromNodes.length, toNodes.length)
  const height = Math.max(180, rows * rowGap + 40)
  const leftX = 120
  const rightX = width - 120
  const topY = 34

  const fromY = new Map(fromNodes.map((n, i) => [n, topY + i * rowGap]))
  const toY = new Map(toNodes.map((n, i) => [n, topY + i * rowGap]))

  const opacityForDistance = (d) => (d <= 1 ? 0.95 : d === 2 ? 0.7 : 0.45)

  return (
    <div className="rounded-xl border border-border bg-surface/40 p-4">
      <div className="overflow-x-auto">
        <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full min-w-[520px]" role="img" aria-label="Adjacency transfer paths">
          <defs>
            <linearGradient id="adj-edge" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="hsl(var(--accent))" />
              <stop offset="100%" stopColor="hsl(var(--primary))" />
            </linearGradient>
          </defs>

          {links.map((l, i) => {
            const y1 = fromY.get(l.from)
            const y2 = toY.get(l.to)
            const d = `M ${leftX + 4} ${y1} C ${leftX + 120} ${y1}, ${rightX - 120} ${y2}, ${rightX - 4} ${y2}`
            return (
              <motion.path
                key={`edge-${l.from}-${l.to}-${i}`}
                d={d}
                fill="none"
                stroke="url(#adj-edge)"
                strokeWidth={2}
                opacity={opacityForDistance(l.distance)}
                initial={{ pathLength: 0 }}
                whileInView={{ pathLength: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.9, delay: i * 0.08, ease: 'easeInOut' }}
              />
            )
          })}

          {fromNodes.map((n) => {
            const y = fromY.get(n)
            return (
              <g key={`from-${n}`}>
                <rect x={12} y={y - 15} width={200} height={30} rx={9} fill="hsl(var(--accent) / 0.12)" stroke="hsl(var(--accent) / 0.4)" />
                <text x={112} y={y + 4} textAnchor="middle" fontSize="11" fill="hsl(var(--foreground))" fontWeight="500">
                  {shortLabel(n)}
                </text>
              </g>
            )
          })}

          {toNodes.map((n) => {
            const y = toY.get(n)
            return (
              <g key={`to-${n}`}>
                <rect x={width - 212} y={y - 15} width={200} height={30} rx={9} fill="hsl(var(--primary) / 0.12)" stroke="hsl(var(--primary) / 0.4)" />
                <text x={width - 112} y={y + 4} textAnchor="middle" fontSize="11" fill="hsl(var(--foreground))" fontWeight="500">
                  {shortLabel(n)}
                </text>
              </g>
            )
          })}
        </svg>
      </div>
      <div className="mt-2 flex items-center justify-between text-2xs text-muted-foreground">
        <span>Candidate strengths</span>
        <span>Role requirements</span>
      </div>
    </div>
  )
}
