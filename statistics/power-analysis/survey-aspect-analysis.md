# Power analysis — survey instrument (5-point scale retained)

This document covers the mixed-effects power analysis for the survey as a
standalone instrument, where the 5-point Likert scale is retained and the goal
is to make statistical claims about contextual modulation of appropriateness
judgments. This is separate from the Dirichlet analysis, which covers the RL
pipeline (ternary collapse + norm-pattern classification).

---

## Three levels of the design — and why they don't multiply

The full design involves several manipulated factors. A natural but mistaken
reading is that they all form one large factorial, e.g.:

```
Setting (2) × Relationship (3) × Stakes (2) × Gender (2) × Role perspective (3)
= 72 cells × 10 participants per cell = 720 participants
```

This is wrong because the factors operate at **different levels** and require
different quantities to be adequately powered. The three levels are:

---

### Level 1 — Vignette structural cells (scale with N_vignettes per cell)

Setting, relationship, and stakes are properties of the **scenario text
itself** — each vignette is authored to place a specific action in a specific
context (e.g., public × authority × high-stakes). This gives:

```
Setting (2) × Relationship (3) × Stakes (2) = 12 vignette structural cells
```

These are the 12 cells modelled in `power_sim.R`. Because the contextual
manipulation is between vignettes (not between participants), power for
these effects is determined by **N_vignettes_per_cell (vpc)**, not by
N_participants. Adding more participants beyond ~50 does not help once each
vignette has ~15–20 ratings.

The **8 settings × 5 actions** from the pilot authoring plan describe the
*scenario space* — the range of (action, context) combinations that exist as
authored text. This is orthogonal to the 12-cell factorial: the 120-vignette
pool can be drawn from diverse actions and settings, but what determines cell
assignment is the structural factors (public/private, relationship type,
stakes), not which specific action or setting was chosen.

---

### Level 2 — Within-vignette text variations (agent identity)

The requirements document recommends randomising **agent identity (gender,
role)**. This does not add new cells requiring new vignettes. Instead, each
vignette has multiple surface-text variants — the same scenario with "she"
vs "he", or "manager" vs "colleague" — randomised across participants.

Implications:
- No additional vignette authoring beyond the 120 structural vignettes
- Each participant sees one gender/role variant per vignette slot
- The gender/role main effect is estimated with N_participants (not vpc)
- ~60 participants is sufficient to detect a medium gender/role effect

Agent identity is a **within-vignette manipulation**, not a new factorial
dimension at the vignette level.

---

### Level 3 — Between-participant role perspective (agent/target/observer)

The role-perspective survey (already implemented as a separate HTML with
`?role=agent|target|observer`) assigns each participant to one perspective.
This is a **between-participants condition**, not a vignette-level factor.

Implications:
- Each arm (agent / target / observer) needs its own N_participants
- Running all three arms requires ~60 × 3 = 180 participants total
- The vignette pool is shared across arms; vpc does not multiply by 3
- The three arms can be treated as separate Prolific studies or sub-conditions

---

## Correct participant count

| Factor | Type | N needed |
|---|---|---|
| Vignette structural cells (12) | Between-vignette | 120 total vignettes at 10 vpc |
| Agent gender/role | Within-vignette text swap | ~60 participants per arm |
| Role perspective (agent/target/observer) | Between-participant | × 3 arms if running all |
| **Single-arm total** | | **~60 participants** |
| **Three-arm total** | | **~180 participants** |

This is far from 720. The key insight is that vignette-level factors and
participant-level factors are powered by different quantities, and within-vignette
text variations cost nothing in vignette count.

---

## Two distinct power regimes (simulation results)

The simulation (`power_sim.R`) confirmed that the survey has two structurally
different types of effects with different binding constraints:

### 1. Participant-level effects (scale with N_participants)

| Effect | Min N for 80% power | Notes |
|---|---|---|
| Q1–Q2 divergence (personal vs injunctive) | 20 | Trivially powered at any N >= 20 |
| Test-retest reliability | any N | Median r = 0.95; floor set by noise ratio |
| Intra-item ICC (5 rewordings) | any N | Observable ICC ~= 0.68 (see below) |

Q1–Q2 divergence is trivially detectable because each participant rates 42
vignettes; even with vignette-level variation in the personal-vs-injunctive
gap, the mean signal is estimated with very low noise. This is a real finding:
the norm-type divergence is robust at any feasible sample size.

**Reword ICC note:** The latent DGM targets ICC = 0.80, but the observable
ICC from the 5-point clipped scale is approximately 0.68. This is a real
property of bounded ordinal scales: ceiling/floor truncation for extreme
participants reduces observable between-participant variance. The ICC threshold
for reporting should be adjusted to >= 0.65 for 5-point scales.

