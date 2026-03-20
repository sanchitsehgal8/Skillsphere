import { useMemo, useState } from 'react'
import TopBar from '../components/TopBar'

export default function CandidatesPage({ analysesByCandidate, theme, onToggleTheme }) {
  const items = Object.values(analysesByCandidate)
  const [query, setQuery] = useState('')
  const [minScore, setMinScore] = useState(0)
  const [onlyDirect, setOnlyDirect] = useState(false)
  const [onlyAdjacency, setOnlyAdjacency] = useState(false)

  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      const matchesQuery = item.candidateId.toLowerCase().includes(query.toLowerCase())
      const matchesScore = (item.score || 0) * 100 >= minScore
      const hasDirect = (item.direct_matches || []).length > 0
      const hasAdj = (item.adjacent_support || []).length > 0
      const matchesDirect = !onlyDirect || hasDirect
      const matchesAdj = !onlyAdjacency || hasAdj
      return matchesQuery && matchesScore && matchesDirect && matchesAdj
    })
  }, [items, minScore, onlyAdjacency, onlyDirect, query])

  function exportCsv() {
    if (!filteredItems.length) return
    const headers = ['candidateId', 'score', 'time_to_productivity_days', 'direct_matches', 'adjacent_support']
    const rows = filteredItems.map((item) => [
      item.candidateId,
      item.score,
      item.time_to_productivity_days ?? '',
      (item.direct_matches || []).join('|'),
      (item.adjacent_support || []).join('|'),
    ])
    const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `skillsphere-candidates-${Date.now()}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="page">
      <TopBar
        title="All Candidates"
        subtitle="Ranked with direct + adjacency potential"
        onExport={exportCsv}
        theme={theme}
        onToggleTheme={onToggleTheme}
      />

      <div className="card filter-bar">
        <input
          placeholder="Filter by candidate handle..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="filter-control">
          <label>Min Score: {minScore}%</label>
          <input
            type="range"
            min="0"
            max="100"
            step="1"
            value={minScore}
            onChange={(e) => setMinScore(Number(e.target.value))}
          />
        </div>
        <label className="check-inline">
          <input
            type="checkbox"
            checked={onlyDirect}
            onChange={(e) => setOnlyDirect(e.target.checked)}
          />
          Only with direct matches
        </label>
        <label className="check-inline">
          <input
            type="checkbox"
            checked={onlyAdjacency}
            onChange={(e) => setOnlyAdjacency(e.target.checked)}
          />
          Only with adjacency support
        </label>
      </div>

      <div className="candidate-grid">
        {filteredItems.length === 0 && <div className="card">No candidates match the current filters.</div>}

        {filteredItems.map((item) => (
          <div className="card" key={item.candidateId}>
            <div className="candidate-head">
              <h3>{item.candidateId}</h3>
              <span className="pill">{Math.round(item.score * 100)}%</span>
            </div>
            <p><strong>TTP:</strong> {item.time_to_productivity_days ? `${item.time_to_productivity_days.toFixed(1)} days` : 'n/a'}</p>
            <p><strong>Direct matches:</strong> {item.direct_matches?.join(', ') || 'None'}</p>
            <p><strong>Adjacency support:</strong> {item.adjacent_support?.join('; ') || 'None'}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
