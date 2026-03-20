import TopBar from '../components/TopBar'

export default function DashboardPage({ analyses, theme, onToggleTheme }) {
  const avgScore = analyses.length
    ? Math.round((analyses.reduce((a, c) => a + c.score, 0) / analyses.length) * 100)
    : 0

  const strong = analyses.filter((a) => a.score >= 0.8).length

  function exportCsv() {
    if (!analyses.length) return
    const headers = ['jobId', 'candidateId', 'score', 'time_to_productivity_pomodoros', 'time_to_productivity_hours', 'time_to_productivity_sprints', 'explanation']
    const lines = analyses.map((a) => [
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
        subtitle="SkillSphere Precision Analytics"
        onExport={exportCsv}
        theme={theme}
        onToggleTheme={onToggleTheme}
      />

      <div className="kpi-grid">
        <div className="card"><p>Candidates Analyzed</p><h3>{analyses.length}</h3></div>
        <div className="card"><p>Avg Match Score</p><h3>{avgScore}%</h3></div>
        <div className="card"><p>Strong Matches</p><h3>{strong}</h3></div>
      </div>

      <div className="card table-card">
        <h3>Recent Analyses</h3>
        <table>
          <thead>
            <tr>
              <th>Candidate</th>
              <th>Score</th>
              <th>Time to Productivity</th>
              <th>Reasoning</th>
            </tr>
          </thead>
          <tbody>
            {analyses.length === 0 && (
              <tr>
                <td colSpan={4}>No analyses yet. Go to Analyze Candidate.</td>
              </tr>
            )}
            {analyses.map((a) => (
              <tr key={`${a.jobId}-${a.candidateId}`}>
                <td>{a.candidateId}</td>
                <td>{Math.round(a.score * 100)}%</td>
                <td>
                  {a.time_to_productivity_pomodoros
                    ? `${a.time_to_productivity_pomodoros.toFixed(1)} pomodoros (~${(a.time_to_productivity_hours || 0).toFixed(1)}h)`
                    : '-'}
                </td>
                <td className="reason-cell">{a.explanation}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
