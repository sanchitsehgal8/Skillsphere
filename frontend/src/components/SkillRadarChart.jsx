function clamp(n, min = 0, max = 100) {
  return Math.max(min, Math.min(max, n))
}

function polarToCartesian(cx, cy, radius, angleDeg) {
  const rad = ((angleDeg - 90) * Math.PI) / 180
  return {
    x: cx + radius * Math.cos(rad),
    y: cy + radius * Math.sin(rad),
  }
}

function polygonPoints(cx, cy, radius, count) {
  const pts = []
  for (let i = 0; i < count; i += 1) {
    const angle = (360 / count) * i
    const p = polarToCartesian(cx, cy, radius, angle)
    pts.push(`${p.x},${p.y}`)
  }
  return pts.join(' ')
}

function extractLearningVelocity(candidate) {
  // Explanation usually contains: "Learning velocity: 0.97."
  const text = candidate?.explanation || ''
  const m = text.match(/Learning velocity:\s*([0-9]*\.?[0-9]+)/i)
  if (!m) return 50
  const v = Number(m[1])
  if (Number.isNaN(v)) return 50
  return clamp(v * 100)
}

function buildMetrics(candidate) {
  const score = clamp((candidate?.score || 0) * 100)
  const learningVelocity = extractLearningVelocity(candidate)

  const directCount = (candidate?.direct_matches || []).length
  const adjCount = (candidate?.adjacent_support || []).length
  const directCoverage = clamp(directCount * 22)
  const adjacencyPotential = clamp(adjCount * 22 + (adjCount > 0 ? 20 : 0))

  const ttpPoms = candidate?.time_to_productivity_pomodoros
  const productivityReadiness =
    ttpPoms == null ? 50 : clamp(100 - Math.min(100, (ttpPoms / 60) * 100))

  const repos = candidate?.ui?.repos || 0
  const stars = candidate?.ui?.stars || 0
  const evidenceStrength = clamp(Math.log1p(repos) * 18 + Math.log1p(stars) * 10)

  return [
    { label: 'Match', value: score },
    { label: 'Velocity', value: learningVelocity },
    { label: 'Direct Fit', value: directCoverage },
    { label: 'Adjacency', value: adjacencyPotential },
    { label: 'Readiness', value: productivityReadiness },
    { label: 'Evidence', value: evidenceStrength },
  ]
}

export default function SkillRadarChart({ candidate }) {
  const metrics = buildMetrics(candidate)
  const size = 260
  const cx = size / 2
  const cy = size / 2
  const outerR = 88
  const levels = [20, 40, 60, 80, 100]

  const valuePoints = metrics
    .map((m, i) => {
      const angle = (360 / metrics.length) * i
      const p = polarToCartesian(cx, cy, (outerR * m.value) / 100, angle)
      return `${p.x},${p.y}`
    })
    .join(' ')

  return (
    <div className="radar-wrap">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="radar-svg">
        {levels.map((lv) => (
          <polygon
            key={lv}
            points={polygonPoints(cx, cy, (outerR * lv) / 100, metrics.length)}
            fill="none"
            stroke="var(--border)"
            strokeWidth="1"
            opacity={0.8}
          />
        ))}

        {metrics.map((m, i) => {
          const angle = (360 / metrics.length) * i
          const edge = polarToCartesian(cx, cy, outerR, angle)
          return (
            <line
              key={m.label}
              x1={cx}
              y1={cy}
              x2={edge.x}
              y2={edge.y}
              stroke="var(--border)"
              strokeWidth="1"
            />
          )
        })}

        <polygon points={valuePoints} fill="rgba(61, 131, 255, 0.35)" stroke="#5ba3ff" strokeWidth="2" />

        {metrics.map((m, i) => {
          const angle = (360 / metrics.length) * i
          const labelPos = polarToCartesian(cx, cy, outerR + 22, angle)
          return (
            <text
              key={`${m.label}-lbl`}
              x={labelPos.x}
              y={labelPos.y}
              textAnchor="middle"
              dominantBaseline="middle"
              className="radar-label"
            >
              {m.label}
            </text>
          )
        })}
      </svg>

      <div className="radar-legend">
        {metrics.map((m) => (
          <div key={m.label} className="radar-legend-item">
            <span>{m.label}</span>
            <strong>{m.value.toFixed(0)}</strong>
          </div>
        ))}
      </div>
    </div>
  )
}
