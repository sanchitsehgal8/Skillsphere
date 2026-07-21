import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import {
  ArrowRight,
  ArrowUpDown,
  ChevronDown,
  Download,
  Gauge,
  RotateCcw,
  Search,
  Sparkles,
  Users,
} from 'lucide-react'
import { PageHeading } from '../components/shell/PageHeading'
import { StatCard } from '../components/common/StatCard'
import { Pagination } from '../components/common/Pagination'
import {
  Avatar,
  Badge,
  Button,
  Card,
  EmptyState,
  Input,
  Label,
  Meter,
  Select,
  Skeleton,
  Slider,
} from '../components/ui'
import { useToast } from '../components/ui'
import ScorecardBreakdown from '../components/ScorecardBreakdown'
import SkillEvidenceList from '../components/SkillEvidenceList'
import { listCandidates } from '../api/client'
import { cn, downloadCsv, scoreTone } from '../lib/utils'

const PAGE_SIZE = 6

export default function CandidatesPage() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [searchParams] = useSearchParams()

  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expandedId, setExpandedId] = useState(null)

  const [query, setQuery] = useState(searchParams.get('query') || '')
  const [minScore, setMinScore] = useState(0)
  const [scoreSort, setScoreSort] = useState('default')
  const [page, setPage] = useState(1)

  useEffect(() => {
    let mounted = true
    async function load() {
      setLoading(true)
      setError('')
      try {
        const rows = await listCandidates()
        if (mounted) setCandidates(rows)
      } catch (e) {
        if (mounted) setError(e?.response?.data?.detail || e.message || 'Failed to load candidates')
      } finally {
        if (mounted) setLoading(false)
      }
    }
    load()
    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    setQuery(searchParams.get('query') || '')
    setPage(1)
  }, [searchParams])

  const filteredItems = useMemo(() => {
    const q = query.trim().toLowerCase()
    const filtered = candidates.filter((c) => {
      const matchesQuery =
        !q ||
        c.evidence.name.toLowerCase().includes(q) ||
        c.evidence.candidate_id.toLowerCase().includes(q)
      const matchesScore = c.scorecard.overall_score >= minScore
      return matchesQuery && matchesScore
    })
    if (scoreSort === 'desc') filtered.sort((a, b) => b.scorecard.overall_score - a.scorecard.overall_score)
    if (scoreSort === 'asc') filtered.sort((a, b) => a.scorecard.overall_score - b.scorecard.overall_score)
    return filtered
  }, [candidates, minScore, query, scoreSort])

  const avgScore = candidates.length
    ? Math.round(candidates.reduce((acc, c) => acc + c.scorecard.overall_score, 0) / candidates.length)
    : 0
  const strongCount = candidates.filter((c) => c.scorecard.overall_score >= 75).length

  const totalPages = Math.max(1, Math.ceil(filteredItems.length / PAGE_SIZE))
  const safePage = Math.min(page, totalPages)
  const pagedItems = filteredItems.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE)

  const filtersActive = query.trim() !== '' || minScore > 0 || scoreSort !== 'default'

  function resetFilters() {
    setQuery('')
    setMinScore(0)
    setScoreSort('default')
    setPage(1)
  }

  function exportCsv() {
    if (!filteredItems.length) {
      return toast({
        title: 'Nothing to export',
        description: candidates.length ? 'No candidates match the current filters.' : 'Analyze a candidate first.',
        variant: 'info',
      })
    }
    downloadCsv(
      `skillsphere-candidates-${Date.now()}.csv`,
      ['candidateId', 'name', 'overallScore', 'confidence', 'evidenceCompleteness', 'topSkills'],
      filteredItems.map((c) => [
        c.evidence.candidate_id,
        c.evidence.name,
        c.scorecard.overall_score,
        c.scorecard.overall_confidence,
        c.scorecard.evidence_completeness,
        c.scorecard.skills.slice(0, 3).map((s) => s.name).join(' | '),
      ]),
    )
    toast({
      title: 'Export ready',
      description: `${filteredItems.length} candidate${filteredItems.length === 1 ? '' : 's'} downloaded.`,
      variant: 'success',
    })
  }

  return (
    <div>
      <PageHeading
        eyebrow="Talent board"
        title="All candidates"
        subtitle="Every analyzed profile with its evidence-based engineering scorecard."
        actions={
          <Button variant="outline" onClick={exportCsv}>
            <Download className="h-4 w-4" /> Export CSV
          </Button>
        }
      />

      {error && (
        <div className="mb-6 rounded-xl border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">{error}</div>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard icon={Users} label="Candidates" value={candidates.length} hint="Profiles with a scorecard" tone="primary" delay={0} loading={loading} />
        <StatCard icon={Gauge} label="Avg score" value={avgScore} suffix="/100" hint="Across the full board" tone="accent" delay={0.06} loading={loading} />
        <StatCard icon={Sparkles} label="Strong (≥75)" value={strongCount} hint={`Of ${candidates.length} analyzed`} tone="success" delay={0.12} loading={loading} />
      </div>

      <Card className="mt-6 p-5">
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)_minmax(0,0.9fr)] lg:items-end">
          <div>
            <Label htmlFor="candidate-search">Search</Label>
            <div className="relative">
              <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="candidate-search"
                className="pl-10"
                placeholder="Search by name or ID…"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value)
                  setPage(1)
                }}
              />
            </div>
          </div>

          <div>
            <div className="mb-1.5 flex items-center justify-between">
              <Label className="mb-0">Min overall score</Label>
              <span className="font-mono text-xs font-semibold text-foreground">{minScore}</span>
            </div>
            <div className="flex h-11 items-center">
              <Slider
                value={[minScore]}
                onValueChange={([v]) => {
                  setMinScore(v)
                  setPage(1)
                }}
                min={0}
                max={100}
                step={1}
                aria-label="Minimum overall score"
              />
            </div>
          </div>

          <div>
            <Label htmlFor="candidate-sort">Sort by</Label>
            <div className="relative">
              <ArrowUpDown className="pointer-events-none absolute left-3.5 top-1/2 z-10 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Select
                id="candidate-sort"
                className="pl-10"
                value={scoreSort}
                onChange={(e) => {
                  setScoreSort(e.target.value)
                  setPage(1)
                }}
              >
                <option value="default">Default order</option>
                <option value="desc">Score: high to low</option>
                <option value="asc">Score: low to high</option>
              </Select>
            </div>
          </div>
        </div>

        {filtersActive && (
          <div className="mt-4 flex items-center justify-between gap-3 border-t border-border pt-4">
            <span className="text-xs text-muted-foreground">
              <span className="font-medium text-foreground">{filteredItems.length}</span> of {candidates.length} match
            </span>
            <Button variant="subtle" size="sm" onClick={resetFilters}>
              <RotateCcw className="h-3.5 w-3.5" /> Reset filters
            </Button>
          </div>
        )}
      </Card>

      <Card className="mt-6">
        <div className="hidden items-center gap-4 border-b border-border px-5 py-3 text-2xs font-semibold uppercase tracking-wide text-muted-foreground sm:grid sm:grid-cols-[1.6fr_1.2fr_0.7fr_0.4fr]">
          <span>Candidate</span>
          <span>Overall score</span>
          <span>Confidence</span>
          <span className="text-right">Detail</span>
        </div>

        {loading ? (
          <div className="space-y-3 p-5">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : !candidates.length ? (
          <EmptyState
            icon={Sparkles}
            title="No candidates analyzed yet"
            description="Run your first evidence-based analysis to populate the talent board."
            action={
              <Button onClick={() => navigate('/analyze')}>
                Analyze a candidate <ArrowRight className="h-4 w-4" />
              </Button>
            }
          />
        ) : !filteredItems.length ? (
          <EmptyState
            icon={Search}
            title="No candidates match your filters"
            description="Try loosening the score threshold or clearing the search query."
            action={
              <Button variant="outline" onClick={resetFilters}>
                <RotateCcw className="h-4 w-4" /> Reset filters
              </Button>
            }
          />
        ) : (
          <>
            <div className="divide-y divide-border">
              {pagedItems.map((c, i) => {
                const id = c.evidence.candidate_id
                const isOpen = expandedId === id
                const score = c.scorecard.overall_score
                const tone = scoreTone(score)
                const confidence = Math.round((c.scorecard.overall_confidence || 0) * 100)
                return (
                  <motion.div
                    key={id}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.04, duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
                  >
                    <button
                      type="button"
                      onClick={() => setExpandedId(isOpen ? null : id)}
                      aria-expanded={isOpen}
                      className={cn(
                        'grid w-full grid-cols-1 items-center gap-4 px-5 py-4 text-left transition-colors hover:bg-secondary/40 sm:grid-cols-[1.6fr_1.2fr_0.7fr_0.4fr]',
                        isOpen && 'bg-secondary/40',
                      )}
                    >
                      <div className="flex min-w-0 items-center gap-3">
                        <Avatar name={c.evidence.name} size="md" />
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium text-foreground">{c.evidence.name}</p>
                          <p className="truncate text-xs text-muted-foreground">{c.evidence.headline || id}</p>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="hidden w-32 sm:block">
                          <Meter value={score} tone={tone} />
                        </div>
                        <Badge tone={tone} size="sm">
                          {score.toFixed(0)}
                        </Badge>
                        <div className="ml-1 flex flex-1 flex-wrap gap-1.5 sm:hidden">
                          {c.scorecard.skills.slice(0, 2).map((s) => (
                            <Badge key={`${id}-m-${s.name}`} variant="outline" size="sm">
                              {s.name}
                            </Badge>
                          ))}
                        </div>
                      </div>

                      <div className="text-sm text-muted-foreground">
                        <span className="font-mono font-medium text-foreground">{confidence}%</span> conf
                      </div>

                      <div className="flex items-center justify-end gap-2">
                        <div className="hidden flex-wrap justify-end gap-1.5 lg:flex">
                          {c.scorecard.skills.slice(0, 2).map((s) => (
                            <Badge key={`${id}-${s.name}`} variant="outline" size="sm">
                              {s.name}
                            </Badge>
                          ))}
                          {!c.scorecard.skills.length && (
                            <span className="text-2xs text-muted-foreground">No verified skills</span>
                          )}
                        </div>
                        <ChevronDown
                          className={cn(
                            'h-4 w-4 shrink-0 text-muted-foreground transition-transform',
                            isOpen && 'rotate-180',
                          )}
                        />
                      </div>
                    </button>

                    <AnimatePresence initial={false}>
                      {isOpen && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                          className="overflow-hidden"
                        >
                          <div className="space-y-6 border-t border-border bg-surface/30 px-5 py-6">
                            <section>
                              <h4 className="mb-3 font-display text-sm font-semibold text-foreground">Full scorecard</h4>
                              <ScorecardBreakdown dimensions={c.scorecard.dimensions} />
                            </section>
                            <section>
                              <h4 className="mb-3 font-display text-sm font-semibold text-foreground">Verified skills</h4>
                              <SkillEvidenceList skills={c.scorecard.skills} />
                            </section>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                )
              })}
            </div>
            <Pagination
              page={safePage}
              totalPages={totalPages}
              onChange={(p) => setPage(Math.min(totalPages, Math.max(1, p)))}
              total={filteredItems.length}
              pageSize={PAGE_SIZE}
            />
          </>
        )}
      </Card>

      {!loading && !!candidates.length && (
        <Card interactive className="group mt-6 flex cursor-pointer items-center justify-between gap-4 p-5" onClick={() => navigate('/analyze')}>
          <div className="flex items-center gap-4">
            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary/12 text-primary">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-display text-base font-semibold">Analyze a new candidate</h3>
              <p className="text-sm text-muted-foreground">Résumé + GitHub → instant evidence-based score.</p>
            </div>
          </div>
          <ArrowRight className="h-5 w-5 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
        </Card>
      )}
    </div>
  )
}
