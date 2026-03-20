import TopBar from '../components/TopBar'

export default function DashboardPage({ analyses }) {
  const avgScore = analyses.length
    ? Math.round((analyses.reduce((a, c) => a + c.score, 0) / analyses.length) * 100)
    : 0

  const strong = analyses.filter((a) => a.score >= 0.8).length

  return (
    <div className="page">
      <TopBar title="Dashboard" subtitle="SkillSphere Precision Analytics" />

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
                <td>{a.time_to_productivity_days ? `${a.time_to_productivity_days.toFixed(1)} days` : '-'}</td>
                <td className="reason-cell">{a.explanation}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
