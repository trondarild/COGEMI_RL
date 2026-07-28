#!/usr/bin/env python3
"""Pilot analysis for the v2 role-router study (30 participants, 10 per arm).

    .venv/bin/python statistics/pilot-analysis/pilot_analysis.py

Reads data/pilot-v2-roles/responses_clean.csv, writes figures to
statistics/pilot-analysis/figures/ and prints every number the report quotes.

Unit of analysis is the participant, not the row. Each person contributes 40
scenarios, so row-level intervals would treat 400 correlated observations as
400 independent ones and come out roughly six times too narrow. Everything
below aggregates within participant first, then across the ten per arm.

Demographics come from the Prolific export, which is gitignored: it carries
Prolific IDs. Only aggregate counts reach the figures, and participants are
joined by the same md5 prefix the survey export uses.
"""
import collections
import csv
import hashlib
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

ROOT    = pathlib.Path(__file__).resolve().parents[2]
DATA    = ROOT / "data" / "pilot-v2-roles" / "responses_clean.csv"
DEMOG   = next((ROOT / "data").glob("prolific_demographic_export_*.csv"), None)
FIGURES = pathlib.Path(__file__).resolve().parent / "figures"

ARMS   = ["agent", "target", "observer"]
CHECKS = ("sa_check_appropriate", "sa_check_inappropriate")

# Categorical slots 1-3 of the reference palette. Validated all-pairs, light
# and dark. Aqua sits under 3:1 on the light surface, so every series carries a
# visible direct label rather than relying on the swatch alone.
COLOR   = {"agent": "#2a78d6", "target": "#eb6834", "observer": "#1baf7a"}
INK     = "#0b0b0b"
INK2    = "#52514e"
MUTED   = "#8a8a85"
SURFACE = "#fcfcfb"
GRID    = "#e6e6e2"
# Diverging pair for the 1-5 appropriateness scale: two poles, neutral middle.
DIVERGING = ["#c2453f", "#e08b86", "#d9d9d4", "#7fb8a4", "#1baf7a"]


def setup():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE, "font.size": 9,
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "text.color": INK, "axes.labelcolor": INK2, "axes.edgecolor": GRID,
        "xtick.color": INK2, "ytick.color": INK2,
        "xtick.labelsize": 8, "ytick.labelsize": 8,
        "axes.titlesize": 10, "axes.labelsize": 8.5,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
        "axes.axisbelow": True, "figure.dpi": 160, "savefig.dpi": 160,
        "savefig.bbox": "tight", "legend.frameon": False, "legend.fontsize": 8,
    })


def bare(ax, keep=("left", "bottom")):
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(side in keep)
    ax.tick_params(length=0)


