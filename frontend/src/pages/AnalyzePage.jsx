import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import {
  ClipboardCheck,
  FileText,
  Gauge,
  Plus,
  ShieldCheck,
  Sparkles,
  Target,
  Upload,
  Users,
  X,
} from 'lucide-react'
import AnalysisLoader from '../components/AnalysisLoader'
import { PageHeading } from '../components/shell/PageHeading'
import {
  Badge,
  Button,
  Card,
  Input,
  Label,
  Select,
  Separator,
  StatusDot,
  Textarea,
  useToast,
} from '../components/ui'
import {
  createCandidate,
  createJob,
  extractJdFromPdf,
  extractResumeFromPdf,
  getAudit,
  runMatch,
} from '../api/client'

function slugify(value, fallback) {
  const s = (value || '').trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
  return s || fallback
}

function emptyCandidateBox() {
  return {
    name: '',
    github: '',
    codeforces: '',
    gender: '',
    resumeFileName: '',
    resumePreview: null,
  }
}

const ANALYSIS_STEPS = [
  'Parsing job requirements',
  'Mining GitHub & résumé evidence',
  'Scoring fit against role requirements',
  'Running fairness audit',
]

const DIMENSIONS = [
  'Programming', 'Backend', 'Frontend', 'AI/ML', 'Cloud', 'DevOps', 'System Design',
  'Code Quality', 'Documentation', 'Testing', 'Open Source', 'Collaboration',
  'Ownership', 'Learning Velocity', 'Consistency', 'Project Complexity',
]

const VERDICT_BANDS = [
  { range: '75 – 100', label: 'Strong match', tone: 'success' },
  { range: '55 – 74', label: 'Promising', tone: 'warning' },
  { range: 'Below 55', label: 'Developing', tone: 'danger' },
]

