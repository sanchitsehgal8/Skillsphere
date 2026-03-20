import TopBar from '../components/TopBar'

export default function CandidatesPage({ analysesByCandidate }) {
  const items = Object.values(analysesByCandidate)

  return (
    <div className="page">
      <TopBar title="All Candidates" subtitle="Ranked with direct + adjacency potential" />

      <div className="candidate-grid">
        {items.length === 0 && <div className="card">No candidates yet. Run an analysis first.</div>}

        {items.map((item) => (
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