def save(fig, name):
    path = FIGURES / name
    fig.savefig(path)
    plt.close(fig)
    print(f"  wrote {path.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load():
    rows = []
    for r in csv.DictReader(DATA.open()):
        for k in ("response_value", "confidence", "viewport_w",
                  "perceived_disagreement"):
            r[k] = int(r[k]) if r[k] not in ("", None) else None
        r["is_repeat"] = r["is_repeat"] == "True"
        r["directed"] = {"True": True, "False": False}.get(r["target_directed"])
        rows.append(r)
    return rows


def demographics():
    """Participant-level attributes keyed by the survey's md5 prefix."""
    if DEMOG is None:
        return {}
    out = {}
    for r in csv.DictReader(DEMOG.open()):
        if r["Status"] != "APPROVED":
            continue
        out[hashlib.md5(r["Participant id"].encode()).hexdigest()[:8]] = {
            "age": int(r["Age"]) if r["Age"].isdigit() else None,
            "sex": r["Sex"], "language": r["Language"],
            "country": r["Country of residence"],
            "minutes": float(r["Time taken"]) / 60 if r["Time taken"] else None,
        }
    return out


def participant_means(rows, norm_type="personal", directed=None):
    """One number per participant: their mean over the 40 main scenarios."""
    acc = collections.defaultdict(list)
    for r in rows:
        if r["norm_type"] != norm_type or r["is_repeat"]:
            continue
        if r["scenario_id"] in CHECKS or r["scenario_id"].startswith("__"):
            continue
        if directed is not None and r["directed"] is not directed:
            continue
        acc[(r["role"], r["pid8"])].append(r["response_value"])
    return {k: float(np.mean(v)) for k, v in acc.items()}


def by_arm(pm):
    return {a: np.array([v for (role, _), v in pm.items() if role == a])
            for a in ARMS}


def ci95(x):
    x = np.asarray(x, float)
    if len(x) < 2:
        return float(np.mean(x)), 0.0
    return float(np.mean(x)), float(stats.sem(x) * stats.t.ppf(0.975, len(x) - 1))


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def fig_arm_means(rows):
    """Headline comparison. Dots with CI, not bars: these are means, and a bar
    implies a count anchored at zero."""
    fig, ax = plt.subplots(figsize=(5.6, 2.5))
    stats_by_arm = {}
    for i, arm in enumerate(ARMS):
        v = by_arm(participant_means(rows))[arm]
        m, h = ci95(v)
        stats_by_arm[arm] = (m, h, v)
        y = len(ARMS) - 1 - i
        ax.plot(v, [y] * len(v), "o", ms=5, color=COLOR[arm], alpha=0.28,
                markeredgewidth=0, zorder=2)
        ax.plot([m - h, m + h], [y, y], "-", lw=2, color=COLOR[arm], zorder=3)
        ax.plot([m], [y], "o", ms=9, color=COLOR[arm], zorder=4,
                markeredgecolor=SURFACE, markeredgewidth=2)
        ax.text(m, y + 0.30, f"{arm}  {m:.2f}", ha="center", va="bottom",
                fontsize=8.5, color=INK, fontweight="bold")
    ax.set_yticks([])
    ax.set_ylim(-0.6, len(ARMS) - 0.15)
    ax.set_xlabel("mean personal appropriateness  (1 = strongly inappropriate, 5 = strongly appropriate)")
    ax.set_title("Arm means with 95% CI — each faint dot is one participant",
                 loc="left", color=INK)
    ax.grid(axis="y", visible=False)
    bare(ax, keep=("bottom",))
    save(fig, "01-arm-means.png")
    return stats_by_arm


def fig_directedness(rows):
    """The comparison the target anchors were built for, split by whether the
    action is aimed at that person."""
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 2.6), sharex=True)
    out = {}
    for ax, (d, label) in zip(axes, [(True, "directed — 17 scenarios"),
                                     (False, "incidental — 23 scenarios")]):
        pm = by_arm(participant_means(rows, directed=d))
        for i, arm in enumerate(ARMS):
            m, h = ci95(pm[arm])
            out[(d, arm)] = (m, h)
            y = len(ARMS) - 1 - i
            ax.plot(pm[arm], [y] * len(pm[arm]), "o", ms=4, color=COLOR[arm],
                    alpha=0.25, markeredgewidth=0)
            ax.plot([m - h, m + h], [y, y], "-", lw=2, color=COLOR[arm])
            ax.plot([m], [y], "o", ms=8, color=COLOR[arm],
                    markeredgecolor=SURFACE, markeredgewidth=2)
            ax.text(m, y + 0.28, f"{arm} {m:.2f}", ha="center", va="bottom",
                    fontsize=7.8, color=INK)
        ax.set_yticks([])
        ax.set_ylim(-0.6, len(ARMS) - 0.1)
        ax.set_title(label, loc="left", color=INK2, fontsize=9)
        ax.grid(axis="y", visible=False)
        bare(ax, keep=("bottom",))
    axes[0].set_xlabel("mean personal appropriateness")
    axes[1].set_xlabel("mean personal appropriateness")
    fig.suptitle("Target vs observer, split by whether anyone is addressed",
                 x=0.005, y=1.10, ha="left", fontsize=10, color=INK)
    save(fig, "02-directedness.png")
    return out