export default function AnalyzePage() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [jobTitle, setJobTitle] = useState('Backend Engineer (Python/FastAPI)')
  const [jobDescription, setJobDescription] = useState(
    'Looking for Python, FastAPI, system design, and cloud experience. Strong ownership and communication required.',
  )
  const [candidateBoxes, setCandidateBoxes] = useState([emptyCandidateBox()])
  const [loading, setLoading] = useState(false)
  const [phase, setPhase] = useState(0)
  const [phaseDetail, setPhaseDetail] = useState('')
  const [jdUploading, setJdUploading] = useState(false)
  const [resumeUploadingIdx, setResumeUploadingIdx] = useState(null)
  const [error, setError] = useState('')
  const jdPdfInputRef = useRef(null)
  const resumeInputRefs = useRef({})

  async function handleJdPdfUpload(e) {
    const file = e.target.files?.[0]
    if (!file) return

    setError('')
    setJdUploading(true)
    try {
      const parsed = await extractJdFromPdf(file)
      if (parsed?.extracted_text) setJobDescription(parsed.extracted_text)
      if (!jobTitle?.trim() && parsed?.suggested_title) setJobTitle(parsed.suggested_title)
      toast({ title: 'Job description imported', description: 'Fields auto-filled from the PDF.', variant: 'success' })
    } catch (eUpload) {
      toast({
        title: 'JD upload failed',
        description: eUpload?.response?.data?.detail || 'Failed to extract text from JD PDF',
        variant: 'error',
      })
    } finally {
      setJdUploading(false)
      e.target.value = ''
    }
  }

  function addCandidateBox() {
    setCandidateBoxes((prev) => [...prev, emptyCandidateBox()])
  }

  function removeCandidateBox(index) {
    setCandidateBoxes((prev) => prev.filter((_, i) => i !== index))
  }

  function updateCandidateBox(index, key, value) {
    setCandidateBoxes((prev) => prev.map((row, i) => (i === index ? { ...row, [key]: value } : row)))
  }

  async function handleResumeUpload(index, e) {
    const file = e.target.files?.[0]
    if (!file) return

    setError('')
    setResumeUploadingIdx(index)
    try {
      const preview = await extractResumeFromPdf(file)
      setCandidateBoxes((prev) =>
        prev.map((row, i) => (i === index ? { ...row, resumePreview: preview, resumeFileName: file.name } : row)),
      )
      toast({ title: 'Résumé parsed', description: `${file.name} attached to candidate ${index + 1}.`, variant: 'success' })
    } catch (eUpload) {
      toast({
        title: 'Résumé upload failed',
        description: eUpload?.response?.data?.detail || 'Failed to extract resume data from PDF',
        variant: 'error',
      })
    } finally {
      setResumeUploadingIdx(null)
      e.target.value = ''
    }
  }

  async function runAnalysis() {
    const rows = candidateBoxes.filter((row) => row.github.trim() || row.name.trim())
    if (!jobTitle.trim() || !jobDescription.trim() || rows.length === 0) {
      setError('Please provide job info and at least one candidate (GitHub username or name).')
      return
    }

    setLoading(true)
    setError('')
    setPhase(0)
    setPhaseDetail('')
    try {
      const newJobId = `job-${Date.now()}`
      await createJob({ job_id: newJobId, title: jobTitle, description: jobDescription })

      setPhase(1)
      const created = {}
      const usedIds = new Set()
      for (let i = 0; i < rows.length; i += 1) {
        const row = rows[i]
        const base = slugify(row.github || row.name, `candidate-${i + 1}`)
        let candidateId = base
        let n = 2
        while (usedIds.has(candidateId)) {
          candidateId = `${base}-${n}`
          n += 1
        }
        usedIds.add(candidateId)

        setPhaseDetail(`Candidate ${i + 1} of ${rows.length} — GitHub, résumé, Codeforces`)
        const payload = {
          candidate_id: candidateId,
          name: row.name.trim() || row.github.trim(),
          github_username: row.github.trim() || undefined,
          codeforces_handle: row.codeforces.trim() || undefined,
          resume_text: row.resumePreview?.raw_text || '',
          demographics: row.gender ? { gender: row.gender } : {},
        }
        const candidate = await createCandidate(payload)
        created[candidateId] = candidate
      }

      setPhase(2)
      setPhaseDetail('')
      const matchResults = await runMatch(newJobId, Object.keys(created))

      setPhase(3)
      const audit = await getAudit(newJobId)

      navigate('/analyze/results', {
        state: { jobId: newJobId, jobTitle, results: matchResults, candidatesById: created, auditReport: audit },
      })
    } catch (e) {
      toast({
        title: 'Analysis failed',
        description: e?.response?.data?.detail || e.message || 'Failed to run analysis',
        variant: 'error',
      })
      setLoading(false)
    }
  }

  return (
    <div>
      <PageHeading
        eyebrow="Analyze"
        title="Run a candidate analysis"
        subtitle="Evidence-based fit scoring against your open role — GitHub, résumé, and competitive-programming signals in one pass."
      />

      <AnimatePresence mode="wait">
        {loading ? (
          <AnalysisLoader key="loader" steps={ANALYSIS_STEPS} activeIndex={phase} detail={phaseDetail} />
        ) : (
          <motion.div
            key="form"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]"
          >
            <div className="space-y-6">
              <Card>
                <div className="flex items-center justify-between gap-3 border-b border-border p-5 sm:p-6">
                  <div className="flex items-center gap-2.5">
                    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-primary/12 text-primary">
                      <FileText className="h-4.5 w-4.5" />
                    </span>
                    <div>
                      <h3 className="font-display text-base font-semibold">Job context</h3>
                      <p className="text-sm text-muted-foreground">Define the role you are matching against.</p>
                    </div>
                  </div>
                  <input
                    ref={jdPdfInputRef}
                    type="file"
                    accept="application/pdf,.pdf"
                    onChange={handleJdPdfUpload}
                    className="hidden"
                  />
                  <Button variant="subtle" size="sm" onClick={() => jdPdfInputRef.current?.click()} loading={jdUploading}>
                    {!jdUploading && <Upload className="h-4 w-4" />}
                    {jdUploading ? 'Uploading…' : 'PDF auto-fill'}
                  </Button>
                </div>

                <div className="space-y-5 p-5 sm:p-6">
                  <div>
                    <Label htmlFor="job-title">Job title</Label>
                    <Input id="job-title" value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} />
                  </div>
                  <div>
                    <Label htmlFor="job-desc">Job description</Label>
                    <Textarea
                      id="job-desc"
                      value={jobDescription}
                      onChange={(e) => setJobDescription(e.target.value)}
                      rows={7}
                      placeholder="Paste the detailed job requirements and ideal candidate profile here..."
                    />
                  </div>
                </div>
              </Card>

              <Card>
                <div className="flex items-center justify-between gap-3 border-b border-border p-5 sm:p-6">
                  <div className="flex items-center gap-2.5">
                    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-accent/12 text-accent">
                      <Users className="h-4.5 w-4.5" />
                    </span>
                    <div>
                      <h3 className="font-display text-base font-semibold">Candidates</h3>
                      <p className="text-sm text-muted-foreground">Add one or more people to score against this role.</p>
                    </div>
                  </div>
                  <Badge variant="outline" size="sm">
                    {candidateBoxes.length} {candidateBoxes.length === 1 ? 'candidate' : 'candidates'}
                  </Badge>
                </div>

                <div className="space-y-4 p-5 sm:p-6">
                  <AnimatePresence initial={false}>
                    {candidateBoxes.map((row, idx) => (
                      <motion.div
                        key={`cand-box-${idx}`}
                        layout
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.98 }}
                        transition={{ duration: 0.25 }}
                        className="rounded-xl border border-border bg-surface/40 p-4 sm:p-5"
                      >
                        <div className="mb-4 flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="grid h-6 w-6 place-items-center rounded-full bg-secondary text-2xs font-semibold text-muted-foreground">
                              {idx + 1}
                            </span>
                            <span className="font-display text-sm font-semibold text-foreground">Candidate {idx + 1}</span>
                          </div>
                          {candidateBoxes.length > 1 && (
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              onClick={() => removeCandidateBox(idx)}
                              aria-label={`Remove candidate ${idx + 1}`}
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          )}
                        </div>

                        <div className="grid gap-4 sm:grid-cols-2">
                          <div>
                            <Label>Candidate name</Label>
                            <Input
                              value={row.name}
                              onChange={(e) => updateCandidateBox(idx, 'name', e.target.value)}
                              placeholder="Required if no GitHub username"
                            />
                          </div>
                          <div>
                            <Label>GitHub username</Label>
                            <Input
                              value={row.github}
                              onChange={(e) => updateCandidateBox(idx, 'github', e.target.value)}
                              placeholder="Optional, but strongly recommended"
                            />
                          </div>
                          <div>
                            <Label>Codeforces handle or URL</Label>
                            <Input
                              value={row.codeforces}
                              onChange={(e) => updateCandidateBox(idx, 'codeforces', e.target.value)}
                              placeholder="Optional"
                            />
                          </div>
                          <div>
                            <Label>Gender (optional — enables fairness audit)</Label>
                            <Select value={row.gender} onChange={(e) => updateCandidateBox(idx, 'gender', e.target.value)}>
                              <option value="">Prefer not to say</option>
                              <option value="male">Male</option>
                              <option value="female">Female</option>
                              <option value="non-binary">Non-binary</option>
                            </Select>
                          </div>
                        </div>

                        <Separator className="my-4" />

                        <input
                          ref={(el) => {
                            resumeInputRefs.current[idx] = el
                          }}
                          type="file"
                          accept="application/pdf,.pdf"
                          onChange={(e) => handleResumeUpload(idx, e)}
                          className="hidden"
                        />
                        <div className="flex flex-wrap items-center gap-3">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => resumeInputRefs.current[idx]?.click()}
                            loading={resumeUploadingIdx === idx}
                          >
                            {resumeUploadingIdx !== idx && <FileText className="h-4 w-4" />}
                            {resumeUploadingIdx === idx ? 'Uploading résumé…' : 'Add résumé PDF'}
                          </Button>
                          {row.resumeFileName && (
                            <div className="flex min-w-0 items-center gap-2 text-xs text-muted-foreground">
                              <ClipboardCheck className="h-3.5 w-3.5 shrink-0 text-success" />
                              <span className="truncate">
                                {row.resumeFileName}
                                {row.resumePreview?.skills?.length
                                  ? ` · ${row.resumePreview.skills.slice(0, 4).join(', ')}`
                                  : ''}
                                {row.resumePreview?.total_experience_years != null
                                  ? ` · ${row.resumePreview.total_experience_years} yrs`
                                  : ''}
                              </span>
                            </div>
                          )}
                        </div>
                      </motion.div>
                    ))}
                  </AnimatePresence>

                  <button
                    type="button"
                    onClick={addCandidateBox}
                    className="flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-border py-3 text-sm font-medium text-muted-foreground transition-colors hover:border-primary/50 hover:bg-secondary/30 hover:text-foreground"
                  >
                    <Plus className="h-4 w-4" /> Add another candidate
                  </button>
                </div>

                <div className="space-y-3 border-t border-border p-5 sm:p-6">
                  <Button variant="gradient" size="lg" className="w-full" onClick={runAnalysis}>
                    <Sparkles className="h-4.5 w-4.5" /> Analyze candidates
                  </Button>
                  {error && <p className="text-sm text-danger">{error}</p>}
                </div>
              </Card>
            </div>

            <aside className="lg:sticky lg:top-6 lg:h-fit">
              <Card className="p-5 sm:p-6">
                <div className="mb-4 flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-primary/12 text-primary">
                      <Gauge className="h-4.5 w-4.5" />
                    </span>
                    <h3 className="font-display text-base font-semibold">Engineering scorecard</h3>
                  </div>
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface/60 px-2.5 py-1 text-2xs font-medium text-muted-foreground">
                    <StatusDot tone="success" /> System live
                  </span>
                </div>

                <p className="text-sm leading-relaxed text-muted-foreground">
                  Every candidate is scored across <span className="font-medium text-foreground">17 explainable dimensions</span>,
                  each derived from observable GitHub and résumé evidence with its own confidence and reasoning. No arbitrary
                  weights — dimensions with little evidence contribute less automatically.
                </p>

                <div className="mt-4 flex flex-wrap gap-1.5">
                  {DIMENSIONS.map((d) => (
                    <span
                      key={d}
                      className="rounded-md border border-border bg-secondary/40 px-2 py-0.5 text-2xs text-muted-foreground"
                    >
                      {d}
                    </span>
                  ))}
                </div>

                <Separator className="my-5" />

                <div className="mb-3 flex items-center gap-2">
                  <Target className="h-4 w-4 text-muted-foreground" />
                  <h4 className="font-display text-sm font-semibold text-foreground">Fit verdict bands</h4>
                </div>
                <div className="space-y-2">
                  {VERDICT_BANDS.map((b) => (
                    <div
                      key={b.label}
                      className="flex items-center justify-between rounded-lg border border-border bg-surface/40 px-3 py-2"
                    >
                      <span className="font-mono text-xs text-muted-foreground">{b.range}</span>
                      <Badge tone={b.tone} size="sm">{b.label}</Badge>
                    </div>
                  ))}
                </div>

                <div className="mt-5 flex items-start gap-2.5 rounded-xl border border-border bg-secondary/30 p-3.5">
                  <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                  <p className="text-xs leading-relaxed text-muted-foreground">
                    Every match runs through an automated bias audit. Provide gender to enable per-candidate fairness flags.
                  </p>
                </div>
              </Card>
            </aside>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
