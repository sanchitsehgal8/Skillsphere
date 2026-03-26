function parseAdjacencyPaths(paths = []) {
  return paths
    .map((raw) => {
      const m = String(raw).match(/^\s*(.+?)\s*->\s*(.+?)\s*\(distance\s*(\d+)\)\s*$/i)
      if (!m) return null
      return {
        from: m[1].trim(),
        to: m[2].trim(),
        distance: Number(m[3]),
      }
    })
    .filter(Boolean)
}

function shortLabel(text) {
  if (!text) return ''
  return text.length > 20 ? `${text.slice(0, 20)}…` : text
}

export default function AdjacencyPathGraph({ paths }) {
  const links = parseAdjacencyPaths(paths)

  if (!links.length) {
    return <p className="subtle-copy">No adjacency graph available for this match.</p>
  }

  const fromNodes = [...new Set(links.map((l) => l.from))]
  const toNodes = [...new Set(links.map((l) => l.to))]

  const width = 560
  const rowGap = 48
  const rows = Math.max(fromNodes.length, toNodes.length)
  const height = Math.max(180, rows * rowGap + 40)

  const leftX = 120
  const rightX = width - 120
  const topY = 34

  const fromY = new Map(fromNodes.map((n, i) => [n, topY + i * rowGap]))
  const toY = new Map(toNodes.map((n, i) => [n, topY + i * rowGap]))

  const strokeForDistance = (d) => {
    if (d <= 1) return '#2f79ff'
    if (d === 2) return '#4d96ff'
    return '#85b7ff'
  }

  return (
    <div className="adj-graph-wrap">
      <svg viewBox={`0 0 ${width} ${height}`} className="adj-graph-svg" role="img" aria-label="Adjacency path graph">
        {links.map((l, i) => {
          const y1 = fromY.get(l.from)
          const y2 = toY.get(l.to)
          const c1x = leftX + 110
          const c2x = rightX - 110
          const d = `M ${leftX + 64} ${y1} C ${c1x} ${y1}, ${c2x} ${y2}, ${rightX - 64} ${y2}`
          return (
            <path
              key={`edge-${l.from}-${l.to}-${i}`}
              d={d}
              fill="none"
              stroke={strokeForDistance(l.distance)}
              strokeWidth={2}
              opacity={0.9}
            />
          )
        })}

        {fromNodes.map((n) => {
          const y = fromY.get(n)
          return (
            <g key={`from-${n}`}>
              <rect x={24} y={y - 14} width={184} height={28} rx={8} className="adj-node from" />
              <text x={116} y={y + 5} textAnchor="middle" className="adj-node-label">{shortLabel(n)}</text>
            </g>
          )
        })}

        {toNodes.map((n) => {
          const y = toY.get(n)
          return (
            <g key={`to-${n}`}>
              <rect x={width - 208} y={y - 14} width={184} height={28} rx={8} className="adj-node to" />
              <text x={width - 116} y={y + 5} textAnchor="middle" className="adj-node-label">{shortLabel(n)}</text>
            </g>
          )
        })}
      </svg>
      <p className="subtle-copy">Left: candidate strengths · Right: role requirements with transfer paths.</p>
    </div>
  )
}
