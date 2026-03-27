import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
})

export async function createJob(job, config = {}) {
  const { data } = await api.post('/jobs', job, config)
  return data
}

export async function extractJdFromPdf(file, config = {}) {
  const form = new FormData()
  form.append('file', file)

  const { data } = await api.post('/jobs/extract-jd-pdf', form, {
    ...config,
    headers: { 'Content-Type': 'multipart/form-data', ...(config.headers || {}) },
    timeout: 60000,
  })
  return data
}

export async function extractResumeFromPdf(file, config = {}) {
  const form = new FormData()
  form.append('file', file)

  const { data } = await api.post('/candidates/extract-resume-pdf', form, {
    ...config,
    headers: { 'Content-Type': 'multipart/form-data', ...(config.headers || {}) },
    timeout: 60000,
  })
  return data
}

export async function createCandidate(candidate, config = {}) {
  const { data } = await api.post('/candidates', candidate, config)
  return data
}

export async function runMatch(job_id, candidate_ids, config = {}) {
  const { data } = await api.post('/match', { job_id, candidate_ids }, config)
  return data
}

export async function getAudit(jobId, config = {}) {
  const { data } = await api.get(`/audit/${jobId}`, config)
  return data
}

export async function getCopilot(jobId, candidateId, config = {}) {
  const { data } = await api.post('/copilot', { job_id: jobId, candidate_id: candidateId }, config)
  return data
}

export async function getCodeforcesAnalysis(handle, config = {}) {
  const { data } = await api.get(`/codeforces/${encodeURIComponent(handle)}/analysis`, config)
  return data
}

export async function fetchGithubProfile(username) {
  const { data } = await axios.get(`https://api.github.com/users/${username}/repos?per_page=100&sort=updated`, {
    headers: { Accept: 'application/vnd.github+json' },
    timeout: 20000,
  })
  return data
}

export function buildCandidateFromGithub(username, repos, options = {}) {
  const { codeforcesHandle = '', resume = null } = options
  const langCounts = {}
  let totalStars = 0

  repos.forEach((repo) => {
    const lang = repo.language || 'Unknown'
    langCounts[lang] = (langCounts[lang] || 0) + 1
    totalStars += Number(repo.stargazers_count || 0)
  })

  const platforms = [
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
  ]

  if (codeforcesHandle) {
    platforms.push({
      platform: 'codeforces_profile',
      url: `https://codeforces.com/profile/${codeforcesHandle}`,
      metadata: { handle: codeforcesHandle },
    })
  }

  if (resume?.text) {
    platforms.push({
      platform: 'resume',
      metadata: {
        resume_text: resume.text,
        inferred_skills: (resume.skills || []).join(','),
        years_experience:
          resume.yearsExperience == null ? '' : String(resume.yearsExperience),
      },
    })
  }

  return {
    candidate_id: username,
    name: username,
    headline: 'GitHub Candidate',
    summary: `Open-source footprint: ${repos.length} repos, ${totalStars} stars`,
    platforms,
    demographics: {},
    ui: {
      repos: repos.length,
      stars: totalStars,
      languages: langCounts,
      resumeSkills: resume?.skills || [],
      yearsExperience: resume?.yearsExperience ?? null,
    },
  }
}
