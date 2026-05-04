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
