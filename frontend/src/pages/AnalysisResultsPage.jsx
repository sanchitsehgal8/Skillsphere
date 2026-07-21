import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowLeft,
  Award,
  Blocks,
  Bot,
  ClipboardCheck,
  Clock,
  Download,
  Gauge,
  ListChecks,
  Radar,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Trophy,
  Users,
  Zap,
} from 'lucide-react'
import SkillRadarChart from '../components/SkillRadarChart'
import AdjacencyPathGraph from '../components/AdjacencyPathGraph'
import ScorecardBreakdown from '../components/ScorecardBreakdown'
import SkillEvidenceList from '../components/SkillEvidenceList'
import CultureFitPanel from '../components/CultureFitPanel'
import CopilotPanel from '../components/CopilotPanel'
import { PageHeading } from '../components/shell/PageHeading'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
  Badge,
  Button,
  Card,
  Ring,
} from '../components/ui'
import { cn, downloadCsv, scoreTone, verdictMeta } from '../lib/utils'

function coverageLabel(status) {
  if (status === 'direct') return 'Direct'
  if (status === 'adjacent') return 'Adjacent'
  return 'Missing'
}

const COVERAGE_TONE = { direct: 'success', adjacent: 'warning', missing: 'danger' }

function SectionTitle({ icon: Icon, children, hint }) {
  return (
    <div className="mb-4 flex items-center gap-2.5">
      {Icon && (
        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
          <Icon className="h-4 w-4" />
        </span>
      )}
      <div>
        <h4 className="font-display text-sm font-semibold text-foreground">{children}</h4>
        {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
      </div>
    </div>
  )
}

function MetricTile({ icon: Icon, label, value, tone = 'primary' }) {
  const toneRing = {
    primary: 'text-primary bg-primary/10',
    success: 'text-success bg-success/10',
    warning: 'text-warning bg-warning/12',
    danger: 'text-danger bg-danger/10',
    accent: 'text-accent bg-accent/10',
  }[tone]
  return (
    <div className="rounded-xl border border-border bg-surface/50 p-4">
      <div className="mb-2 flex items-center gap-2">
        <span className={cn('grid h-7 w-7 place-items-center rounded-lg', toneRing)}>
          <Icon className="h-3.5 w-3.5" />
        </span>
        <span className="text-xs font-medium text-muted-foreground">{label}</span>
      </div>
      <p className="font-display text-base font-semibold text-foreground">{value}</p>
    </div>
  )
}

export default function AnalysisResultsPage() {
  const navigate = useNavigate()
  const { state } = useLocation()

  // This route only makes sense as the destination of the Analyze flow — a
  // direct visit or refresh has no data to show, so send the user back
  // rather than rendering an empty shell.
  if (!state?.results?.length) {
    return <Navigate to="/analyze" replace />
  }

  const { jobId, jobTitle, results, candidatesById, auditReport } = state

  function exportCsv() {
    const headers = [
      'candidateId', 'fitScore', 'verdict', 'overallScore', 'ttpHoursLow', 'ttpHoursHigh', 'sprints',
      'matched', 'adjacent', 'missing', 'reasoning',
    ]
    const rows = results.map((r) => {
      const ttp = r.scorecard?.time_to_productivity
      return [
        r.candidate_id, r.fit_score, r.verdict, r.scorecard?.overall_score,
        ttp?.hours_low ?? '', ttp?.hours_high ?? '', ttp?.sprints ?? '',
        (r.matched_requirements || []).join('|'), (r.adjacent_requirements || []).join('|'),
        (r.missing_requirements || []).join('|'), r.reasoning || '',
      ]
    })
    downloadCsv(`skillsphere-analysis-${Date.now()}.csv`, headers, rows)
  }

  return (
    <div>
      <PageHeading
        eyebrow="Analysis results"
        title={jobTitle || 'Candidate analysis'}
        subtitle={`${results.length} candidate${results.length === 1 ? '' : 's'} scored against this role — every number below cites its evidence.`}
        actions={
          <>
            <Button variant="ghost" onClick={() => navigate('/analyze')}>
              <ArrowLeft className="h-4 w-4" /> New analysis
            </Button>
            <Button variant="outline" onClick={exportCsv}>
              <Download className="h-4 w-4" /> Export
            </Button>
          </>
        }
      />

      <div className="space-y-6">
        {results.map((r, idx) => {
          const candidate = candidatesById?.[r.candidate_id]
          const ev = candidate?.evidence
          const sc = r.scorecard
          const ttp = sc.time_to_productivity
          const flags = (auditReport?.flags || []).filter((f) => f.candidate_id === r.candidate_id)
          const vm = verdictMeta(r.verdict)

          return (
            <motion.article
              key={r.candidate_id}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: idx * 0.08 }}
            >
              <Card>
                <div className="flex flex-col gap-5 border-b border-border p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
                  <div className="flex items-center gap-4">
                    <Ring value={r.fit_score} tone={vm.tone} size={72} stroke={6} />
                    <div>
                      <h3 className="font-display text-lg font-semibold text-foreground">{ev?.name || r.candidate_id}</h3>
                      <p className="text-sm text-muted-foreground">Evidence-based summary</p>
                      <div className="mt-2 flex items-center gap-2">
                        <Badge tone={vm.tone} size="sm">{vm.label}</Badge>
                        <span className="font-mono text-sm font-semibold text-foreground">{Math.round(r.fit_score)}% fit</span>
                      </div>
                    </div>
                  </div>
                  {ev?.codeforces && (
                    <Badge variant="primary" size="sm">
                      <Trophy className="h-3 w-3" /> CF {ev.codeforces.stats_overview.current_rating}
                    </Badge>
                  )}
                </div>

                <div className="space-y-8 p-5 sm:p-6">
                  <section>
                    <SectionTitle icon={Zap}>Productivity snapshot</SectionTitle>
                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                      <MetricTile
                        icon={Clock}
                        label="Estimated ramp-up"
                        value={`${ttp?.hours_low?.toFixed(0)}-${ttp?.hours_high?.toFixed(0)}h (${ttp?.days_low?.toFixed(1)}-${ttp?.days_high?.toFixed(1)}d)`}
                      />
                      <MetricTile icon={Gauge} label="Sprint equivalent" value={`~${ttp?.sprints?.toFixed(2)} sprints`} tone="accent" />
                      <MetricTile
                        icon={Award}
                        label="Engineering score"
                        value={`${sc.overall_score.toFixed(0)}/100 · ${Math.round(sc.overall_confidence * 100)}%`}
                        tone={scoreTone(sc.overall_score)}
                      />
                      <MetricTile
                        icon={flags.length ? ShieldAlert : ShieldCheck}
                        label="Fairness check"
                        value={flags.length ? `${flags.length} flag(s)` : 'No flags'}
                        tone={flags.length ? 'warning' : 'success'}
                      />
                    </div>
                    {ttp?.reasoning && <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{ttp.reasoning}</p>}
                  </section>

                  <section>
                    <SectionTitle icon={ListChecks} hint="How the candidate covers each role requirement">
                      Role fit breakdown
                    </SectionTitle>
                    <div className="space-y-2">
                      {r.coverage.map((c) => (
                        <div
                          key={c.requirement}
                          className="flex flex-col gap-1.5 rounded-lg border border-border bg-surface/40 p-3 sm:flex-row sm:items-center sm:gap-3"
                        >
                          <Badge tone={COVERAGE_TONE[c.status]} size="sm" className="w-fit">
                            {coverageLabel(c.status)}
                          </Badge>
                          <span className="text-sm font-medium text-foreground sm:w-48 sm:shrink-0">{c.requirement}</span>
                          <span className="text-xs text-muted-foreground">{c.detail}</span>
                        </div>
                      ))}
                    </div>
                    <div className="mt-5">
                      <SectionTitle icon={Blocks}>Adjacency graph</SectionTitle>
                      <AdjacencyPathGraph coverage={r.coverage} />
                    </div>
                  </section>

                  <section>
                    <SectionTitle icon={ListChecks}>Full engineering scorecard</SectionTitle>
                    <ScorecardBreakdown dimensions={sc.dimensions} />
                  </section>

                  <section>
                    <SectionTitle icon={Radar}>Scorecard at a glance</SectionTitle>
                    <SkillRadarChart dimensions={sc.dimensions} />
                  </section>

                  <section>
                    <SectionTitle icon={ClipboardCheck}>Evidence-based skill verification</SectionTitle>
                    <SkillEvidenceList skills={sc.skills} />
                  </section>

                  <section>
                    <SectionTitle icon={Users} hint="Observable signals only">Culture fit</SectionTitle>
                    <CultureFitPanel signals={sc.culture} />
                  </section>

                  {ev?.codeforces && (
                    <section>
                      <SectionTitle icon={Trophy}>Codeforces benchmark · {ev.codeforces.handle}</SectionTitle>
                      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                        <MetricTile
                          icon={Gauge}
                          label="Rating"
                          value={`${ev.codeforces.stats_overview.current_rating} (max ${ev.codeforces.stats_overview.max_rating})`}
                        />
                        <MetricTile icon={Award} label="Rank" value={ev.codeforces.stats_overview.rank_title} tone="accent" />
                        <MetricTile
                          icon={ClipboardCheck}
                          label="Solved / AC"
                          value={`${ev.codeforces.stats_overview.total_problems_solved} / ${ev.codeforces.stats_overview.acceptance_rate}%`}
                        />
                        <MetricTile icon={Zap} label="Trajectory" value={ev.codeforces.contest_performance.rating_trajectory} />
                      </div>
                      <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                        <span className="font-medium text-foreground">Mentor verdict:</span>{' '}
                        {ev.codeforces.honest_skill_verdict.mentor_summary}
                      </p>
                    </section>
                  )}

                  {!!flags.length && (
                    <section>
                      <SectionTitle icon={ShieldAlert}>Fairness flags</SectionTitle>
                      <ul className="space-y-2">
                        {flags.map((f, i) => (
                          <li
                            key={`${r.candidate_id}-flag-${i}`}
                            className="flex items-start gap-2.5 rounded-lg border border-warning/25 bg-warning/8 p-3 text-sm text-foreground/90"
                          >
                            <Badge tone="warning" size="sm" className="shrink-0 uppercase">{f.severity}</Badge>
                            <span>{f.reason}</span>
                          </li>
                        ))}
                      </ul>
                    </section>
                  )}

                  <section>
                    <SectionTitle icon={Sparkles}>Summary</SectionTitle>
                    <p className="text-sm leading-relaxed text-muted-foreground">{sc.summary}</p>

                    <div className="mt-4 grid gap-4 lg:grid-cols-3">
                      {!!sc.strengths.length && (
                        <div className="rounded-xl border border-success/25 bg-success/8 p-4">
                          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-success">Strengths</p>
                          <ul className="space-y-1.5 text-sm text-foreground/90">
                            {sc.strengths.map((s, i) => (
                              <li key={`${r.candidate_id}-st-${i}`} className="flex gap-2">
                                <span className="text-success">+</span>{s}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {!!sc.gaps.length && (
                        <div className="rounded-xl border border-danger/25 bg-danger/8 p-4">
                          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-danger">Gaps</p>
                          <ul className="space-y-1.5 text-sm text-foreground/90">
                            {sc.gaps.map((g, i) => (
                              <li key={`${r.candidate_id}-gp-${i}`} className="flex gap-2">
                                <span className="text-danger">–</span>{g}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {!!sc.recommendations.length && (
                        <div className="rounded-xl border border-primary/25 bg-primary/8 p-4">
                          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-primary">Recommendations</p>
                          <ul className="space-y-1.5 text-sm text-foreground/90">
                            {sc.recommendations.map((rec, i) => (
                              <li key={`${r.candidate_id}-rc-${i}`} className="flex gap-2">
                                <span className="text-primary">→</span>{rec}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </section>

                  <Accordion type="single" collapsible className="border-t border-border">
                    <AccordionItem value="raw-reasoning" className="border-b-0">
                      <AccordionTrigger className="text-sm">Raw engine reasoning (advanced)</AccordionTrigger>
                      <AccordionContent className="whitespace-pre-wrap text-sm">{r.reasoning}</AccordionContent>
                    </AccordionItem>
                  </Accordion>
                </div>
              </Card>
            </motion.article>
          )
        })}

        <Card>
          <div className="flex items-center gap-2.5 border-b border-border p-5 sm:p-6">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-primary/12 text-primary">
              <Bot className="h-4.5 w-4.5" />
            </span>
            <div>
              <h3 className="font-display text-base font-semibold">Ask the recruiter copilot</h3>
              <p className="text-sm text-muted-foreground">Every answer cites the evidence behind it.</p>
            </div>
          </div>
          <div className="p-5 sm:p-6">
            <CopilotPanel
              jobId={jobId}
              candidateIds={results.map((r) => r.candidate_id)}
              emptyHint="Ask anything about these candidates — comparisons, missing skills, or why someone ranks higher."
            />
          </div>
        </Card>
      </div>
    </div>
  )
}
