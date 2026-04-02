import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import TopBar from '../components/TopBar'

export default function CandidatesPage({ analysesByCandidate, theme, onToggleTheme }) {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const items = Object.values(analysesByCandidate)
  const [query, setQuery] = useState(searchParams.get('query') || '')
  const [minScore, setMinScore] = useState(0)
  const [onlyDirect, setOnlyDirect] = useState(false)
  const [onlyAdjacency, setOnlyAdjacency] = useState(false)
  const [scoreSort, setScoreSort] = useState('default')
  const [page, setPage] = useState(1)

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

  useEffect(() => {
    const q = searchParams.get('query') || ''
    setQuery(q)
    setPage(1)
  }, [searchParams])

  const pageSize = 3
  const totalPages = Math.max(1, Math.ceil(filteredItems.length / pageSize))
  const safePage = Math.min(page, totalPages)
  const pagedItems = filteredItems.slice((safePage - 1) * pageSize, safePage * pageSize)

  function onPageChange(nextPage) {
    setPage(Math.min(totalPages, Math.max(1, nextPage)))
  }

  function exportCsv() {
    const headers = ['candidateId', 'score', 'time_to_productivity_pomodoros', 'time_to_productivity_hours', 'time_to_productivity_sprints', 'direct_matches', 'adjacent_support']
    const source = filteredItems.length
      ? filteredItems
      : [
          {
            candidateId: 'n/a',
            score: 0,
            time_to_productivity_pomodoros: '',
            time_to_productivity_hours: '',
            time_to_productivity_sprints: '',
            direct_matches: ['No candidates match current filters'],
            adjacent_support: [],
          },
        ]

    const rows = source.map((item) => [
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
    <div className="page candidates-page">
      <TopBar
        title="All Candidates"
        subtitle="Ranked with direct fit and adjacency potential"
        onExport={exportCsv}
        theme={theme}
        onToggleTheme={onToggleTheme}
      />

      <section className="card filter-panel candidates-filter-panel">
        <div className="filter-bar">
          <div className="filter-control search-block">
            <label>Search Handle</label>
            <div className="search-wrap">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" />
              </svg>
              <input
                placeholder="Search by candidate handle..."
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value)
                  setPage(1)
                }}
              />
            </div>
          </div>

          <div className="filter-control score-block">
            <label>Min Score</label>
            <div className="score-slider-row">
              <input
                type="range"
                min="0"
                max="100"
                step="1"
                value={minScore}
                onChange={(e) => {
                  setMinScore(Number(e.target.value))
                  setPage(1)
                }}
              />
              <span>{minScore}%</span>
            </div>
          </div>

          <div className="filter-control checkbox-block">
            <label className="check-inline">
              <input
                type="checkbox"
                checked={onlyDirect}
                onChange={(e) => {
                  setOnlyDirect(e.target.checked)
                  setPage(1)
                }}
              />
              <span className="check-text">Only with direct matches</span>
            </label>

            <label className="check-inline">
              <input
                type="checkbox"
                checked={onlyAdjacency}
                onChange={(e) => {
                  setOnlyAdjacency(e.target.checked)
                  setPage(1)
                }}
              />
              <span className="check-text">Only with adjacency support</span>
            </label>
          </div>

          <div className="sort-control">
            <label>Sort By</label>
            <select
              value={scoreSort}
              onChange={(e) => {
                setScoreSort(e.target.value)
                setPage(1)
              }}
            >
              <option value="default">Score (Default)</option>
              <option value="desc">High to Low</option>
              <option value="asc">Low to High</option>
            </select>
          </div>
        </div>
      </section>

      <section className="card modern-table-card candidates-table-card">
        <div className="table-scroll-wrap">
          <div className="table-head-grid">
            <span>Candidate</span>
            <span>Score</span>
            <span>Time to Productivity</span>
            <span>Signals</span>
          </div>

          {pagedItems.length === 0 && (
            <div className="empty-state">
              <p>No candidates match the current filters.</p>
            </div>
          )}

          {pagedItems.map((item) => {
            const scorePercent = Math.round((item.score || 0) * 100)
            const ttpText = item.time_to_productivity_pomodoros
              ? `${Math.max(1, Math.round((item.time_to_productivity_hours || 0) / 10))}-${Math.max(2, Math.round((item.time_to_productivity_hours || 0) / 8))} weeks`
              : 'Pending'

            return (
              <article className="table-row-grid" key={item.candidateId}>
                <div className="candidate-cell">
                  <div className="candidate-avatar">{item.candidateId.slice(0, 2).toUpperCase()}</div>
                  <div>
                    <p className="candidate-name">{item.candidateId}</p>
                    <p className="candidate-sub">{item.direct_matches?.[0] || 'Candidate profile'}</p>
                  </div>
                </div>

                <div className="score-cell-modern score-percent-cell">
                  <strong>{scorePercent}%</strong>
                  <div className="score-progress">
                    <div className="score-progress-fill" style={{ width: `${scorePercent}%` }} />
                  </div>
                </div>

                <div>
                  <span className="time-pill">{ttpText}</span>
                </div>

                <div className="signals-cell">
                  <div className="signals-list">
                    {(item.direct_matches || []).slice(0, 1).map((t) => (
                      <span className="tag-chip" key={`${item.candidateId}-d-${t}`}>{t}</span>
                    ))}
                    {(item.adjacent_support || []).slice(0, 1).map((t) => (
                      <span className="tag-chip alt" key={`${item.candidateId}-a-${t}`}>{t}</span>
                    ))}
                    {(item.direct_matches || []).length === 0 && (item.adjacent_support || []).length === 0 && (
                      <span className="badge-soft">Strategic hire</span>
                    )}
                  </div>
                </div>

              </article>
            )
          })}

          <div className="table-footer-modern">
            <span>
              Showing {filteredItems.length === 0 ? 0 : (safePage - 1) * pageSize + 1} of {filteredItems.length} entries
            </span>
            <div className="pagination">
              <button className="pg-btn" onClick={() => onPageChange(safePage - 1)} disabled={safePage === 1}>‹</button>
              {Array.from({ length: totalPages }).slice(0, 5).map((_, i) => {
                const p = i + 1
                return (
                  <button
                    key={`pg-${p}`}
                    className={`pg-btn ${p === safePage ? 'active' : ''}`}
                    onClick={() => onPageChange(p)}
                  >
                    {p}
                  </button>
                )
              })}
              <button className="pg-btn" onClick={() => onPageChange(safePage + 1)} disabled={safePage === totalPages}>›</button>
            </div>
          </div>
        </div>
      </section>

      <section className="candidate-radar-grid candidates-cta-grid">
        <button className="card candidate-radar-card cta-card" onClick={() => navigate('/analyze')}>
          <div>
            <h4>Analyze New Candidate</h4>
            <p className="subtle-copy">Run deep AI fit analysis for new talent</p>
          </div>
          <span>→</span>
        </button>

        <button
          className="card candidate-radar-card cta-card cta-dark"
          onClick={() => {
            setQuery('')
            setOnlyDirect(false)
            setOnlyAdjacency(false)
            setScoreSort('default')
            setMinScore(0)
            setPage(1)
          }}
        >
          <div>
            <h4>Full Candidate Pipeline</h4>
            <p className="subtle-copy">View the full board of active recruits</p>
          </div>
          <span>→</span>
        </button>
      </section>
    </div>
  )
}
