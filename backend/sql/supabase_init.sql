-- Run in Supabase SQL editor before deploying backend persistence.

create table if not exists public.jobs (
  owner_id text not null,
  job_id text not null,
  title text not null,
  description text not null,
  requirements jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  primary key (owner_id, job_id)
);

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

create index if not exists idx_jobs_owner on public.jobs(owner_id);
create index if not exists idx_candidates_owner on public.candidates(owner_id);