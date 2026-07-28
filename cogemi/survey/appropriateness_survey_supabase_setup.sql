-- supabase_setup.sql
-- Run this once in the Supabase SQL Editor for your project.
-- Creates tables for both the base appropriateness survey and the role-perspectives survey.

create table responses (
  id          bigint generated always as identity primary key,
  created_at  timestamptz default now(),
  prolific_id text,
  scenario_id text,
  response    text,
  age         text,
  gender      text,
  country     text,
  language    text
);

-- Enable row-level security: anyone can insert, nobody can read via the anon key.
alter table responses enable row level security;

create policy "anon insert"
  on responses
  for insert
  to anon
  with check (true);

-- ── Aspect-ranking variant (appropriateness_survey_aspects_ghpages.html) ────
-- Run only this section if the responses table already exists.
alter table responses add column if not exists aspect_ranking text;

-- ── Prolific pilot (appropriateness_survey_prolific.html) ────────────────────
-- Run only this section if the responses table already exists.
alter table responses add column if not exists study_id       text;
alter table responses add column if not exists session_id     text;
alter table responses add column if not exists completion_code text;

-- ── Role-perspectives survey (role_survey_ghpages.html) ─────────────────────
-- Run only this section if the responses table already exists.

create table role_responses (
  id               bigint generated always as identity primary key,
  created_at       timestamptz default now(),
  prolific_id      text,
  scenario_id      text,
  response         text,
  role_perspective text,   -- "agent" | "target" | "observer"
  agent_role       text,   -- e.g. "queue-jumper"
  target_role      text,   -- e.g. "waiting customer"
  context_words    text,   -- pipe-separated words clicked in order, e.g. "visibly|unwell"
  age              text,
  gender           text,
  country          text,
  language         text
);

alter table role_responses enable row level security;

create policy "anon insert"
  on role_responses
  for insert
  to anon
  with check (true);

-- ── Park role Prolific pilot (appropriateness_survey_aspects_park_role_prolific.html) ──
-- Run only this section if the role_responses table already exists.
alter table role_responses add column if not exists study_id        text;
alter table role_responses add column if not exists session_id      text;
alter table role_responses add column if not exists completion_code text;
alter table role_responses add column if not exists aspect_ranking  text;

-- ── Reference-level v2 (appropriateness_survey_aspects_park_prolific_v2.html) ────────
-- Separate table — run once to create it.

create table responses_v2 (
  id                     bigint generated always as identity primary key,
  created_at             timestamptz default now(),
  prolific_id            text,
  study_id               text,
  session_id             text,
  completion_code        text,
  scenario_id            text,
  norm_type              text,      -- "personal" | "injunctive" | "empirical" | "disagreement"
  response               text,      -- human-readable label
  response_value         integer,   -- 1–5 Likert or -1/0/1 for empirical
  confidence             integer,   -- 1–5 certainty (personal norm_type only)
  perceived_disagreement integer,   -- 1–5 (disagreement norm_type only)
  aspect_ranking         text,      -- pipe-separated aspects in ranked order
  is_repeat              boolean default false,
  language               text
);

alter table responses_v2 enable row level security;

create policy "anon insert"
  on responses_v2
  for insert
  to anon
  with check (true);

-- ── Role arms (v2_agent / v2_target / v2_observer) ──────────────────────────
-- Required before the role-arm pilot: the arm files post a `role` field on
-- every scenario row, and PostgREST rejects the whole insert if the column
-- is absent. Safe to re-run.

alter table responses_v2 add column if not exists role text;   -- "agent" | "target" | "observer"

create index if not exists responses_v2_role_idx on responses_v2 (role);

-- ── Role router (appropriateness_survey_aspects_park_prolific_v2_roles.html) ─
-- Single Prolific study, role drawn server-side at entry. Prolific prevents a
-- participant from submitting the same study twice, so one study with a
-- server-side draw guarantees disjoint arms; three separate studies do not,
-- because the "exclude previous participants" prescreener is unreliable for
-- concurrently running studies.
--
-- Run this whole section once. Every statement is safe to re-run.

create table if not exists role_assignments (
  prolific_id  text primary key,
  role         text not null check (role in ('agent','target','observer')),
  claimed_at   timestamptz not null default now(),
  completed_at timestamptz
);

create index if not exists role_assignments_role_idx on role_assignments (role);

-- No policies: anon reaches this table only through the functions below,
-- which run as the table owner and so bypass RLS.
alter table role_assignments enable row level security;

-- How long an unfinished claim holds its slot before the pool reclaims it.
-- The instrument runs ~22 min, so two hours leaves ample headroom while still
-- releasing slots abandoned by returns and timeouts.
--
-- claim_role: idempotent on prolific_id (a reload returns the same role) and
-- serialised by an advisory lock, so concurrent entrants cannot both read the
-- same "least filled" count and land in the same arm.
create or replace function claim_role(pid text)
returns text
language plpgsql
security definer
set search_path = public
as $$
declare r text;
begin
  if pid is null or btrim(pid) = '' then
    raise exception 'claim_role: prolific_id required';
  end if;

  select role into r from role_assignments where prolific_id = pid;
  if r is not null then return r; end if;

  perform pg_advisory_xact_lock(hashtext('claim_role'));

  -- re-check under the lock
  select role into r from role_assignments where prolific_id = pid;
  if r is not null then return r; end if;

  delete from role_assignments
   where completed_at is null
     and claimed_at < now() - interval '2 hours';

  select a.role into r
    from (values ('agent'),('target'),('observer')) as a(role)
    left join role_assignments ra on ra.role = a.role
   group by a.role
   order by count(ra.prolific_id), random()
   limit 1;

  insert into role_assignments (prolific_id, role) values (pid, r);
  return r;
end
$$;

-- complete_role: pins the claim so the reclaim sweep can never free a slot
-- that has already produced data.
create or replace function complete_role(pid text)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  update role_assignments
     set completed_at = coalesce(completed_at, now())
   where prolific_id = pid;
end
$$;

-- role_assignment_counts: aggregate only, no participant identifiers. Used by
-- the integration tests and for watching the pilot fill.
create or replace function role_assignment_counts()
returns table (role text, claimed bigint, completed bigint, smoketest bigint)
language sql
security definer
set search_path = public
as $$
  select a.role,
         count(ra.prolific_id)                                             as claimed,
         count(ra.completed_at)                                            as completed,
         count(*) filter (where ra.prolific_id like '\_\_smoketest\_\_%')  as smoketest
    from (values ('agent'),('target'),('observer')) as a(role)
    left join role_assignments ra on ra.role = a.role
   group by a.role
   order by a.role;
$$;

-- purge_smoketest_data: lets the integration tests clean up after themselves.
-- The prefix is fixed, not a parameter, so this can only ever remove rows a
-- test created — real Prolific IDs are 24 hex characters and never match.
create or replace function purge_smoketest_data()
returns integer
language plpgsql
security definer
set search_path = public
as $$
declare n integer;
begin
  delete from role_assignments where prolific_id like '\_\_smoketest\_\_%';
  get diagnostics n = row_count;
  delete from responses_v2     where prolific_id like '\_\_smoketest\_\_%';
  return n;
end
$$;

revoke all on function claim_role(text)          from public;
revoke all on function complete_role(text)       from public;
revoke all on function role_assignment_counts()  from public;
revoke all on function purge_smoketest_data()    from public;

grant execute on function claim_role(text)         to anon;
grant execute on function complete_role(text)      to anon;
grant execute on function role_assignment_counts() to anon;
grant execute on function purge_smoketest_data()   to anon;
