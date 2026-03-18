# cogemi/data/export_cogemi_csv.py
"""
Export COGEMI scenario datasets to standardised CSV files.

Produces:
  data/cogemi_normbank.csv          — NormBank social-appropriateness scenarios
  data/cogemi_scruples_justice.csv  — SCRUPLES justice-filtered scenarios
  data/aesop_scenarios.csv          — Aesop fable scenarios (already written by
                                      aesop.extract_scenarios_to_csv; re-exported
                                      here for format consistency)

Common CSV schema
-----------------
id              COGEMI scenario ID
representation  Text shown to survey participants
action          Action anchor (what the agent does)
context         Context anchor (setting / situation)
agent_role      Role of the actor (if available)
target_role     Role of the affected person (if available)
source          Dataset name
n_responses     Total annotator votes
majority_norm   Most common response label
pct_majority    Fraction of votes for majority_norm

Usage
-----
    python -m cogemi.data.export_cogemi_csv
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import List

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_OUT_DIR = Path("data")
_FIELDS = [
    "id", "representation", "action", "context",
    "agent_role", "target_role",
    "source", "n_responses", "majority_norm", "pct_majority",
]


def _write_csv(path: Path, rows: List[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_FIELDS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# NormBank
# ---------------------------------------------------------------------------

def export_normbank(normbank_csv: Path, out_path: Path) -> int:
    from cogemi.data.normbank import load_normbank

    print("Loading NormBank …")
    scenarios, responses = load_normbank(normbank_csv)

    # Build response lookup: scenario_id → list of norm strings
    resp_by_scenario: dict = {}
    for r in responses:
        resp_by_scenario.setdefault(r.scenario_id, []).append(r.response)

    rows = []
    for sc in scenarios:
        resp = resp_by_scenario.get(sc.id, [])
        if not resp:
            continue
        counter = Counter(resp)
        majority, majority_count = counter.most_common(1)[0]
        rows.append({
            "id":             sc.id,
            "representation": sc.representation,
            "action":         sc.anchors.get("action", ""),
            "context":        sc.anchors.get("setting", ""),
            "agent_role":     "",
            "target_role":    "",
            "source":         "normbank",
            "n_responses":    len(resp),
            "majority_norm":  majority,
            "pct_majority":   round(majority_count / len(resp), 3),
        })

    _write_csv(out_path, rows)
    print(f"  → {len(rows)} scenarios written to {out_path}")
    return len(rows)


# ---------------------------------------------------------------------------
# SCRUPLES justice
# ---------------------------------------------------------------------------

def export_scruples_justice(scruples_jsonl: Path, out_path: Path) -> int:
    from cogemi.data.scruples import load_justice_subset, _clean_title

    print("Loading SCRUPLES justice subset …")
    scenarios, responses = load_justice_subset(scruples_jsonl)

    resp_by_scenario: dict = {}
    for r in responses:
        resp_by_scenario.setdefault(r.scenario_id, []).append(r.response)

    rows = []
    for sc in scenarios:
        resp = resp_by_scenario.get(sc.id, [])
        if not resp:
            continue
        counter = Counter(resp)
        majority, majority_count = counter.most_common(1)[0]
        rows.append({
            "id":             sc.id,
            "representation": _clean_title(sc.representation),
            "action":         sc.anchors.get("action", ""),
            "context":        "",
            "agent_role":     (sc.roles or {}).get("agent", ""),
            "target_role":    (sc.roles or {}).get("target", ""),
            "source":         "scruples_justice",
            "n_responses":    len(resp),
            "majority_norm":  majority,
            "pct_majority":   round(majority_count / len(resp), 3),
        })

    _write_csv(out_path, rows)
    print(f"  → {len(rows)} scenarios written to {out_path}")
    return len(rows)


# ---------------------------------------------------------------------------
# Aesop (re-export in common schema)
# ---------------------------------------------------------------------------

def export_aesop(aesop_txt: Path, out_path: Path) -> int:
    from cogemi.data.aesop import load_aesop

    print("Loading Aesop fables …")
    scenarios = load_aesop(aesop_txt)

    rows = []
    for sc in scenarios:
        rows.append({
            "id":             sc.id,
            "representation": sc.representation,
            "action":         sc.anchors.get("moral", ""),
            "context":        "",
            "agent_role":     "",
            "target_role":    "",
            "source":         "aesop_children_19994",
            "n_responses":    0,
            "majority_norm":  "",
            "pct_majority":   "",
        })

    _write_csv(out_path, rows)
    print(f"  → {len(rows)} scenarios written to {out_path}")
    return len(rows)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Export COGEMI scenario CSVs.")
    parser.add_argument("--normbank",  default="data/NormBank.csv")
    parser.add_argument("--scruples",  default="data/anecdotes/train.scruples-anecdotes.jsonl")
    parser.add_argument("--aesop",     default="data/aesop_children_19994.txt")
    parser.add_argument("--out-dir",   default="data")
    args = parser.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    export_normbank(Path(args.normbank),  out / "cogemi_normbank.csv")
    export_scruples_justice(Path(args.scruples), out / "cogemi_scruples_justice.csv")
    export_aesop(Path(args.aesop),        out / "cogemi_aesop.csv")

    print("\nDone.")


if __name__ == "__main__":
    main()
