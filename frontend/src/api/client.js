import axios from 'axios'
import supabase from '../supabaseClient'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '')

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
})

// Attach the current Supabase access token to every request automatically so
// callers never have to thread `Authorization` headers through by hand.
api.interceptors.request.use(async (config) => {
  const {
    data: { session },
  } = await supabase.auth.getSession()
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  return config
})

// --- Jobs ------------------------------------------------------------- //
export async function createJob(job) {
  const { data } = await api.post('/jobs', job)
  return data
}

export async function listJobs() {
  const { data } = await api.get('/jobs')
  return data
}

export async function getJob(jobId) {
  const { data } = await api.get(`/jobs/${encodeURIComponent(jobId)}`)
  return data
}

export async function extractJdFromPdf(file) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/jobs/extract-jd-pdf', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  })
  return data
}

// --- Candidates --------------------------------------------------------- //
export async function extractResumeFromPdf(file) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/candidates/extract-resume-pdf', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  })
  return data
}

export async function createCandidate(payload) {
  // Server does GitHub mining + resume parsing + Codeforces analysis + scoring.
  const { data } = await api.post('/candidates', payload, { timeout: 90000 })
  return data
}

export async function listCandidates() {
  const { data } = await api.get('/candidates')
  return data
}

export async function getCandidate(candidateId) {
  const { data } = await api.get(`/candidates/${encodeURIComponent(candidateId)}`)
  return data
}

// --- Matching + fairness ------------------------------------------------ //
export async function runMatch(jobId, candidateIds) {
  const { data } = await api.post('/match', { job_id: jobId, candidate_ids: candidateIds }, { timeout: 60000 })
  return data
}

export async function getMatchResults(jobId) {
  const { data } = await api.get(`/match/${encodeURIComponent(jobId)}`)
  return data
}

export async function listAllAnalyses() {
  const { data } = await api.get('/analyses')
  return data
}

export async function getAudit(jobId) {
  const { data } = await api.get(`/audit/${encodeURIComponent(jobId)}`)
  return data
}

// --- Recruiter Copilot --------------------------------------------------- //
export async function askCopilot(query, { jobId, candidateIds } = {}) {
  const { data } = await api.post('/copilot', {
    query,
    job_id: jobId || null,
    candidate_ids: candidateIds || null,
  })
  return data
}

// --- Codeforces ----------------------------------------------------------- //
export async function getCodeforcesAnalysis(handle) {
  const { data } = await api.get(`/codeforces/${encodeURIComponent(handle)}/analysis`)
  return data
}
