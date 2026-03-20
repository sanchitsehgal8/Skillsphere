import { useMemo, useState } from 'react'
import TopBar from '../components/TopBar'
import {
  buildCandidateFromGithub,
  createCandidate,
  createJob,
  fetchGithubProfile,
  getAudit,
  getCopilot,
  runMatch,
} from '../api/client'

export default function AnalyzePage({ onNewAnalyses }) {
  const [jobTitle, setJobTitle] = useState('Backend Engineer (Python/FastAPI)')
  const [jobDescription, setJobDescription] = useState(
    'Looking for Python, FastAPI, system design, and cloud experience. Strong ownership and communication required.',
  )
  const [githubInput, setGithubInput] = useState('torvalds, gaearon')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [results, setResults] = useState([])

  const usernames = useMemo(
    () => githubInput.split(',').map((u) => u.trim()).filter(Boolean),
    [githubInput],
  )

  async function runAnalysis() {
    setLoading(true)
    setError('')
    try {
      if (!jobTitle || !jobDescription || usernames.length === 0) {
        throw new Error('Please provide job info and at least one GitHub username.')
      }

      const jobId = `react-${Date.now()}`
      await createJob({ job_id: jobId, title: jobTitle, description: jobDescription })

      const prepared = []
      for (const username of usernames) {
        const repos = await fetchGithubProfile(username)
        const candidatePayload = buildCandidateFromGithub(username, repos)
        await createCandidate(candidatePayload)
        prepared.push({ username, ui: candidatePayload.ui })
      }

      const matchData = await runMatch(jobId, usernames)
      const audit = await getAudit(jobId)

      const enriched = []
      for (const ranked of matchData.ranked) {
        const copilot = await getCopilot(jobId, ranked.candidate_id)
        const aud = audit.entries.find((e) => e.candidate_id === ranked.candidate_id)
        const uiMeta = prepared.find((p) => p.username === ranked.candidate_id)?.ui

        enriched.push({
          jobId,
          candidateId: ranked.candidate_id,
          score: ranked.score,
          explanation: ranked.explanation,
          time_to_productivity_days: ranked.time_to_productivity_days,
          direct_matches: ranked.direct_matches,
          adjacent_support: ranked.adjacent_support,
          copilot: copilot.answer,
          bias_flags: aud?.bias_flags || [],
          ui: uiMeta,
        })
      }

      setResults(enriched)
      onNewAnalyses(enriched)
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || 'Failed to run analysis')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <TopBar title="Candidate Analysis" subtitle="Impact Area 02: Potential & Learning Trajectory" />

      <div className="analysis-grid">
        <section className="card form-card">
          <h3>Run New Analysis</h3>
          <label>Job Title</label>
          <input value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} />

          <label>Job Description</label>
          <textarea value={jobDescription} onChange={(e) => setJobDescription(e.target.value)} rows={6} />

          <label>GitHub Usernames (comma separated)</label>
          <input value={githubInput} onChange={(e) => setGithubInput(e.target.value)} />

          <button className="primary-btn" onClick={runAnalysis} disabled={loading}>
            {loading ? 'Analyzing...' : 'Analyze Candidates'}
          </button>
          {error && <p className="error">{error}</p>}
        </section>

        <section className="card">
          <h3>How scoring works</h3>
          <ul>
            <li>Current skill fit via role-vs-skill alignment.</li>
            <li>Learning velocity from GitHub evidence.</li>
            <li>Skill adjacency transferability (e.g. React → Vue, C++ → Rust).</li>
            <li>Time-to-productivity estimate with explicit reasoning.</li>
          </ul>
        </section>
      </div>

      <div className="result-grid">
        {results.map((r) => (
          <article className="card result-card" key={r.candidateId}>
            <div className="result-header">
              <h3>{r.candidateId}</h3>
              <span className="score">{Math.round(r.score * 100)}%</span>
            </div>
            <p><strong>Estimated TTP:</strong> {r.time_to_productivity_days?.toFixed(1)} days</p>
            <p><strong>Repos:</strong> {r.ui?.repos ?? '-'} | <strong>Stars:</strong> {r.ui?.stars ?? '-'}</p>
            <p><strong>Direct matches:</strong> {r.direct_matches?.join(', ') || 'None'}</p>
            <p><strong>Adjacency support:</strong> {r.adjacent_support?.join('; ') || 'None'}</p>
            <p><strong>Bias flags:</strong> {r.bias_flags.length ? r.bias_flags.join('; ') : 'None'}</p>
            <details>
              <summary>Why this match?</summary>
              <p>{r.explanation}</p>
              <p>{r.copilot}</p>
            </details>
          </article>
        ))}
      </div>
    </div>
  )
}