def fig_scenarios(rows):
    """Item variation against arm variation, on one axis."""
    acc = collections.defaultdict(list)
    for r in rows:
        if (r["norm_type"] != "personal" or r["is_repeat"]
                or r["scenario_id"] in CHECKS or r["scenario_id"].startswith("__")):
            continue
        acc[(r["scenario_id"], r["role"])].append(r["response_value"])
    scen = sorted({s for s, _ in acc},
                  key=lambda s: np.mean([v for (ss, _), vs in acc.items()
                                         if ss == s for v in vs]))
    fig, ax = plt.subplots(figsize=(7.0, 8.4))
    for i, s in enumerate(scen):
        vals = [np.mean(acc[(s, a)]) for a in ARMS]
        ax.plot([min(vals), max(vals)], [i, i], "-", lw=1, color=GRID, zorder=1)
        for a in ARMS:
            ax.plot(np.mean(acc[(s, a)]), i, "o", ms=5.5, color=COLOR[a],
                    markeredgecolor=SURFACE, markeredgewidth=1.2, zorder=3)
    ax.set_yticks(range(len(scen)))
    ax.set_yticklabels([s.replace("_park_", " · ") for s in scen], fontsize=7)
    ax.set_ylim(-1, len(scen))
    ax.set_xlabel("mean personal appropriateness")
    ax.set_title("Scenario means by arm — sorted by overall appropriateness",
                 loc="left", color=INK)
    handles = [plt.Line2D([], [], marker="o", ls="", ms=6, color=COLOR[a],
                          label=a) for a in ARMS]
    ax.legend(handles=handles, loc="lower right", ncol=1)
    ax.grid(axis="y", visible=False)
    bare(ax, keep=("bottom", "left"))
    save(fig, "03-scenario-means.png")
    return scen, acc


def fig_personal_vs_injunctive(rows):
    """Do people think others share their judgement?"""
    per = collections.defaultdict(list)
    inj = collections.defaultdict(list)
    for r in rows:
        if r["is_repeat"] or r["scenario_id"] in CHECKS or r["scenario_id"].startswith("__"):
            continue
        if r["norm_type"] == "personal":
            per[(r["scenario_id"], r["role"])].append(r["response_value"])
        elif r["norm_type"] == "injunctive":
            inj[(r["scenario_id"], r["role"])].append(r["response_value"])
    fig, ax = plt.subplots(figsize=(4.6, 4.4))
    ax.plot([1, 5], [1, 5], "-", lw=1, color=MUTED, zorder=1)
    ax.text(4.85, 4.6, "agree", fontsize=7.5, color=MUTED, ha="right")
    xs, ys = [], []
    for a in ARMS:
        x = [np.mean(per[k]) for k in per if k[1] == a]
        y = [np.mean(inj[k]) for k in inj if k[1] == a]
        xs += x; ys += y
        ax.plot(x, y, "o", ms=5, color=COLOR[a], alpha=0.75, markeredgewidth=0,
                label=a, zorder=3)
    r_pi = stats.pearsonr(xs, ys)
    ax.set_xlabel("personal judgement (Q1)")
    ax.set_ylabel("what most people would think (Q2)")
    ax.set_title(f"Personal vs injunctive, per scenario × arm\nr = {r_pi[0]:.2f}",
                 loc="left", color=INK)
    ax.legend(loc="upper left")
    bare(ax)
    save(fig, "04-personal-vs-injunctive.png")
    return r_pi, float(np.mean(ys) - np.mean(xs))