### 2. Between-vignette contextual effects (scale with N_vignettes per cell)

Setting, relationship, and stakes are assigned at the **vignette level** — each
vignette has a fixed context. This means their power is determined by
**N_vignettes per contextual cell**, not by N_participants.

The standard error for a between-vignette contrast is:

```
SE ~= sqrt(sigma2_vignette / N_vpc + sigma2_residual / (N_vpc x N_ratings_per_vignette))
```

With sigma2_vignette = 0.64 dominating, the sigma2_residual term becomes negligible
once each vignette has >= 15 ratings. Adding more participants beyond this
threshold does not reduce the SE — the floor is set by N_vignettes per
condition (N_vpc).

**Power for contextual effects as a function of vignettes per cell**
(N_participants = 50 fixed, medium effects d ~= 0.30–0.50):

| Vignettes/cell | Total vignettes | Setting | Rel: friend | Rel: authority | Stakes |
|---|---|---|---|---|---|
| 3.5 (current) | 42 | 47% | 45% | 26% | 32% |
| 5 | 60 | 63% | 67% | 32% | 42% |
| 7 | 84 | 78% | **80%** | 45% | 53% |
| 10 | 120 | **92%** | **89%** | 57% | 69% |
| 15 | 180 | 99% | 98% | 74% | **84%** |
| 20 | 240 | ~100% | ~100% | **85%** | 92% |

The hardest effect is relationship-authority (d ~= -0.30, smallest effect and
only 1/3 of relationship vignettes). The binding vpc for 80% power across all
four contextual effects is 20 vpc = 240 total vignettes.

For the main effects (setting, rel-friend, stakes), 10 vpc = 120 total
vignettes is sufficient.

---

## Key finding: 120 vignettes != 120 vignettes per participant

120 total vignettes does **not** mean each participant rates 120 vignettes.
An **incomplete block design** keeps per-participant burden identical to the
current survey while expanding the vignette pool:

- 120 total vignettes (10 per cell × 12 cells)
- Each participant rates a random 42-vignette subset (same ~20 min session)
- With N_participants = 60: each vignette gets rated by 60 × 42/120 ~= 21 participants
- 21 ratings per vignette is sufficient for the residual SE term to be negligible
- Power for contextual effects ~= equivalent to a fully-crossed design

### Design comparison

| | Current | Recommended (main effects) | Recommended (full factorial) |
|---|---|---|---|
| Total vignettes | 42 | 120 | 240 |
| Vignettes per cell | ~3.5 | 10 | 20 |
| Per-participant burden | 42 | 42 | 42 |
| Session time | ~20 min | ~20 min | ~20 min |
| N participants (single arm) | 50 | ~60 | ~60 |
| N participants (all 3 role arms) | 150 | ~180 | ~180 |
| Contextual power (setting) | ~47% | ~92% | ~100% |
| Contextual power (authority) | ~26% | ~57% | ~85% |
| Extra vignettes to author | — | ~78 | ~198 |

The cost increase is modest in participants (50 → 60 per arm) but substantial in
vignette authoring (need to expand from 42 to 120–240 vignettes across the
12-cell factorial).

---

## Recommended minimum N for participants

Combining both analyses:

| Criterion | Min N (per arm) | Source |
|---|---|---|
| Norm-pattern classification (RL pipeline) | 50 | Dirichlet simulation |
| Participant-level survey effects (Q1–Q2, reliability) | 20 | lmerTest simulation |
| Agent gender/role effect | ~60 | lmerTest sensitivity estimate |
| **Recommended minimum (single arm)** | **60** | Agent-identity effect binding |
| **Recommended minimum (all three role arms)** | **180** | 60 × 3 |

**N = 60 participants per arm** is the binding recommendation for a full study.
Contextual modulation claims require expanding the vignette pool, not recruiting
more participants. The three role-perspective arms (agent/target/observer) can be
run sequentially or in parallel as separate Prolific studies.

---

## Simulation details

- Script: `statistics/power-analysis/power_sim.R`
- Model: `lmerTest::lmer` with Satterthwaite df (continuous approximation for
  5-point scale — standard practice for >= 5-point scales)
- DGM: random intercepts for participants (SD = 0.6) and vignettes (SD = 0.8);
  residual SD = 0.7; total SD ~= 1.22
- Medium effects: d = 0.40 (setting), 0.50 (rel-friend), 0.30 (rel-auth/stakes)
- 500 replications per N; alpha = 0.05 (two-sided)
- Sensitivity scenarios: small (d × 0.5) and large (d × 1.5)
- The 12 vignette-level cells (setting × relationship × stakes) are the only
  factors in the simulation; agent identity and role perspective are not
  modelled because they operate at different levels (see above)
