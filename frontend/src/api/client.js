import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 20000,
})

export async function createJob(job) {
  const { data } = await api.post('/jobs', job)
  return data
}

export async function createCandidate(candidate) {
  const { data } = await api.post('/candidates', candidate)
  return data
}

export async function runMatch(job_id, candidate_ids) {
  const { data } = await api.post('/match', { job_id, candidate_ids })
  return data
}

export async function getAudit(jobId) {
  const { data } = await api.get(`/audit/${jobId}`)
  return data
}

export async function getCopilot(jobId, candidateId) {
  const { data } = await api.post('/copilot', { job_id: jobId, candidate_id: candidateId })
  return data
}

export async function getCodeforcesAnalysis(handle) {
  const { data } = await api.get(`/codeforces/${encodeURIComponent(handle)}/analysis`)
  return data
}

export async function fetchGithubProfile(username) {
  const { data } = await axios.get(`https://api.github.com/users/${username}/repos?per_page=100&sort=updated`, {
    headers: { Accept: 'application/vnd.github+json' },
    timeout: 20000,
  })
  return data
}

export function buildCandidateFromGithub(username, repos) {
  const langCounts = {}
  let totalStars = 0

  repos.forEach((repo) => {
    const lang = repo.language || 'Unknown'
    langCounts[lang] = (langCounts[lang] || 0) + 1
    totalStars += Number(repo.stargazers_count || 0)
  })

  return {
    candidate_id: username,
    name: username,
    headline: 'GitHub Candidate',
    summary: `Open-source footprint: ${repos.length} repos, ${totalStars} stars`,
    platforms: [
      {
        platform: 'github',
        url: `https://github.com/${username}`,
        metadata: {
          languages: Object.keys(langCounts).join(','),
          languages_json: JSON.stringify(langCounts),
          repo_count: String(repos.length),
          total_stars: String(totalStars),
          top_repo: repos[0]?.name || 'unknown',
        },
      },
    ],
    demographics: {},
    ui: {
      repos: repos.length,
      stars: totalStars,
      languages: langCounts,
    },
  }
}