def fig_response_distribution(rows):
    """Diverging: the scale has a neutral midpoint and two poles."""
    fig, ax = plt.subplots(figsize=(6.4, 2.3))
    labels = ["strongly\ninappropriate", "inappropriate", "neutral",
              "appropriate", "strongly\nappropriate"]
    for i, arm in enumerate(ARMS):
        vals = [r["response_value"] for r in rows
                if r["role"] == arm and r["norm_type"] == "personal"
                and not r["is_repeat"] and r["scenario_id"] not in CHECKS
                and not r["scenario_id"].startswith("__")]
        c = collections.Counter(vals)
        total = sum(c.values())
        left = 0
        y = len(ARMS) - 1 - i
        for v in range(1, 6):
            w = 100 * c[v] / total
            ax.barh(y, w - 0.35, left=left, height=0.62,
                    color=DIVERGING[v - 1], edgecolor="none")
            if w > 7:
                ax.text(left + w / 2, y, f"{w:.0f}", ha="center", va="center",
                        fontsize=7.5,
                        color="#ffffff" if v in (1, 5) else INK)
            left += w
        ax.text(-1.5, y, arm, ha="right", va="center", fontsize=8.5, color=INK)
    ax.set_yticks([]); ax.set_xlim(0, 100); ax.set_ylim(-0.6, 2.6)
    ax.set_xlabel("percent of responses")
    ax.set_title("Distribution of personal judgements", loc="left", color=INK)
    handles = [plt.Rectangle((0, 0), 1, 1, color=DIVERGING[i]) for i in range(5)]
    ax.legend(handles, labels, ncol=5, loc="upper center",
              bbox_to_anchor=(0.5, -0.30), fontsize=7, handlelength=1.2,
              columnspacing=1.4, handletextpad=0.5)
    ax.grid(axis="y", visible=False)
    bare(ax, keep=("bottom",))
    save(fig, "05-response-distribution.png")


def fig_retest(rows):
    pairs = []
    first = collections.defaultdict(dict)
    again = collections.defaultdict(dict)
    for r in rows:
        if r["norm_type"] != "personal":
            continue
        (again if r["is_repeat"] else first)[r["pid8"]][r["scenario_id"]] = r
    for pid in again:
        for s, r2 in again[pid].items():
            r1 = first[pid].get(s)
            if r1:
                pairs.append((r1["response_value"], r2["response_value"],
                              r1["role"]))
    rng = np.random.default_rng(0)
    fig, ax = plt.subplots(figsize=(4.4, 4.2))
    ax.plot([0.6, 5.4], [0.6, 5.4], "-", lw=1, color=MUTED, zorder=1)
    for a in ARMS:
        x = [p[0] for p in pairs if p[2] == a]
        y = [p[1] for p in pairs if p[2] == a]
        ax.plot(np.array(x) + rng.normal(0, .07, len(x)),
                np.array(y) + rng.normal(0, .07, len(y)),
                "o", ms=5, color=COLOR[a], alpha=0.6, markeredgewidth=0,
                label=a, zorder=3)
    r_rt = stats.pearsonr([p[0] for p in pairs], [p[1] for p in pairs])
    exact = sum(1 for p in pairs if p[0] == p[1]) / len(pairs)
    within1 = sum(1 for p in pairs if abs(p[0] - p[1]) <= 1) / len(pairs)
    ax.set_xticks(range(1, 6)); ax.set_yticks(range(1, 6))
    ax.set_xlabel("first presentation"); ax.set_ylabel("repeat presentation")
    ax.set_title(f"Test–retest, 5 scenarios × 30 people\n"
                 f"r = {r_rt[0]:.2f} · {exact:.0%} identical · {within1:.0%} within 1",
                 loc="left", color=INK)
    ax.legend(loc="upper left")
    bare(ax)
    save(fig, "06-test-retest.png")
    return r_rt, exact, within1


