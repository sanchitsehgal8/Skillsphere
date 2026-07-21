import { GitBranch, Clock, HardDrive } from 'lucide-react'
import { Meter } from './ui/meter'
import { Badge } from './ui/badge'
import { EmptyState } from './ui/misc'
import { formatBytes, scoreTone } from '../lib/utils'

export default function SkillEvidenceList({ skills = [] }) {
  if (!skills.length) {
    return (
      <EmptyState
        icon={GitBranch}
        title="No verified skills yet"
        description="Add a GitHub username or resume to build evidence-backed skill signals."
      />
    )
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {skills.map((s) => (
        <div key={s.name} className="rounded-xl border border-border bg-surface/40 p-4 transition-colors hover:border-foreground/10">
          <div className="mb-2.5 flex items-center justify-between gap-2">
            <span className="font-medium text-foreground">{s.name}</span>
            <span className="font-mono text-xs font-semibold text-foreground">{s.score.toFixed(0)}/100</span>
          </div>
          <Meter value={s.score} tone={scoreTone(s.score)} />

          <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-2xs text-muted-foreground">
            <span className="font-medium text-foreground/70">{Math.round(s.confidence * 100)}% conf</span>
            {s.repo_count > 0 && (
              <span className="inline-flex items-center gap-1">
                <GitBranch className="h-3 w-3" /> {s.repo_count} repo{s.repo_count === 1 ? '' : 's'}
              </span>
            )}
            {formatBytes(s.loc_bytes) && (
              <span className="inline-flex items-center gap-1">
                <HardDrive className="h-3 w-3" /> {formatBytes(s.loc_bytes)}
              </span>
            )}
            {s.commit_recency_days != null && (
              <span className="inline-flex items-center gap-1">
                <Clock className="h-3 w-3" /> {s.commit_recency_days}d ago
              </span>
            )}
          </div>

          {!!s.frameworks?.length && (
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {s.frameworks.map((f) => (
                <Badge key={`${s.name}-fw-${f}`} variant="primary" size="sm">
                  {f}
                </Badge>
              ))}
            </div>
          )}

          {s.reasoning && <p className="mt-2.5 text-xs leading-relaxed text-muted-foreground">{s.reasoning}</p>}
          {!!s.suggestions?.length && (
            <p className="mt-1.5 text-xs text-primary/90">↳ {s.suggestions[0]}</p>
          )}
        </div>
      ))}
    </div>
  )
}
