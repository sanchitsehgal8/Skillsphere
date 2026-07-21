-- SkillSphere schema migration.
-- Run this in the Supabase SQL editor (Project → SQL Editor → New query).
-- Every statement is additive/idempotent — safe to run against a database that
-- already has data from the earlier schema version.

-- ---------------------------------------------------------------------------
-- jobs: existing table, extended with the full parsed JobSpec payload.
-- ---------------------------------------------------------------------------
create table if not exists public.jobs (
  owner_id text not null,
  job_id text not null,
  title text not null,
  description text not null,
  requirements jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  primary key (owner_id, job_id)
);

alter table public.jobs add column if not exists spec jsonb not null default '{}'::jsonb;
alter table public.jobs add column if not exists seniority text;

-- ---------------------------------------------------------------------------
-- candidates: existing table, extended with evidence + computed scorecard.
-- ---------------------------------------------------------------------------
create table if not exists public.candidates (
  owner_id text not null,
  candidate_id text not null,
  name text not null,
  headline text,
  summary text,
  platforms jsonb not null default '[]'::jsonb,
  demographics jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  primary key (owner_id, candidate_id)
);

alter table public.candidates add column if not exists evidence jsonb not null default '{}'::jsonb;
alter table public.candidates add column if not exists scorecard jsonb not null default '{}'::jsonb;
alter table public.candidates add column if not exists updated_at timestamptz not null default now();

-- ---------------------------------------------------------------------------
-- analyses: NEW table — persists match results so they survive a page reload
-- or server restart (previously held only in ephemeral browser/server state).
-- ---------------------------------------------------------------------------
create table if not exists public.analyses (
  owner_id text not null,
  job_id text not null,
  candidate_id text not null,
  fit_score double precision not null,
  verdict text not null,
  overall_score double precision not null,
  result jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  primary key (owner_id, job_id, candidate_id)
);

create index if not exists idx_jobs_owner on public.jobs(owner_id);
create index if not exists idx_candidates_owner on public.candidates(owner_id);
create index if not exists idx_analyses_owner_job on public.analyses(owner_id, job_id);
create index if not exists idx_analyses_owner_created on public.analyses(owner_id, created_at desc);
