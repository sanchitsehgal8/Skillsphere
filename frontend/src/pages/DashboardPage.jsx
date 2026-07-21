import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, Award, Download, Gauge, ShieldCheck, Sparkles, Users } from 'lucide-react'
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip as RTooltip, XAxis } from 'recharts'
import { PageHeading } from '../components/shell/PageHeading'
import { StatCard } from '../components/common/StatCard'
import { Pagination } from '../components/common/Pagination'
import { Card } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { Meter } from '../components/ui/meter'
import { Avatar, EmptyState, Skeleton } from '../components/ui/misc'
import { useToast } from '../components/ui/toast'
import { listAllAnalyses, listCandidates } from '../api/client'
import { downloadCsv, scoreTone, verdictMeta } from '../lib/utils'

export default function DashboardPage() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [candidates, setCandidates] = useState([])
  const [analyses, setAnalyses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showStrongOnly, setShowStrongOnly] = useState(false)
  const [page, setPage] = useState(1)

  useEffect(() => {
    let mounted = true
    async function load() {
      setLoading(true)
      setError('')
      try {
        const [candidateRows, analysisRows] = await Promise.all([listCandidates(), listAllAnalyses()])
        if (!mounted) return
        setCandidates(candidateRows)
        setAnalyses(analysisRows)
      } catch (e) {
        if (mounted) setError(e?.response?.data?.detail || e.message || 'Failed to load dashboard data')
      } finally {
        if (mounted) setLoading(false)
      }
    }
    load()
    return () => {
      mounted = false
    }
  }, [])

  const analysisByCandidate = useMemo(() => {
    const map = {}
    analyses.forEach((a) => {
      const prev = map[a.candidate_id]
      if (!prev || prev.fit_score < a.fit_score) map[a.candidate_id] = a
    })
    return map
  }, [analyses])

  const avgScore = candidates.length
    ? Math.round(candidates.reduce((acc, c) => acc + c.scorecard.overall_score, 0) / candidates.length)
    : 0
  const strongCount = candidates.filter((c) => c.scorecard.overall_score >= 75).length

  const rows = useMemo(
    () =>
      candidates.map((c) => {
        const latest = analysisByCandidate[c.evidence.candidate_id]
        return {
          candidateId: c.evidence.candidate_id,
          name: c.evidence.name,
          overall: c.scorecard.overall_score,
          fit: latest?.fit_score ?? null,
          verdict: latest?.verdict ?? null,
          topSkill: c.scorecard.skills[0]?.name || null,
        }
      }),
    [candidates, analysisByCandidate],
  )

  const distribution = useMemo(() => {
    const buckets = [
      { label: '0–39', min: 0, max: 39, tone: 'hsl(var(--danger))' },
      { label: '40–54', min: 40, max: 54, tone: 'hsl(var(--danger))' },
      { label: '55–74', min: 55, max: 74, tone: 'hsl(var(--warning))' },
      { label: '75–89', min: 75, max: 89, tone: 'hsl(var(--success))' },
      { label: '90+', min: 90, max: 100, tone: 'hsl(var(--success))' },
    ]
    return buckets.map((b) => ({
      ...b,
      count: rows.filter((r) => r.overall >= b.min && r.overall <= b.max).length,
    }))
  }, [rows])

  const visibleRows = useMemo(
    () => (showStrongOnly ? rows.filter((r) => r.overall >= 75) : rows),
    [rows, showStrongOnly],
  )

  const pageSize = 6
  const totalPages = Math.max(1, Math.ceil(visibleRows.length / pageSize))
  const safePage = Math.min(page, totalPages)
  const pagedRows = visibleRows.slice((safePage - 1) * pageSize, safePage * pageSize)

  function exportCsv() {
    if (!rows.length) return toast({ title: 'Nothing to export', description: 'Analyze a candidate first.', variant: 'info' })
    downloadCsv(
      `skillsphere-dashboard-${Date.now()}.csv`,
      ['candidateId', 'name', 'overallScore', 'latestFitScore', 'topSkill'],
      rows.map((r) => [r.candidateId, r.name, r.overall, r.fit ?? '', r.topSkill ?? '']),
    )
    toast({ title: 'Export ready', description: 'Dashboard CSV downloaded.', variant: 'success' })
  }

  return (
    <div>
      <PageHeading
        eyebrow="Overview"
        title="Talent intelligence"
        subtitle="Evidence-based candidate signals across your entire pipeline."
        actions={
          <Button variant="outline" onClick={exportCsv}>
            <Download className="h-4 w-4" /> Export
          </Button>
        }
      />

      {error && (
        <div className="mb-6 rounded-xl border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">{error}</div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Users} label="Candidates" value={candidates.length} hint="Profiles with a computed scorecard" tone="primary" delay={0} loading={loading} />
        <StatCard icon={Gauge} label="Avg score" value={avgScore} suffix="/100" hint="Confidence-weighted, 17 dimensions" tone="accent" delay={0.06} loading={loading} />
        <StatCard icon={Award} label="Strong (≥75)" value={strongCount} hint={`Of ${candidates.length} analyzed`} tone="success" delay={0.12} loading={loading} />
        <StatCard icon={ShieldCheck} label="Fairness" value="Audited" hint="Bias checks on every match" tone="warning" delay={0.18} loading={loading} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between gap-3 border-b border-border p-5">
            <div>
              <h3 className="font-display text-base font-semibold">Candidate pipeline</h3>
              <p className="text-sm text-muted-foreground">Overall engineering score and latest role-fit.</p>
            </div>
            <Button variant="subtle" size="sm" onClick={() => { setShowStrongOnly((s) => !s); setPage(1) }}>
              {showStrongOnly ? 'Show all' : 'Strong only'}
            </Button>
          </div>

          {loading ? (
            <div className="space-y-3 p-5">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : !rows.length ? (
            <EmptyState
              icon={Sparkles}
              title="No candidates analyzed yet"
              description="Run your first evidence-based analysis to populate the pipeline."
              action={<Button onClick={() => navigate('/analyze')}>Analyze a candidate <ArrowRight className="h-4 w-4" /></Button>}
            />
          ) : (
            <>
              <div className="divide-y divide-border">
                {pagedRows.map((r, i) => {
                  const vm = r.verdict ? verdictMeta(r.verdict) : null
                  return (
                    <motion.button
                      key={r.candidateId}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: i * 0.04 }}
                      onClick={() => navigate('/candidates')}
                      className="grid w-full grid-cols-[1fr_auto] items-center gap-4 p-4 text-left transition-colors hover:bg-secondary/40 sm:grid-cols-[1.4fr_1fr_auto]"
                    >
                      <div className="flex min-w-0 items-center gap-3">
                        <Avatar name={r.name} size="md" />
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium text-foreground">{r.name}</p>
                          <p className="truncate text-xs text-muted-foreground">
                            {r.topSkill || 'No verified skill yet'}
                          </p>
                        </div>
                      </div>
                      <div className="hidden items-center gap-3 sm:flex">
                        <div className="w-28">
                          <Meter value={r.overall} tone={scoreTone(r.overall)} />
                        </div>
                        <span className="font-mono text-sm font-semibold text-foreground">{r.overall.toFixed(0)}</span>
                      </div>
                      <div className="flex items-center gap-3 justify-self-end">
                        {vm ? <Badge tone={vm.tone} size="sm">{vm.label}</Badge> : <Badge variant="outline" size="sm">Not matched</Badge>}
                        <ArrowRight className="h-4 w-4 text-muted-foreground" />
                      </div>
                    </motion.button>
                  )
                })}
              </div>
              <Pagination page={safePage} totalPages={totalPages} onChange={(p) => setPage(Math.min(totalPages, Math.max(1, p)))} total={visibleRows.length} pageSize={pageSize} />
            </>
          )}
        </Card>

        <div className="space-y-6">
          <Card className="p-5">
            <h3 className="font-display text-base font-semibold">Score distribution</h3>
            <p className="mb-4 text-sm text-muted-foreground">Where your pipeline sits.</p>
            <div className="h-40">
              {loading ? (
                <Skeleton className="h-full w-full" />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={distribution} margin={{ top: 6, right: 0, left: 0, bottom: 0 }}>
                    <XAxis dataKey="label" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 10 }} axisLine={false} tickLine={false} />
                    <RTooltip
                      cursor={{ fill: 'hsl(var(--muted) / 0.4)' }}
                      contentStyle={{
                        background: 'hsl(var(--popover))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: 12,
                        fontSize: 12,
                        color: 'hsl(var(--foreground))',
                      }}
                    />
                    <Bar dataKey="count" radius={[6, 6, 0, 0]} maxBarSize={38}>
                      {distribution.map((d, i) => (
                        <Cell key={i} fill={d.tone} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </Card>

          <Card interactive className="group cursor-pointer p-5" onClick={() => navigate('/analyze')}>
            <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-primary/12 text-primary">
              <Sparkles className="h-5 w-5" />
            </div>
            <h3 className="font-display text-base font-semibold">Analyze new candidate</h3>
            <p className="mt-1 text-sm text-muted-foreground">Résumé + GitHub → instant evidence-based score.</p>
            <span className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-primary">
              Start <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </span>
          </Card>
        </div>
      </div>
    </div>
  )
}
