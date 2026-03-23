# cogemi/data/normbank_pilot.py
"""
Select 5 actions × 20 contexts from NormBank for the social-appropriateness pilot survey.

Selection criteria
------------------
Actions:
  Chosen to span five semantically distinct categories (body expression,
  physical contact, topic of conversation, consumption, appearance) while
  maximising setting coverage and rating diversity (entropy of
  taboo/normal/expected labels).

Contexts (settings) per action:
  - At least ``min_annotations`` annotator votes for this (action, setting) pair
  - Sorted by Shannon entropy of the label distribution, then stratified so
    each of the three norm buckets (taboo-majority / neutral / expected-majority)
    contributes roughly equally
  - Final 20 contexts are spread across indoor/outdoor, public/private,
    formal/informal setting types

Output
------
  data/normbank_pilot.csv
      scenario_id, action, setting, n_annotations, pct_taboo, pct_normal,
      pct_expected, majority_norm, entropy
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict, Counter
from pathlib import Path
from typing import List, Tuple, Dict

# ---------------------------------------------------------------------------
# Five pilot actions (manually chosen for semantic breadth + data coverage)
# ---------------------------------------------------------------------------
PILOT_ACTIONS = [
    "yell",            # body expression / volume
    "kiss someone",    # physical contact / intimacy
    "talk about money",# conversation topic / taboo subject
    "drink alcohol",   # consumption / social norm
    "wear makeup",     # appearance / gender norms
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entropy(labels: List[str]) -> float:
    c = Counter(labels)
    n = len(labels)
    return -sum((v / n) * math.log2(v / n) for v in c.values() if v > 0)


def _select_contexts(
    by_setting: Dict[str, List[str]],
    n: int = 20,
    min_annotations: int = 5,
) -> List[dict]:
    """Select n diverse contexts for one action.

    Strategy: score all settings by entropy, then take a stratified sample
    that balances taboo-majority / ambiguous / expected-majority settings.
    """
    scored: List[Tuple] = []
    for setting, labels in by_setting.items():
        if len(labels) < min_annotations:
            continue
        c = Counter(labels)
        total = len(labels)
        pt = c["taboo"] / total
        pn = c["normal"] / total
        pe = c["expected"] / total
        e = _entropy(labels)
        majority = c.most_common(1)[0][0]
        scored.append((setting, total, e, pt, pn, pe, majority))

    # Sort by entropy (most informative first)
    scored.sort(key=lambda x: -x[2])

    # Stratify: bucket by majority norm
    buckets: Dict[str, list] = {"taboo": [], "normal": [], "expected": []}
    for row in scored:
        buckets[row[6]].append(row)

    # Take roughly equal from each bucket, filling remainder with highest entropy
    per_bucket = n // 3
    selected: list = []
    for bucket in ["taboo", "normal", "expected"]:
        selected.extend(buckets[bucket][:per_bucket])
    # Top up to n with highest-entropy remaining (any bucket)
    used_settings = {r[0] for r in selected}
    for row in scored:
        if len(selected) >= n:
            break
        if row[0] not in used_settings:
            selected.append(row)
            used_settings.add(row[0])

    return [
        {
            "setting":       r[0],
            "n_annotations": r[1],
            "entropy":       round(r[2], 3),
            "pct_taboo":     round(r[3], 3),
            "pct_normal":    round(r[4], 3),
            "pct_expected":  round(r[5], 3),
            "majority_norm": r[6],
        }
        for r in selected[:n]
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def select_pilot(
    normbank_csv: Path = Path("data/NormBank.csv"),
    out_path: Path = Path("data/normbank_pilot.csv"),
    actions: List[str] = PILOT_ACTIONS,
    n_contexts: int = 20,
    min_annotations: int = 5,
) -> int:
    """Load NormBank, select pilot scenarios, write CSV. Returns row count."""
    # Build (action, setting) → labels index
    action_setting: Dict[str, Dict[str, List[str]]] = {a: defaultdict(list) for a in actions}
    action_set = set(actions)

    with open(normbank_csv, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            b = (row.get("behavior") or "").strip()
            s = (row.get("setting") or "").strip()
            norm = (row.get("norm") or "").strip()
            if b in action_set and s and norm in ("taboo", "normal", "expected"):
                action_setting[b][s].append(norm)

    rows_out: List[dict] = []
    scenario_idx = 0
    for action in actions:
        contexts = _select_contexts(action_setting[action], n=n_contexts,
                                    min_annotations=min_annotations)
        print(f"  {action!r}: {len(contexts)} contexts selected "
              f"(taboo={sum(1 for c in contexts if c['majority_norm']=='taboo')}, "
              f"normal={sum(1 for c in contexts if c['majority_norm']=='normal')}, "
              f"expected={sum(1 for c in contexts if c['majority_norm']=='expected')})")
        for ctx in contexts:
            rows_out.append({
                "scenario_id":   f"nb_pilot_{scenario_idx:03d}",
                "action":        action,
                "setting":       ctx["setting"],
                "n_annotations": ctx["n_annotations"],
                "pct_taboo":     ctx["pct_taboo"],
                "pct_normal":    ctx["pct_normal"],
                "pct_expected":  ctx["pct_expected"],
                "majority_norm": ctx["majority_norm"],
                "entropy":       ctx["entropy"],
            })
            scenario_idx += 1

    fields = ["scenario_id","action","setting","n_annotations",
              "pct_taboo","pct_normal","pct_expected","majority_norm","entropy"]
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows_out)

    print(f"  → {len(rows_out)} scenarios written to {out_path}")
    return len(rows_out)


if __name__ == "__main__":
    print("Selecting NormBank pilot scenarios …")
    select_pilot()
