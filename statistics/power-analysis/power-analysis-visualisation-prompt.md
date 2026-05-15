# Image-generation prompt — COGEMI v2 survey power analysis figure

## Prompt

Create a multi-panel scientific figure in the style of a Nature journal article.
White background. Sans-serif typeface (Helvetica or similar). Thin, precise axis
lines. Muted, distinct color palette: deep teal (#1b7a6e), amber (#e07b39),
slate blue (#3a5e9e), warm grey (#8a8a8a), with black for axes and labels.
Panel labels in bold uppercase (A, B, C, D) at top-left of each panel.
No decorative borders. Figure caption area below all panels in 8pt grey text.

The figure has four panels arranged in a 2×2 grid.

---

**Panel A — Survey design hierarchy (schematic, left column, top)**

A vertical layered diagram with three tiers, connected by downward arrows.

Tier 1 (top box, teal): "Vignette pool (120 total)"
  Subtitle: "12 structural cells: Setting × Relationship × Stakes (2×3×2)"
  Small 3×4 grid of squares inside the box, each square a faint teal, to
  suggest the 12 cells. Label one column header "Public / Private", one row
  header "Friend / Stranger / Authority", a small ×2 badge for Stakes.

Tier 2 (middle box, amber): "Participant session (42 vignettes)"
  Subtitle: "Random subset per participant — incomplete block design"
  Show a small row of 42 tiny rectangles, 5 highlighted in amber (retest
  items), the rest grey.
  Below the rectangles: "~21 ratings per vignette at N=60"

Tier 3 (bottom, two side-by-side sub-boxes in slate blue and warm grey):
  Left sub-box (slate blue): "Agent identity variants"
    "Gender × Role — text swap within vignette slot; no extra authoring"
  Right sub-box (warm grey): "Role perspective arms"
    "Agent / Target / Observer — separate Prolific conditions"
    "60 participants × 3 arms = 180 total"

Arrow from Tier 1 to Tier 2 labelled "random 42-item block".
Arrow from Tier 2 to Tier 3 labelled "between-participant assignment".

---

**Panel B — Power by vignettes per cell (line chart, right column, top)**

A line chart. X-axis: "Vignettes per structural cell (vpc)", ticks at 3, 5, 7,
10, 15, 20. Y-axis: "Power (1 - β)", 0 to 1.0, ticks at 0.2 intervals.
Horizontal dashed line at y = 0.80, labelled "80% threshold" in warm grey.

Four lines, each with distinct markers:
  - "Setting (d=0.40)" — teal, circle markers
  - "Rel: friend (d=0.50)" — amber, square markers
  - "Rel: authority (d=0.30)" — slate blue, triangle markers
  - "Stakes (d=0.30)" — warm grey, diamond markers

Data points (approximate from simulation):
  vpc=3:  Setting=0.47, Friend=0.45, Authority=0.26, Stakes=0.32
  vpc=5:  Setting=0.63, Friend=0.67, Authority=0.32, Stakes=0.42
  vpc=7:  Setting=0.78, Friend=0.80, Authority=0.45, Stakes=0.53
  vpc=10: Setting=0.92, Friend=0.89, Authority=0.57, Stakes=0.69
  vpc=15: Setting=0.99, Friend=0.98, Authority=0.74, Stakes=0.84
  vpc=20: Setting=1.00, Friend=0.99, Authority=0.85, Stakes=0.92

Vertical dashed line at vpc=10 in light teal, labelled "10 vpc / 120 vignettes
(main effects)". Vertical dashed line at vpc=20 in light amber, labelled
"20 vpc / 240 vignettes (full factorial)".

Legend inside the plot area, top-left, no box border.

---

**Panel C — Participant-level power (small bar chart, left column, bottom)**

Horizontal bar chart. Y-axis: three effects listed top to bottom:
  "Q1–Q2 norm divergence", "Test-retest reliability (r)", "Intra-item ICC"
X-axis: "Power / observed statistic", 0 to 1.0.

Bars (all teal, same shade as Panel A Tier 1):
  Q1–Q2 divergence: bar to 1.00, labelled "1.00 (N=20+)"
  Test-retest:      bar to 0.95, labelled "median r=0.95"
  Intra-item ICC:   bar to 0.68, labelled "observable ICC=0.68"

Vertical dashed line at x=0.80, labelled "target" in warm grey.
Vertical dashed line at x=0.65, labelled "adjusted ICC threshold" in slate blue,
with a small annotation "5-pt scale truncation".

Small note below x-axis: "Participant-level effects powered at N=20;
binding N is set by vignette-level and arm requirements."

---

**Panel D — Recommended sample size summary (annotated table, right column, bottom)**

A clean summary table, no cell borders except thin lines under the header row
and above the total row. Column headers in small caps: "Criterion", "N", "Source".

Rows:
  Dirichlet pattern classification  |  50  |  Dirichlet simulation
  Q1–Q2 norm divergence             |  20  |  lmerTest simulation
  Agent identity (gender/role)      |  60  |  lmerTest sensitivity
  Vignette pool (10 vpc, main)      | 120 vignettes  |  vpc sweep
  Vignette pool (20 vpc, full)      | 240 vignettes  |  vpc sweep
  Role arms (agent/target/observer) |  ×3  |  between-participant design
  ─────────────────────────────────
  Recommended (single arm)          |  60  |  binding
  Recommended (three arms)          | 180  |  binding × 3

Highlight the two "Recommended" rows with a faint teal background.
Bold the numbers 60 and 180 in those rows.

Below the table, a single-sentence caption in 8pt warm grey:
"N=60 per arm is agent-identity binding; contextual claims require expanding
the vignette pool, not recruiting more participants."

---

## Style notes for the generator

- Render as a flat vector-style illustration, not a photograph.
- All text must be legible at A4 print size (approx. 170mm wide).
- Use thin (0.5pt equivalent) axis lines and grid lines; avoid heavy gridlines.
- Data lines in Panel B should be smooth curves through the data points, not
  straight line segments.
- Maintain consistent visual weight across all four panels.
- No drop shadows, gradients, or 3D effects.
- The overall impression should be: precise, publication-ready, information-dense
  but uncluttered — matching the aesthetic of Nature Methods or Nature Human
  Behaviour supplementary figures.
