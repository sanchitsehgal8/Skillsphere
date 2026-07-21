import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Bot, MessageSquareText, ScanSearch, Sparkles, Target } from 'lucide-react'
import { PageHeading } from '../components/shell/PageHeading'
import CopilotPanel from '../components/CopilotPanel'
import { Card, CardContent, CardHeader, CardTitle, CardDescription, Select, Label, Badge, Skeleton } from '../components/ui'
import { listJobs } from '../api/client'

const CAPABILITIES = [
  { icon: ScanSearch, label: 'Surface strong candidates' },
  { icon: Target, label: 'Compare fit against a role' },
  { icon: Sparkles, label: 'Explain evidence & rankings' },
]

export default function CopilotPage() {
  const [jobs, setJobs] = useState([])
  const [jobId, setJobId] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let mounted = true
    async function load() {
      setLoading(true)
      setError('')
      try {
        const rows = await listJobs()
        if (mounted) setJobs(rows)
      } catch (e) {
        if (mounted) setError(e?.response?.data?.detail || e.message || 'Failed to load jobs')
      } finally {
        if (mounted) setLoading(false)
      }
    }
    load()
    return () => {
      mounted = false
    }
  }, [])

  return (
    <div>
      <PageHeading
        eyebrow="Copilot"
        title="AI Recruiter Copilot"
        subtitle="Ask natural-language questions about your candidate pool — every answer cites the evidence behind it."
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="lg:col-span-1 space-y-6"
        >
          <Card className="overflow-hidden">
            <div className="relative border-b border-border bg-[linear-gradient(135deg,hsl(var(--primary)/0.12),hsl(var(--accent)/0.1))] p-6">
              <div className="mb-3 grid h-11 w-11 place-items-center rounded-2xl bg-[linear-gradient(135deg,hsl(var(--primary)),hsl(var(--accent)))] text-primary-foreground shadow-glow">
                <Bot className="h-5 w-5" />
              </div>
              <h3 className="font-display text-lg font-semibold text-foreground">Your hiring copilot</h3>
              <p className="mt-1 text-sm text-muted-foreground">
                Grounded in every scorecard and analysis you have run. No guessing — just evidence.
              </p>
            </div>
            <CardContent className="pt-5">
              <ul className="space-y-3">
                {CAPABILITIES.map(({ icon: Icon, label }, i) => (
                  <motion.li
                    key={label}
                    initial={{ opacity: 0, x: -6 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.12 + i * 0.06 }}
                    className="flex items-center gap-3 text-sm text-foreground/90"
                  >
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-primary/12 text-primary">
                      <Icon className="h-4 w-4" />
                    </span>
                    {label}
                  </motion.li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Scope</CardTitle>
              <CardDescription>
                Narrow comparisons to candidates matched against a specific role.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-11 w-full" />
              ) : error ? (
                <p className="text-sm text-danger">{error}</p>
              ) : (
                <div>
                  <Label htmlFor="copilot-scope">Role</Label>
                  <Select id="copilot-scope" value={jobId} onChange={(e) => setJobId(e.target.value)}>
                    <option value="">All analyzed candidates</option>
                    {jobs.map((j) => (
                      <option key={j.id} value={j.id}>
                        {j.title}
                      </option>
                    ))}
                  </Select>
                  <div className="mt-3 flex items-center gap-2">
                    <Badge variant={jobId ? 'primary' : 'outline'} size="sm">
                      <Target className="h-3 w-3" />
                      {jobId ? jobs.find((j) => j.id === jobId)?.title || 'Role' : 'Whole pool'}
                    </Badge>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.08 }}
          className="lg:col-span-2"
        >
          <Card className="flex flex-col overflow-hidden">
            <div className="flex items-center gap-3 border-b border-border p-5">
              <span className="grid h-9 w-9 place-items-center rounded-xl bg-primary/12 text-primary">
                <MessageSquareText className="h-4 w-4" />
              </span>
              <div>
                <h3 className="font-display text-base font-semibold text-foreground">Conversation</h3>
                <p className="text-sm text-muted-foreground">Ask anything — answers stream with citations.</p>
              </div>
            </div>
            <div className="p-4 sm:p-5">
              <CopilotPanel
                jobId={jobId || undefined}
                emptyHint="Try: “Find strong backend engineers”, “Compare the top two candidates”, or “What skills are missing for this JD?”"
              />
            </div>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}