def fig_duration(rows, demo):
    inside = {}
    import datetime
    for r in rows:
        t = datetime.datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
        lo, hi = inside.get(r["pid8"], (t, t))
        inside[r["pid8"]] = (min(lo, t), max(hi, t))
    surveyed = np.array([(hi - lo).total_seconds() / 60 for lo, hi in inside.values()])
    prolific = np.array([d["minutes"] for d in demo.values() if d["minutes"]]) \
        if demo else np.array([])

    fig, ax = plt.subplots(figsize=(6.2, 2.6))
    bins = np.arange(10, 52, 3)
    ax.hist(surveyed, bins=bins, color=COLOR["agent"], alpha=0.85,
            edgecolor=SURFACE, linewidth=1.5, label="first to last response")
    if len(prolific):
        ax.hist(prolific, bins=bins, histtype="step", lw=2,
                color=COLOR["target"], label="Prolific, incl. consent")
    ax.axvline(22, color=INK, lw=1.4, ls=(0, (4, 3)))
    ax.text(22.4, ax.get_ylim()[1] * 0.92, "22 min advertised", fontsize=7.5,
            color=INK)
    ax.set_xlabel("minutes"); ax.set_ylabel("participants")
    ax.set_title("How long it actually took", loc="left", color=INK)
    ax.legend(loc="upper right")
    ax.grid(axis="x", visible=False)
    bare(ax)
    save(fig, "07-duration.png")
    return surveyed, prolific


def fig_confidence(rows):
    """Are people more certain at the ends of the scale than in the middle?"""
    acc = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        if (r["norm_type"] != "personal" or r["confidence"] is None
                or r["is_repeat"] or r["scenario_id"] in CHECKS):
            continue
        acc[r["role"]][r["response_value"]].append(r["confidence"])
    fig, ax = plt.subplots(figsize=(5.0, 2.8))
    for a in ARMS:
        xs = sorted(acc[a])
        ys = [np.mean(acc[a][v]) for v in xs]
        ax.plot(xs, ys, "-o", lw=2, ms=7, color=COLOR[a],
                markeredgecolor=SURFACE, markeredgewidth=1.5, label=a)
        ax.text(xs[-1] + 0.08, ys[-1], a, fontsize=8, color=COLOR[a],
                va="center")
    ax.set_xticks(range(1, 6))
    ax.set_xlim(0.7, 5.9)
    ax.set_xlabel("personal judgement")
    ax.set_ylabel("mean confidence (1–5)")
    ax.set_title("Confidence against judgement", loc="left", color=INK)
    bare(ax)
    save(fig, "08-confidence.png")
    return {a: {v: float(np.mean(acc[a][v])) for v in sorted(acc[a])} for a in ARMS}


def fig_aspects(rows):
    """Which aspect did people rank first?"""
    firsts = collections.Counter()
    for r in rows:
        if r["norm_type"] != "personal" or not r["aspect_ranking"]:
            continue
        if r["scenario_id"] in CHECKS or r["scenario_id"].startswith("__"):
            continue
        firsts[r["aspect_ranking"].split("|")[0]] += 1
    top = firsts.most_common(14)
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ys = range(len(top))[::-1]
    ax.barh(list(ys), [c for _, c in top], height=0.66,
            color=COLOR["agent"], edgecolor="none")
    for y, (lab, c) in zip(ys, top):
        ax.text(c + 3, y, str(c), va="center", fontsize=7.5, color=INK2)
    ax.set_yticks(list(ys))
    ax.set_yticklabels([lab for lab, _ in top], fontsize=8)
    ax.set_xlabel("times ranked most important")
    ax.set_title("Most-cited aspect, top 14 of "
                 f"{len(firsts)} distinct", loc="left", color=INK)
    ax.grid(axis="y", visible=False)
    bare(ax, keep=("bottom", "left"))
    save(fig, "09-aspects.png")
    return firsts


def fig_language(rows, demo):
    """The covariate imbalance that limits what the arm comparison can say."""
    if not demo:
        return {}
    arm_of = {r["pid8"]: r["role"] for r in rows}
    counts = {a: [0, 0] for a in ARMS}          # [English L1, other]
    for pid, d in demo.items():
        a = arm_of.get(pid)
        if a:
            counts[a][0 if d["language"] == "English" else 1] += 1
    fig, ax = plt.subplots(figsize=(5.2, 2.2))
    for i, a in enumerate(ARMS):
        y = len(ARMS) - 1 - i
        eng, oth = counts[a]
        ax.barh(y, eng - 0.06, height=0.6, color=COLOR[a], edgecolor="none")
        ax.barh(y, oth - 0.06, left=eng + 0.06, height=0.6, color=GRID,
                edgecolor="none")
        ax.text(eng / 2 if eng else 0.1, y, str(eng), ha="center", va="center",
                fontsize=8, color="#ffffff" if eng > 1 else INK)
        ax.text(-0.25, y, a, ha="right", va="center", fontsize=8.5, color=INK)
    ax.set_yticks([]); ax.set_xlim(0, 10); ax.set_ylim(-0.6, 2.6)
    ax.set_xlabel("participants  (coloured = English first language)")
    ax.set_title("First language did not balance across arms", loc="left",
                 color=INK)
    ax.grid(axis="y", visible=False)
    bare(ax, keep=("bottom",))
    save(fig, "10-language.png")
    return counts


