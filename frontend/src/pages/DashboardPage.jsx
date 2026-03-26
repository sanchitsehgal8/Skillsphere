import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import TopBar from '../components/TopBar'

export default function DashboardPage({ analyses, theme, onToggleTheme }) {
  const navigate = useNavigate()
  const [showStrongOnly, setShowStrongOnly] = useState(false)
  const [page, setPage] = useState(1)

  function getScoreBand(score) {
    if (score >= 0.8) return 'Strong match'
    if (score >= 0.65) return 'Promising match'
    return 'Developing match'
  }

  function buildReasonOneLiner(a) {
    const band = getScoreBand(a.score)
    const direct = (a.direct_matches || []).slice(0, 2).join(', ')
    const hasAdj = !!(a.adjacent_support && a.adjacent_support.length)
    const ttp = a.time_to_productivity_hours ? `~${a.time_to_productivity_hours.toFixed(1)}h to productivity` : null

    const pieces = [band]
    if (direct) {
      pieces.push(`direct fit: ${direct}`)
    } else if (hasAdj) {
      pieces.push('adjacent skills can transfer quickly')
    } else {
      pieces.push('needs focused onboarding for role-specific gaps')
    }
    if (ttp) pieces.push(ttp)

    return pieces.join(' • ')
  }

  const avgScore = analyses.length
    ? Math.round((analyses.reduce((a, c) => a + c.score, 0) / analyses.length) * 100)
    : 0

  const strong = analyses.filter((a) => a.score >= 0.8).length

  const recent = analyses
  const fallback = [
    {
      candidateId: 'Elena Petrova',
      role: 'Senior Cloud Architect',
      score: 0.94,
      ttp: '2 – 3 weeks',
      reason: 'Strong alignment with AWS/K8s stack and leadership signal.',
      initials: 'EP',
      tone: 'orange',
    },
    {
      candidateId: 'Marcus Wright',
      role: 'Lead Product Designer',
      score: 0.81,
      ttp: '4 – 6 weeks',
      reason: 'Excellent portfolio, may require short ramp-up on backend systems.',
      initials: 'MW',
      tone: 'blue',
    },
    {
      candidateId: 'Sarah Lim',
      role: 'Backend Engineer',
      score: 0.72,
      ttp: '8+ weeks',
      reason: 'Solid logic skills, benefits from mentorship on distributed systems.',
      initials: 'SL',
      tone: 'gold',
    },
  ]

  const allRows = useMemo(() => {
    if (!recent.length) {
      return Array.from({ length: 15 }).map((_, i) => {
        const base = fallback[i % fallback.length]
        return {
          ...base,
          candidateId: `${base.candidateId} ${i + 1}`,
          score: Math.max(0.52, base.score - (i % 4) * 0.03),
        }
      })
    }

    return recent.map((a, i) => ({
      candidateId: a.candidateId,
      role: (a.direct_matches && a.direct_matches[0]) || 'Candidate profile',
      score: a.score,
      ttp: a.time_to_productivity_hours ? `~${a.time_to_productivity_hours.toFixed(1)}h` : 'Pending',
      reason: buildReasonOneLiner(a),
      initials: a.candidateId.slice(0, 2).toUpperCase(),
      tone: i % 3 === 0 ? 'orange' : i % 3 === 1 ? 'blue' : 'gold',
    }))
  }, [recent])

  const visibleRows = useMemo(
    () => (showStrongOnly ? allRows.filter((r) => r.score >= 0.8) : allRows),
    [allRows, showStrongOnly],
  )

  const pageSize = 3
  const totalPages = Math.max(1, Math.ceil(visibleRows.length / pageSize))
  const safePage = Math.min(page, totalPages)
  const rows = visibleRows.slice((safePage - 1) * pageSize, safePage * pageSize)

  function onPageChange(nextPage) {
    setPage(Math.min(totalPages, Math.max(1, nextPage)))
  }

  function toggleFilterInsights() {
    setShowStrongOnly((prev) => !prev)
    setPage(1)
  }

  function exportCsv() {
    const headers = ['jobId', 'candidateId', 'score', 'time_to_productivity_pomodoros', 'time_to_productivity_hours', 'time_to_productivity_sprints', 'explanation']
    const source = analyses.length
      ? analyses
      : [
          {
            jobId: 'n/a',
            candidateId: 'n/a',
            score: 0,
            time_to_productivity_pomodoros: '',
            time_to_productivity_hours: '',
            time_to_productivity_sprints: '',
            explanation: 'No analyses available yet.',
          },
        ]

    const lines = source.map((a) => [
      a.jobId,
      a.candidateId,
      a.score,
      a.time_to_productivity_pomodoros ?? '',
      a.time_to_productivity_hours ?? '',
      a.time_to_productivity_sprints ?? '',
      (a.explanation || '').replaceAll('"', '""'),
    ])

    const csv = [
      headers.join(','),
      ...lines.map((row) => `${row[0]},${row[1]},${row[2]},${row[3]},${row[4]},${row[5]},"${row[6]}"`),
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `skillsphere-dashboard-${Date.now()}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="page">
      <TopBar
        title="Dashboard"
        subtitle="Real-time candidate intelligence and match analytics powered by SkillSphere."
        onExport={exportCsv}
        theme={theme}
        onToggleTheme={onToggleTheme}
      />

      <div className="kpi-grid">
        <article className="card kpi-card tone-orange">
          <p className="kpi-label">Candidates Analyzed</p>
          <h3 className="kpi-value">{analyses.length || 1284} <span>{analyses.length ? '' : '↑ 12%'}</span></h3>
          <p className="kpi-sub">+138 profiles since last month</p>
          <div className="bar-track"><div className="bar-fill" style={{ width: '72%' }} /></div>
        </article>

        <article className="card kpi-card tone-blue">
          <p className="kpi-label">Avg Match Score</p>
          <h3 className="kpi-value">{avgScore || 84.2}<small>/100</small></h3>
          <p className="kpi-sub">Top 18% of all active pipelines</p>
          <div className="seg-row">
            <span className="seg on" /><span className="seg on" /><span className="seg on" />
            <span className="seg on" /><span className="seg on" /><span className="seg" /><span className="seg" />
          </div>
        </article>

        <article className="card kpi-card tone-gold">
          <p className="kpi-label">Strong Matches</p>
          <h3 className="kpi-value">{strong || 312} <span>≈ 75%</span></h3>
          <p className="kpi-sub">Candidates in active pool</p>
          <div className="stack-row">
            <span className="stack a">EP</span>
            <span className="stack b">MW</span>
            <span className="stack c">SL</span>
            <span className="stack more">+309</span>
            <span className="stack-label">in pipeline</span>
          </div>
        </article>
      </div>

      <div className="card table-card">
        <div className="section-header">
          <div>
            <h3>Recent Analyses</h3>
            <p className="subtle-copy">Detailed evaluation of the last 15 candidates matched to active roles.</p>
          </div>
          <button className="ghost-btn" onClick={toggleFilterInsights}>
            {showStrongOnly ? 'Show All' : 'Filter Insights'}
          </button>
        </div>

        <div className="table-head-grid dashboard-table-head">
          <span>Candidate</span>
          <span>Score</span>
          <span>Time to Productivity</span>
          <span>Reasoning</span>
          <span></span>
        </div>

        {rows.map((r) => (
          <div className="table-row-grid dashboard-table-row" key={r.candidateId}>
            <div className="candidate-cell">
              <div className="candidate-avatar">{r.initials}</div>
              <div>
                <p className="candidate-name">{r.candidateId}</p>
                <p className="candidate-sub">{r.role}</p>
              </div>
            </div>
            <div className={`score-cell-modern tone-${r.tone}`}>
              <strong>{Math.round(r.score * 100)}</strong>
              <div className="score-progress"><div className="score-progress-fill" style={{ width: `${Math.round(r.score * 100)}%` }} /></div>
            </div>
            <div><span className="time-pill">{r.ttp}</span></div>
            <div className="reason-cell">{r.reason}</div>
            <button className="details-link" onClick={() => navigate('/candidates')}>Details →</button>
          </div>
        ))}

        <div className="table-footer-modern">
          <span>
            SHOWING {visibleRows.length === 0 ? 0 : (safePage - 1) * pageSize + 1}–{Math.min(safePage * pageSize, visibleRows.length)} OF {visibleRows.length} ENTRIES
          </span>
          <div className="pagination">
            <button className="pg-btn" onClick={() => onPageChange(safePage - 1)} disabled={safePage === 1}>‹</button>
            {Array.from({ length: totalPages }).slice(0, 5).map((_, i) => {
              const p = i + 1
              return (
                <button
                  key={`dashboard-pg-${p}`}
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

      <div className="candidate-radar-grid">
        <button className="card candidate-radar-card cta-card" onClick={() => navigate('/analyze')}>
          <div>
            <h4>Analyze New Candidate</h4>
            <p className="subtle-copy">Upload a résumé for instant match score</p>
          </div>
          <span>→</span>
        </button>
        <button className="card candidate-radar-card cta-card" onClick={() => navigate('/candidates')}>
          <div>
            <h4>Full Candidate Pipeline</h4>
            <p className="subtle-copy">Browse and filter all active profiles</p>
          </div>
          <span>→</span>
        </button>
      </div>
    </div>
  )
}
