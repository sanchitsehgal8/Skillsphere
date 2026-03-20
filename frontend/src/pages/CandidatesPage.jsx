import { useMemo, useState } from 'react'
import TopBar from '../components/TopBar'

export default function CandidatesPage({ analysesByCandidate, theme, onToggleTheme }) {
  const items = Object.values(analysesByCandidate)
  const [query, setQuery] = useState('')
  const [minScore, setMinScore] = useState(0)
  const [onlyDirect, setOnlyDirect] = useState(false)
  const [onlyAdjacency, setOnlyAdjacency] = useState(false)
  const [scoreSort, setScoreSort] = useState('default')

  const filteredItems = useMemo(() => {
    const filtered = items.filter((item) => {
      const matchesQuery = item.candidateId.toLowerCase().includes(query.toLowerCase())
      const matchesScore = (item.score || 0) * 100 >= minScore
      const hasDirect = (item.direct_matches || []).length > 0
      const hasAdj = (item.adjacent_support || []).length > 0
      const matchesDirect = !onlyDirect || hasDirect
      const matchesAdj = !onlyAdjacency || hasAdj
      return matchesQuery && matchesScore && matchesDirect && matchesAdj
    })

    if (scoreSort === 'desc') {
      filtered.sort((a, b) => (b.score || 0) - (a.score || 0))
    } else if (scoreSort === 'asc') {
      filtered.sort((a, b) => (a.score || 0) - (b.score || 0))
    }

    return filtered
  }, [items, minScore, onlyAdjacency, onlyDirect, query, scoreSort])

  function exportCsv() {
    if (!filteredItems.length) return
    const headers = ['candidateId', 'score', 'time_to_productivity_pomodoros', 'time_to_productivity_hours', 'time_to_productivity_sprints', 'direct_matches', 'adjacent_support']
    const rows = filteredItems.map((item) => [
      item.candidateId,
      item.score,
      item.time_to_productivity_pomodoros ?? '',
      item.time_to_productivity_hours ?? '',
      item.time_to_productivity_sprints ?? '',
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
        <div className="sort-control">
          <label>Sort by score</label>
          <select value={scoreSort} onChange={(e) => setScoreSort(e.target.value)}>
            <option value="default">Default</option>
            <option value="desc">High to Low</option>
            <option value="asc">Low to High</option>
          </select>
        </div>
      </div>

      <div className="candidate-grid">
        {filteredItems.length === 0 && <div className="card">No candidates match the current filters.</div>}

        {filteredItems.map((item) => (
          <div className="card" key={item.candidateId}>
            <div className="candidate-head">
              <h3>{item.candidateId}</h3>
              <span className="pill">{Math.round(item.score * 100)}%</span>
            </div>
            <p>
              <strong>TTP:</strong>{' '}
              {item.time_to_productivity_pomodoros
                ? `${item.time_to_productivity_pomodoros.toFixed(1)} pomodoros (~${(item.time_to_productivity_hours || 0).toFixed(1)}h, ~${(item.time_to_productivity_sprints || 0).toFixed(2)} sprints)`
                : 'n/a'}
            </p>
            <p><strong>Direct matches:</strong> {item.direct_matches?.join(', ') || 'None'}</p>
            <p><strong>Adjacency support:</strong> {item.adjacent_support?.join('; ') || 'None'}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
