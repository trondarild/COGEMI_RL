# Prolific Setup Notes

Answers to meeting questions about running the COGEMI online experiments.

---

## 1. Does Prolific have a survey template? Can we use Google Forms?

**Prolific is a participant recruitment platform, not a survey builder.**
It works by redirecting participants to an external URL you provide, then collecting a completion code.

### Options for the survey form:

| Platform | Supports word-click ordering | Notes |
|---|---|---|
| **Our custom HTML** | ✅ Yes (already implemented) | Best choice. Host on GitHub Pages, Netlify, or any static server. |
| **Qualtrics** | ✅ Yes (with custom JS block) | Common in academia. Requires institutional licence. Complex to set up. |
| **Google Forms** | ❌ No | No custom JS. Cannot support the word-click interaction. |
| **SurveyMonkey / Typeform** | ❌ No | No custom JS for interactive elements. |
| **jsPsych / GORILLA** | ✅ Yes | Built for behavioural experiments. More setup work. |

**Recommendation:** Use our existing custom HTML surveys hosted on GitHub Pages (free, zero setup).

### How it works on Prolific:
1. Host the HTML file at a public URL (e.g. `https://yourname.github.io/cogemi-survey/`)
2. Append `?PROLIFIC_PID={{%PROLIFIC_PID%}}&STUDY_ID={{%STUDY_ID%}}` to the URL — Prolific auto-fills these.
3. The survey saves `PROLIFIC_PID` as the participant ID instead of the typed text box.
4. At the end, show the completion code (already in the HTML: `COGEMI2025`).
5. Prolific validates completion by the participant entering this code.

### Word-click ordering and Prolific:
Since our survey is a custom hosted webpage, the word-click interaction works exactly as locally tested. Prolific only cares about the completion URL redirect — it has no visibility into what happens on our page.

---

## 2. How to estimate pay — do participants only get money if they complete in time?

**No time cap.** Prolific uses a fixed reward per completion, not a time-based payment:
- Participants are shown your estimated completion time before accepting.
- They receive the fixed reward when they submit the completion code, regardless of how long they took.
- If someone takes much longer than estimated they can request a bonus, but this is rare and optional.

### Pay calculation for our survey (20 scenarios + demographics):

| Phase | Estimated time |
|---|---|
| Consent + demographics | ~2 min |
| 20 scenarios × rating phase (~12s each) | ~4 min |
| 20 scenarios × word-click phase (~8s each) | ~3 min |
| **Total** | **~9 min** |

**Prolific minimum wage:** £9.00 / hour (as of 2025).

| | Conservative (12 min estimate) | Standard (10 min estimate) |
|---|---|---|
| Reward per participant | £1.80 | £1.50 |
| Prolific service fee (33%) | £0.60 | £0.50 |
| **Total cost per participant** | **£2.40** | **£2.00** |
| 50 participants | £120 | £100 |
| 100 participants | £240 | £200 |

**Recommendation:** Set reward at **£1.80**, estimated duration **12 minutes**. This is above minimum wage and gives a 33% buffer for slower participants.

Set the estimated completion time generously (12 min). Prolific flags studies as potentially under-paying if actual median completion time exceeds your estimate × 1.5.

---

## 3. Which actions and contexts from NormBank for the pilot? (5 actions × 20 contexts)

### Selected actions

Five actions chosen to span semantically distinct categories with high setting coverage and label diversity:

| Action | Category | # settings in NormBank | Entropy |
|---|---|---|---|
| `yell` | Body expression / volume | 115 | 1.52 |
| `kiss someone` | Physical contact / intimacy | 88 | 1.34 |
| `talk about money` | Conversation topic | 38 | 1.56 |
| `drink alcohol` | Consumption | 82 | 1.27 |
| `wear makeup` | Appearance / gender | 52 | 1.44 |

### Context selection per action

For each action, 20 settings were selected from NormBank using:
- **Minimum 5 annotator votes** for the (action, setting) pair
- **Stratified by majority norm** — roughly equal split across taboo-majority / neutral / expected-majority settings (ensuring survey rating diversity)
- **Sorted by label entropy** within each stratum (most informative settings first)

The 100 pilot scenarios are written to `data/normbank_pilot.csv`.

Script: `python -m cogemi.data.normbank_pilot` (re-runs selection from NormBank.csv).

### Distribution in the pilot dataset:

| Action | Taboo | Neutral | Expected |
|---|---|---|---|
| yell | 7 | 6 | 7 |
| kiss someone | 9 | 7 | 4 |
| talk about money | 8 | 6 | 6 |
| drink alcohol | 13 | 6 | 1 |
| wear makeup | 8 | 9 | 3 |
| **Total** | **45** | **34** | **21** |

Note: `drink alcohol` skews taboo (alcohol in most settings is mildly taboo to inappropriate). This is useful signal — it gives participants a spread even within one action.

### Example scenarios from the pilot:

| Action | Setting | Majority norm |
|---|---|---|
| yell | courthouse | expected (emergency) |
| yell | bakery | taboo (quiet commercial space) |
| yell | waterfall | neutral (noise drowns it) |
| kiss someone | art gallery | neutral |
| kiss someone | temple | taboo |
| kiss someone | armchair (at home) | expected |
| drink alcohol | auditorium | neutral |
| drink alcohol | child's room | taboo |
| wear makeup | banquet hall | neutral |
| wear makeup | army base | taboo |
