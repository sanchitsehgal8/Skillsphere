import { useRef, useState } from 'react'
import TopBar from '../components/TopBar'
import SkillRadarChart from '../components/SkillRadarChart'
import {
  buildCandidateFromGithub,
  createCandidate,
  createJob,
  extractJdFromPdf,
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
  const [candidateBoxes, setCandidateBoxes] = useState([
    { github: 'sanchitsehgal8', codeforces: '' },
  ])
  const [loading, setLoading] = useState(false)
  const [jdUploading, setJdUploading] = useState(false)
  const [error, setError] = useState('')
  const [results, setResults] = useState([])
  const jdPdfInputRef = useRef(null)

  async function handleJdPdfUpload(e) {
    const file = e.target.files?.[0]
    if (!file) return

    setError('')
    setJdUploading(true)
    try {
      const parsed = await extractJdFromPdf(file)
      if (parsed?.extracted_text) {
        setJobDescription(parsed.extracted_text)
      }
      if (!jobTitle?.trim() && parsed?.suggested_title) {
        setJobTitle(parsed.suggested_title)
      }
    } catch (eUpload) {
      setError(eUpload?.response?.data?.detail || 'Failed to extract text from JD PDF')
    } finally {
      setJdUploading(false)
      e.target.value = ''
    }
  }

  function addCandidateBox() {
    setCandidateBoxes((prev) => [...prev, { github: '', codeforces: '' }])
  }

  function removeCandidateBox(index) {
    setCandidateBoxes((prev) => prev.filter((_, i) => i !== index))
  }

  function updateCandidateBox(index, key, value) {
    setCandidateBoxes((prev) =>
      prev.map((row, i) => (i === index ? { ...row, [key]: value } : row)),
    )
  }

  async function runAnalysis() {
    setLoading(true)
    setError('')
    try {
      const rows = candidateBoxes
        .map((row) => ({ github: row.github.trim(), codeforces: row.codeforces.trim() }))
        .filter((row) => row.github)

      const usernames = rows.map((r) => r.github)

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
        const mappedHandle = rows[i]?.codeforces || candidateId
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
    const source = results.length
      ? results
      : [
          {
            jobId: 'n/a',
            candidateId: 'n/a',
            score: 0,
            time_to_productivity_pomodoros: '',
            time_to_productivity_hours: '',
            time_to_productivity_sprints: '',
            direct_matches: ['Run analysis to generate results'],
            adjacent_support: [],
            bias_flags: [],
            codeforces: null,
            explanation: 'No analysis results available yet.',
          },
        ]

    const lines = source.map((r) => [
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

  function listOrFallback(items, fallback) {
    return items && items.length ? items : [fallback]
  }

  return (
    <div className="page analyze-page">
      <TopBar
        title="Analyze Candidate"
        subtitle="Run deep AI fit analysis for new talent against your open roles."
        onExport={exportCsv}
        theme={theme}
        onToggleTheme={onToggleTheme}
      />

      <div className="analysis-grid">
        <div className="analyze-main-col">
          <section className="card form-card analyze-block">
            <div className="card-section-head">
              <h3>Job Context</h3>
              <div className="jd-actions">
                <input
                  ref={jdPdfInputRef}
                  type="file"
                  accept="application/pdf,.pdf"
                  onChange={handleJdPdfUpload}
                  style={{ display: 'none' }}
                />
                <button
                  type="button"
                  className="ghost-btn"
                  onClick={() => jdPdfInputRef.current?.click()}
                  disabled={jdUploading}
                >
                  {jdUploading ? 'Uploading PDF...' : 'Add PDF to Auto-fill'}
                </button>
              </div>
            </div>

            <label className="field-label">Job Title</label>
            <input value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} />

            <label className="field-label">Job Description</label>
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              rows={7}
              placeholder="Paste the detailed job requirements and ideal candidate profile here..."
            />
          </section>

          <section className="card form-card analyze-block">
            <div className="card-section-head">
              <h3>Candidate Handles</h3>
            </div>

            <div className="candidate-boxes">
              {candidateBoxes.map((row, idx) => (
                <div className="candidate-box" key={`cand-box-${idx}`}>
                  <div className="candidate-inline-inputs">
                    <input
                      value={row.codeforces}
                      onChange={(e) => updateCandidateBox(idx, 'codeforces', e.target.value)}
                      placeholder="Codeforces Profile URL (optional)"
                    />
                    <input
                      value={row.github}
                      onChange={(e) => updateCandidateBox(idx, 'github', e.target.value)}
                      placeholder="GitHub Username (required)"
                    />
                  </div>
                  {candidateBoxes.length > 1 && (
                    <div className="candidate-box-head">
                      <button
                        type="button"
                        className="ghost-btn"
                        onClick={() => removeCandidateBox(idx)}
                      >
                        Remove Candidate
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <button type="button" className="ghost-btn dashed" onClick={addCandidateBox}>
              + Add Another Candidate
            </button>

            <button className="primary-btn analyze-run-btn" onClick={runAnalysis} disabled={loading}>
              {loading ? 'Analyzing...' : 'Analyze Candidate'}
            </button>
            {error && <p className="error">{error}</p>}
          </section>
        </div>

        <aside className="analyze-side-col">
          <section className="card rubric-card analyze-side-card">
            <div className="card-section-head">
              <h3>AI Scoring Rubric</h3>
            </div>

            <div className="rubric-grid">
              <div className="rubric-item">
                <div className="rubric-head">
                  <strong>Present Skill Fit</strong>
                  <span>40%</span>
                </div>
                <p>Direct correlation between current stack expertise and the job's core technical requirements.</p>
              </div>

              <div className="rubric-item">
                <div className="rubric-head">
                  <strong>Learning Velocity</strong>
                  <span>30%</span>
                </div>
                <p>Predicted speed of adapting to internal tools and new architectural patterns based on past trajectory.</p>
              </div>

              <div className="rubric-item">
                <div className="rubric-head">
                  <strong>Productivity Readiness</strong>
                  <span>30%</span>
                </div>
                <p>Assessment of soft skills, project management approach, and collaborative history.</p>
              </div>
            </div>

            <div className="rubric-bands decision-card">
              <div className="status-pill">System live</div>
              <h4>Decision Bands</h4>
              <p><strong>80 - 100:</strong> Strong Match</p>
              <p><strong>65 - 79:</strong> Promising</p>
              <p><strong>Below 65:</strong> Out of Scope</p>
            </div>
          </section>
        </aside>
      </div>

      <div className="result-grid">
        {results.map((r) => (
          <article className="card result-card" key={r.candidateId}>
            <div className="result-header">
              <div>
                <h3>{r.candidateId}</h3>
                <p className="subtle-copy">Evidence-based summary</p>
              </div>
              <span className="score">{Math.round(r.score * 100)}%</span>
            </div>

            <div className="result-section">
              <h4>Productivity Snapshot</h4>
              <div className="metric-grid">
                <div className="metric-item">
                  <span className="k">Estimated TTP</span>
                  <strong>
                    {r.time_to_productivity_pomodoros?.toFixed(1)} pomodoros
                    {' '}({r.time_to_productivity_hours?.toFixed(1)}h)
                  </strong>
                </div>
                <div className="metric-item">
                  <span className="k">Sprint Equivalent</span>
                  <strong>~{r.time_to_productivity_sprints?.toFixed(2)} sprints</strong>
                </div>
                <div className="metric-item">
                  <span className="k">GitHub Evidence</span>
                  <strong>{r.ui?.repos ?? '-'} repos | {r.ui?.stars ?? '-'} stars</strong>
                </div>
                <div className="metric-item">
                  <span className="k">Bias Check</span>
                  <strong>{r.bias_flags.length ? 'Flags present' : 'No flags'}</strong>
                </div>
              </div>
              {r.time_to_productivity_explanation && <p className="subtle-copy">{r.time_to_productivity_explanation}</p>}
            </div>

            <div className="result-section">
              <h4>Role Fit Breakdown</h4>
              <div className="tag-list">
                {listOrFallback(r.direct_matches, 'No direct matches').map((t) => (
                  <span className="tag-chip" key={`d-${t}`}>{t}</span>
                ))}
              </div>
              <p className="subtle-copy"><strong>Direct fit:</strong> Skills already demonstrated for this role.</p>
              <div className="tag-list">
                {listOrFallback(r.adjacent_support, 'No adjacent transfer paths found').map((t) => (
                  <span className="tag-chip alt" key={`a-${t}`}>{t}</span>
                ))}
              </div>
              <p className="subtle-copy"><strong>Adjacency potential:</strong> Skills that can transfer quickly to missing requirements.</p>
            </div>

            {r.codeforces && (
              <div className="result-section cf-block">
                <h4>Codeforces Benchmark ({r.codeforces.handle})</h4>
                <div className="metric-grid">
                  <div className="metric-item"><span className="k">Rating</span><strong>{r.codeforces.stats_overview.current_rating} (max {r.codeforces.stats_overview.max_rating})</strong></div>
                  <div className="metric-item"><span className="k">Rank</span><strong>{r.codeforces.stats_overview.rank_title}</strong></div>
                  <div className="metric-item"><span className="k">Solved / AC</span><strong>{r.codeforces.stats_overview.total_problems_solved} / {r.codeforces.stats_overview.acceptance_rate}%</strong></div>
                  <div className="metric-item"><span className="k">Trajectory</span><strong>{r.codeforces.contest_performance.rating_trajectory}</strong></div>
                </div>
                <p className="subtle-copy"><strong>Mentor verdict:</strong> {r.codeforces.honest_skill_verdict.mentor_summary}</p>
              </div>
            )}

            <div className="result-section cf-block">
              <h4>Candidate Skill Graph</h4>
              <SkillRadarChart candidate={r} />
              <p className="subtle-copy"><strong>Adjacency map:</strong> {r.adjacent_support?.join('; ') || 'No adjacent transfer paths found for this role.'}</p>
            </div>
            <details>
              <summary>Why this match? (Full explanation)</summary>
              <p className="subtle-copy">{r.explanation}</p>
              <p className="subtle-copy">{r.copilot}</p>
            </details>
          </article>
        ))}
      </div>
    </div>
  )
}
