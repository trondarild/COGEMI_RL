# Online Experiment Plan — Social Appropriateness

## Research question

What are the contextual norms governing social appropriateness of everyday actions?
We collect human judgments on a curated set of (action, setting) scenarios and feed them into the COGEMI pipeline to learn context clusters and generalise to new situations.

---

## Study design

| Parameter | Value |
|---|---|
| Dimension | Social appropriateness |
| Response scale | Inappropriate / Neutral / Appropriate |
| Scenarios per participant | 25 (random subset) + 2 attention checks |
| Target ratings per scenario | 15 |
| Languages | English (primary); French (secondary) |
| Participant metadata | age, gender, country of origin, first language |
| Platform | Prolific → Google Apps Script form → Google Sheets → COGEMI |

### Scenario pool

40 scenarios covering 8 action types × 5 settings each.
Scenario IDs follow COGEMI convention: `sa_{action}_{setting}` (e.g. `sa_cutinline_cinema`).

| Action | Settings |
|---|---|
| `cutinline` | supermarket, cinema, busstop, emergency, border |
| `holdoor` | office, elevator, shop, street, rain |
| `speakloud` | library, cafe, restaurant, cinema, publictransport |
| `phonetable` | family_dinner, date, meeting, funeral, cafe |
| `littering` | park, beach, street, publictransport, forest |
| `ignoregreet` | office, neighborhood, gym, elevator, party |
| `offerhelp` | stranger_directions, grocery_bags, door, crying, fallen |
| `personalspace` | queue, elevator, empty_bus, bench, waiting_room |

### Attention checks (embedded, fixed responses expected)

- `sa_check_obvious_appropriate` — "Someone holds the door open for the person directly behind them." → expected: Appropriate
- `sa_check_obvious_inappropriate` — "Someone pushes past a queue of people waiting at a hospital reception." → expected: Inappropriate

Participants failing both attention checks are excluded from analysis.

### Randomisation

- Scenarios are shuffled per participant.
- Attention checks are placed at positions 8 and 18 of the 27-item sequence.
- All participants see the same attention checks.

---

## Data collection → COGEMI pipeline mapping

| Survey field | COGEMI field |
|---|---|
| `prolific_id` | `SurveyResponse.participant_id` |
| `scenario_id` | `SurveyResponse.scenario_id` |
| `response` | `SurveyResponse.response` ∈ {Inappropriate, Neutral, Appropriate} |

The judgment map for the pipeline:
```python
{"Inappropriate": -1, "Neutral": 0, "Appropriate": 1}
```

Scenario IDs decode as: prefix=`sa`, action=index 1, state=index 2.

---

## Prolific budget estimate

### Pilot (40 scenarios, 15 ratings each)

| Item | Calculation | Cost |
|---|---|---|
| Participants needed | 40 scenarios × 15 ratings ÷ 25 per session | 24 |
| Session time | 27 items × ~12 s + consent + demographics | ~8 min |
| Pay per participant | £9/hr × 8/60 | £1.20 |
| Participant total | 24 × £1.20 | £28.80 |
| Prolific fee (33%) | £28.80 × 0.33 | £9.50 |
| **Pilot total** | | **~£38** |

### Full study (200 scenarios, 15 ratings each)

| Item | Calculation | Cost |
|---|---|---|
| Participants needed | 200 × 15 ÷ 25 | 120 |
| Participant total | 120 × £1.20 | £144 |
| Prolific fee (33%) | £144 × 0.33 | £47.52 |
| **Full study total** | | **~£192** |

> Prolific minimum pay rate as of 2025: £9.00/hr. Adjust if rate changes.
> VAT may apply depending on institution billing arrangement.

### Recommended approach

Run the pilot (24 participants, ~£38) first. Inspect inter-rater agreement (Krippendorff's α) and context cluster quality before committing to the full study.

---

## Timeline

1. Finalise scenario texts and translations → survey form ready
2. Internal pilot: 5 lab members rate all 40 scenarios (check wording, timing)
3. Prolific pilot: 24 participants
4. Analyse: inter-rater agreement, COGEMI context clusters, attention-check pass rate
5. Decide: extend to full 200-scenario study or refine scenarios first
6. Full Prolific study if warranted

---

## Ethical considerations

- Consent screen with opt-out before any scenarios are shown
- No deception; scenarios are fictional third-person vignettes
- No personally identifiable information collected beyond Prolific ID (which is pseudonymous)
- Data stored in Google Sheets accessible only to research team
- Prolific IDs deleted from analysis dataset after payment verification
