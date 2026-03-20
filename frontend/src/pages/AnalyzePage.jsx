import { useMemo, useState } from 'react'
import TopBar from '../components/TopBar'
import SkillRadarChart from '../components/SkillRadarChart'
import {
  buildCandidateFromGithub,
  createCandidate,
  createJob,
  fetchGithubProfile,
  getAudit,
  getCodeforcesAnalysis,
  getCopilot,
  runMatch,
} from '../api/client'

export default function AnalyzePage({ onNewAnalyses, theme, onToggleTheme }) {
  const [jobTitle, setJobTitle] = useState('Backend Engineer (Python/FastAPI)')
  const [jobDescription, setJobDescription] = useState(
    'Looking for Python, FastAPI, system design, and cloud experience. Strong ownership and communication required.',
  )
  const [githubInput, setGithubInput] = useState('torvalds, gaearon')
  const [codeforcesInput, setCodeforcesInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [results, setResults] = useState([])

  const usernames = useMemo(
    () => githubInput.split(',').map((u) => u.trim()).filter(Boolean),
    [githubInput],
  )
  const cfHandles = useMemo(
    () => codeforcesInput.split(',').map((u) => u.trim()).filter(Boolean),
    [codeforcesInput],
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
      const cfByCandidate = {}
      for (const username of usernames) {
        const repos = await fetchGithubProfile(username)
        const candidatePayload = buildCandidateFromGithub(username, repos)
        await createCandidate(candidatePayload)
        prepared.push({ username, ui: candidatePayload.ui })
      }

      for (let i = 0; i < usernames.length; i += 1) {
        const candidateId = usernames[i]
        const mappedHandle = cfHandles[i] || candidateId
        try {
          const cf = await getCodeforcesAnalysis(mappedHandle)
          cfByCandidate[candidateId] = cf
        } catch {
          cfByCandidate[candidateId] = null
        }
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
          time_to_productivity_pomodoros: ranked.time_to_productivity_pomodoros,
          time_to_productivity_hours: ranked.time_to_productivity_hours,
          time_to_productivity_sprints: ranked.time_to_productivity_sprints,
          time_to_productivity_explanation: ranked.time_to_productivity_explanation,
          direct_matches: ranked.direct_matches,
          adjacent_support: ranked.adjacent_support,
          copilot: copilot.answer,
          bias_flags: aud?.bias_flags || [],
          ui: uiMeta,
          codeforces: cfByCandidate[ranked.candidate_id] || null,
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

  function exportCsv() {
    if (!results.length) return
    const headers = [
      'jobId',
      'candidateId',
      'score',
      'time_to_productivity_pomodoros',
      'time_to_productivity_hours',
      'time_to_productivity_sprints',
      'direct_matches',
      'adjacent_support',
      'bias_flags',
      'cf_rating',
      'cf_max_rating',
      'cf_trajectory',
      'cf_consistency',
      'explanation',
    ]
    const lines = results.map((r) => [
      r.jobId,
      r.candidateId,
      r.score,
      r.time_to_productivity_pomodoros ?? '',
      r.time_to_productivity_hours ?? '',
      r.time_to_productivity_sprints ?? '',
      (r.direct_matches || []).join('|'),
      (r.adjacent_support || []).join('|'),
      (r.bias_flags || []).join('|'),
      r.codeforces?.stats_overview?.current_rating ?? '',
      r.codeforces?.stats_overview?.max_rating ?? '',
      r.codeforces?.contest_performance?.rating_trajectory ?? '',
      r.codeforces?.contest_performance?.consistency_score ?? '',
      (r.explanation || '').replaceAll('"', '""'),
    ])

    const csv = [
      headers.join(','),
      ...lines.map((row) => `${row[0]},${row[1]},${row[2]},${row[3]},${row[4]},${row[5]},${row[6]},${row[7]},${row[8]},${row[9]},${row[10]},${row[11]},${row[12]},"${row[13]}"`),
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `skillsphere-analysis-${Date.now()}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="page">
      <TopBar
        title="Candidate Analysis"
        subtitle="Impact Area 02: Potential & Learning Trajectory"
        onExport={exportCsv}
        theme={theme}
        onToggleTheme={onToggleTheme}
      />

      <div className="analysis-grid">
        <section className="card form-card">
          <h3>Run New Analysis</h3>
          <label>Job Title</label>
          <input value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} />

          <label>Job Description</label>
          <textarea value={jobDescription} onChange={(e) => setJobDescription(e.target.value)} rows={6} />

          <label>GitHub Usernames (comma separated)</label>
          <input value={githubInput} onChange={(e) => setGithubInput(e.target.value)} />

          <label>Codeforces Handles (optional, comma separated)</label>
          <input
            value={codeforcesInput}
            onChange={(e) => setCodeforcesInput(e.target.value)}
            placeholder="tourist, benq (blank = try same as GitHub usernames)"
          />

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
            <p>
              <strong>Estimated TTP:</strong>{' '}
              {r.time_to_productivity_pomodoros?.toFixed(1)} pomodoros
              {' '}({r.time_to_productivity_hours?.toFixed(1)}h, ~{r.time_to_productivity_sprints?.toFixed(2)} sprints)
            </p>
            {r.time_to_productivity_explanation && (
              <p><strong>What this means:</strong> {r.time_to_productivity_explanation}</p>
            )}
            <p><strong>Repos:</strong> {r.ui?.repos ?? '-'} | <strong>Stars:</strong> {r.ui?.stars ?? '-'}</p>
            <p><strong>Direct matches:</strong> {r.direct_matches?.join(', ') || 'None'}</p>
            <p><strong>Adjacency support:</strong> {r.adjacent_support?.join('; ') || 'None'}</p>
            <p><strong>Bias flags:</strong> {r.bias_flags.length ? r.bias_flags.join('; ') : 'None'}</p>
            {r.codeforces && (
              <div className="cf-block">
                <h4>Codeforces ({r.codeforces.handle})</h4>
                <p>
                  <strong>Rating:</strong> {r.codeforces.stats_overview.current_rating}
                  {' '}(max {r.codeforces.stats_overview.max_rating}) — {r.codeforces.stats_overview.rank_title}
                </p>
                <p>
                  <strong>Solved:</strong> {r.codeforces.stats_overview.total_problems_solved}
                  {' '}| <strong>Submissions:</strong> {r.codeforces.stats_overview.submission_count}
                  {' '}| <strong>AC:</strong> {r.codeforces.stats_overview.acceptance_rate}%
                </p>
                <p>
                  <strong>Comfort:</strong> {r.codeforces.problem_solving_profile.comfort_zone}
                  {' '}| <strong>Struggle:</strong> {r.codeforces.problem_solving_profile.struggle_zone}
                </p>
                <p>
                  <strong>Trajectory:</strong> {r.codeforces.contest_performance.rating_trajectory}
                  {' '}| <strong>Consistency:</strong> {r.codeforces.contest_performance.consistency_score}
                </p>
                <p><strong>Mentor verdict:</strong> {r.codeforces.honest_skill_verdict.mentor_summary}</p>
              </div>
            )}

            <div className="cf-block">
              <h4>Candidate Skill Graph</h4>
              <SkillRadarChart candidate={r} />
              <p><strong>Adjacency map:</strong> {r.adjacent_support?.join('; ') || 'No adjacent transfer paths found for this role.'}</p>
            </div>
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
