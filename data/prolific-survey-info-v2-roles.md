# Prolific Study Registration Info — v2 role router (pilot)

**One** Prolific study of 30 places. The role arm — agent, target, observer —
is drawn server-side when the participant opens the survey. Everything below
is ready to paste into the Prolific study setup form.

Supersedes two earlier plans:

- `prolific-survey-info.md` — the v1 single-arm study (3-point scale, ~12 min,
  £1.80). Kept for the record.
- The three-separate-studies design described in earlier revisions of this
  file, along with the per-arm HTML files
  `appropriateness_survey_aspects_park_prolific_v2_{agent,target,observer}.html`
  and `set_completion_codes.sh`. They still work, but see "Why one study".

---

## Why one study

The three arms must draw disjoint participants. Prolific's *previously
participated in studies* prescreener is unreliable for studies running at the
same time, so three concurrent studies can leak a participant into two arms;
enforcing separation there means publishing strictly in sequence and waiting
for each arm to fill.

Prolific does structurally prevent a participant from submitting the **same**
study twice. So one study with a server-side role draw makes the arms disjoint
by construction, releases all 30 places at once, and — because the study title
is identical for everyone — removes any chance of self-selection into a
perspective.

The draw is a pool, not a coin flip: `claim_role()` assigns the least-filled
arm under an advisory lock, giving exactly 10/10/10. Sampling each role
independently at 1/3 would land on splits like 7/11/12 about as often as not.

---

## Instrument

Same scenario pool in all three arms; only the framing of Q1/Q2 and the
consent intro differ, and those are selected at runtime from `ROLE_TEXT`.

The target arm sees one extra line under each vignette naming the position it
is to take — "In this situation you are: one of the joggers being shouted at."
About half the pool has no addressee: nobody is on the receiving end of someone
applying makeup or leaving litter. Without a named position the target arm
collapses into the observer arm on those items, and participants improvise
different resolutions. Each scenario is tagged `directed` (17 items, the action
is aimed at that person) or incidental (23, it merely lands on them), and the
tag is written to `responses_v2.target_directed` on every arm. Targetedness is
close to confounded with the action factor — kiss and money are almost all
directed, makeup and litter none — so compare the target–observer gap within
each level rather than pooling across items.

| | |
|---|---|
| Items per participant | 47 — 40 park scenarios, 2 attention checks (positions 10 and 22), 5 test-retest repeats at the end |
| Per item | Q1 personal appropriateness (1–5), Q2 injunctive norm (1–5), Q3 empirical expectation (rarely/sometimes/often), confidence (1–5), rank 3 aspects |
| Every 10 main scenarios | perceived-disagreement item (1–5) |
| Estimated duration | 22 min |
| Reward | £3.00 (£8.18/hr at 22 min — above the £6.00/hr Prolific floor, below the £9.00/hr "fair" mark; £3.30 buys the fair badge if you want it) |
| Cost, pilot | 30 participants × £3.00 = £90 + ~33% fee ≈ **£120 total** |

---

## Study name (participant-facing)

**Judging Everyday Social Situations**

## Internal study name (researcher-facing)

`COGEMI v2 pilot — role router (30 = 3×10) — park scenarios — Jul 2026`

---

## Study description (participant-facing)

> In this study you will read a series of short descriptions of everyday
> situations taking place in a public park. For each situation you will
> judge how socially appropriate the action is, how appropriate you think
> most people would consider it, and how often you think it happens. You
> will then rank which aspects of the situation most influenced your
> judgement.
>
> The study consists of 47 short scenarios and takes around 22 minutes.
> There are no right or wrong answers — we are interested in your personal
> judgements.

The perspective a participant is asked to take is assigned and stated on the
first page of the survey itself, so it need not appear in the listing.

---

## Survey URL

Paste the whole line, placeholders included — Prolific substitutes them.

```
https://trondarild.github.io/cavaa/appropriateness_survey_aspects_park_prolific_v2_roles.html?PROLIFIC_PID={{%PROLIFIC_PID%}}&STUDY_ID={{%STUDY_ID%}}&SESSION_ID={{%SESSION_ID%}}
```

A participant arriving without `PROLIFIC_PID` sees a "must be accessed via
your Prolific study link" page and cannot start. One arriving with an ID gets
a role before the consent page renders; a reload returns the same role.

---

## Completion

Set completion to **"Redirect to a URL"** (participants are redirected
automatically; there is no code to type). Prolific issues one completion code
for the study. It must be written into the HTML before publishing:

```
cogemi/survey/set_completion_code_roles.sh <CODE>   # patch
cogemi/survey/deploy_to_pages.sh                    # publish
```

`set_completion_code_roles.sh` only edits the file. `deploy_to_pages.sh` is
the sanctioned way to publish, and it refuses to push a file still carrying a
placeholder — which is the failure worth guarding: a study that runs to
completion and then redirects every participant to an invalid Prolific URL.

---

## Eligibility

- Fluent English speakers
- Approval rate ≥ 95%, minimum 10 previous submissions
- Desktop/laptop only if the option is available — the aspect-ranking
  interaction is awkward on a phone
- No arm exclusions needed. Disjointness comes from the study itself.

---

## Pre-launch checklist

1. Run the **Role router** section of
   `cogemi/survey/appropriateness_survey_supabase_setup.sql` in the Supabase
   SQL editor. It creates `role_assignments` and the four functions the page
   calls. The `role` and `target_directed` columns on `responses_v2` (the two
   sections above it) must also be in place — without either, every insert
   400s and the study silently collects nothing.
2. Run the live integration tests, which check exactly that:
   ```
   COGEMI_LIVE_SUPABASE=1 .venv/bin/python -m pytest tests/test_integration_role_router.py -v
   ```
   They write only `__smoketest__…` rows and purge themselves afterwards.
   Run them **before** publishing — the balance test claims 30 slots, and it
   refuses to run once real participants are in the pool.
3. Confirm Prolific balance ≥ £120.
4. Create the study as a draft (30 places), note the completion code.
5. `cogemi/survey/set_completion_code_roles.sh <CODE>` — patches both
   occurrences in the HTML.
6. `cogemi/survey/deploy_to_pages.sh` — checks for leftover placeholders,
   parses the inline JS, runs the structural tests, shows what would change,
   then copies to `~/code/trondarild.github.io/cavaa/`, commits and pushes.
   Use `--dry-run` first if you want to see the file list without publishing.
   Wait ~1 min for the Pages build.
7. Open the Prolific preview link yourself, confirm a role is assigned and
   rows land in `responses_v2` with that role, then remove your test rows.
8. Publish. All 30 places at once.

---

## Watching it fill

`role_assignment_counts()` returns claimed/completed per arm, and no
participant identifiers:

```
curl -s -X POST "$SUPABASE_URL/rest/v1/rpc/role_assignment_counts" \
  -H "apikey: $ANON_KEY" -H "Authorization: Bearer $ANON_KEY" \
  -H "Content-Type: application/json" -d '{}'
```

Unfinished claims older than two hours are released back to the pool on the
next draw, so returns and timeouts do not permanently consume a slot.