# ---------------------------------------------------------------------------

def main():
    setup()
    FIGURES.mkdir(exist_ok=True)
    rows = load()
    demo = demographics()
    print(f"{len(rows)} rows, {len({r['pid8'] for r in rows})} participants, "
          f"demographics for {len(demo)}")

    arm = fig_arm_means(rows)
    dr  = fig_directedness(rows)
    fig_scenarios(rows)
    r_pi, gap = fig_personal_vs_injunctive(rows)
    fig_response_distribution(rows)
    r_rt, exact, within1 = fig_retest(rows)
    surveyed, prolific = fig_duration(rows, demo)
    conf = fig_confidence(rows)
    firsts = fig_aspects(rows)
    lang = fig_language(rows, demo)

    print("\n--- arm means (participant-level, 95% CI) ---")
    for a in ARMS:
        m, h, v = arm[a]
        print(f"  {a:9} {m:.3f} ± {h:.3f}   sd {np.std(v, ddof=1):.3f}")
    f = stats.f_oneway(*[arm[a][2] for a in ARMS])
    print(f"  one-way ANOVA  F = {f.statistic:.2f}  p = {f.pvalue:.3f}")
    t_to = stats.ttest_ind(arm["target"][2], arm["observer"][2])
    print(f"  target vs observer  t = {t_to.statistic:.2f}  p = {t_to.pvalue:.3f}")
    t_ao = stats.ttest_ind(arm["agent"][2],
                           np.concatenate([arm["target"][2], arm["observer"][2]]))
    print(f"  agent vs rest       t = {t_ao.statistic:.2f}  p = {t_ao.pvalue:.3f}")
    pooled = np.concatenate([arm[a][2] for a in ARMS])
    d = (np.mean(arm["agent"][2]) -
         np.mean(np.concatenate([arm["target"][2], arm["observer"][2]]))) / np.std(pooled, ddof=1)
    print(f"  agent vs rest  Cohen d = {d:.2f}")

    print("\n--- directedness ---")
    for dd, label in ((True, "directed"), (False, "incidental")):
        print(f"  {label}: " + "  ".join(
            f"{a} {dr[(dd, a)][0]:.2f}±{dr[(dd, a)][1]:.2f}" for a in ARMS))

    print(f"\n--- other ---")
    print(f"  personal vs injunctive  r = {r_pi[0]:.3f}  p = {r_pi[1]:.2g}  "
          f"mean shift {gap:+.3f}")
    print(f"  test-retest r = {r_rt[0]:.3f}  identical {exact:.1%}  within 1 {within1:.1%}")
    print(f"  duration in-survey median {np.median(surveyed):.1f} "
          f"({surveyed.min():.1f}-{surveyed.max():.1f})")
    if len(prolific):
        print(f"  duration Prolific  median {np.median(prolific):.1f} "
              f"({prolific.min():.1f}-{prolific.max():.1f})")
    print(f"  confidence by judgement: " +
          "; ".join(f"{a} " + ",".join(f"{conf[a][v]:.2f}" for v in sorted(conf[a]))
                    for a in ARMS))
    print(f"  distinct first-ranked aspects: {len(firsts)}")
    if lang:
        print("  English L1 by arm: " +
              "  ".join(f"{a} {lang[a][0]}/10" for a in ARMS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
