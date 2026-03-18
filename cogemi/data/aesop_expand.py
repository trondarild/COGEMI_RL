# cogemi/data/aesop_expand.py
"""
Expand Aesop fable morals into concrete action-context scenarios via LLM.

For each fable, the LLM generates 2-3 real-world scenarios that instantiate
the moral lesson, formatted as NormBank-style action-context pairs with an
expected ternary rating (wrong / neutral / right).

Usage
-----
    python -m cogemi.data.aesop_expand \\
        --aesop   data/aesop_children_19994.txt \\
        --out     data/aesop_action_contexts.csv \\
        [--model  qwen3:14b]   # defaults to cogemi_config.yaml

The script skips rows that already exist in the output file, so it is safe
to interrupt and resume.
"""

from __future__ import annotations

import argparse
import csv
import re
import time
from pathlib import Path
from typing import List, Optional

from cogemi.data.aesop import load_aesop
from cogemi.features.extractor_llm import LLMFeatureExtractor
from cogemi.observe.scenario import Scenario

# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_EXPAND_PROMPT = """\
You are given an Aesop fable and its one-sentence moral.  Your task is to \
generate {n} concrete, real-world scenarios that illustrate the moral lesson.

Each scenario must describe a specific person performing a specific action in \
a specific social situation.  The scenario should feel relatable and plausible \
for a modern-day human survey participant.

Format each scenario EXACTLY as shown (one block per scenario, blank line \
between blocks):

ACTION: <what the person does, ≤ 15 words>
CONTEXT: <the situation or circumstances, ≤ 15 words>
RATING: <wrong | neutral | right>

Rules:
- RATING must be exactly one of: wrong, neutral, right
- RATING should reflect whether the action aligns with the moral:
    * actions that violate the moral → wrong
    * actions that embody the moral → right
    * genuinely ambiguous actions → neutral
- Generate at least one "wrong" and at least one "right" scenario per fable.
- Do NOT include the fable characters (Wolf, Fox, etc.) — use real-world \
  human roles (student, employee, parent, friend, etc.).
- Do NOT reproduce the moral text verbatim in the action or context.

Fable: {title}
Moral: {moral}
Story (for context only): {story}

Generate {n} scenarios:"""

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

# Match ACTION/CONTEXT/RATING blocks in any whitespace layout (multi-line or single-line).
# Each field ends lazily at the next field keyword.
_BLOCK_RE = re.compile(
    r"ACTION\s*:\s*(.+?)\s*CONTEXT\s*:\s*(.+?)\s*RATING\s*:\s*(wrong|neutral|right)",
    re.IGNORECASE | re.DOTALL,
)


def _parse_scenarios(raw: str) -> List[dict]:
    """Parse LLM output into a list of {action, context, rating} dicts."""
    # Strip <think>...</think> blocks (chain-of-thought models)
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    results = []
    for m in _BLOCK_RE.finditer(raw):
        action = " ".join(m.group(1).strip().splitlines()).strip().rstrip(".")
        context = " ".join(m.group(2).strip().splitlines()).strip().rstrip(".")
        rating = m.group(3).strip().lower()
        if action and context and rating in ("wrong", "neutral", "right"):
            results.append({"action": action, "context": context, "rating": rating})
    return results


# ---------------------------------------------------------------------------
# Main expansion logic
# ---------------------------------------------------------------------------

CSV_FIELDS = ["id", "fable_id", "fable_title", "fable_moral", "action", "context", "rating"]


def expand_aesop_scenarios(
    aesop_path: str | Path,
    out_path: str | Path,
    n_per_fable: int = 3,
    model: Optional[str] = None,
    config_path: Optional[str] = None,
    delay_s: float = 0.5,
) -> int:
    """Generate action-context scenarios for each Aesop fable and save to CSV.

    Parameters
    ----------
    aesop_path:
        Path to the Gutenberg plain-text Aesop file.
    out_path:
        Output CSV path.
    n_per_fable:
        Number of scenarios to generate per fable (default 3).
    model:
        Override LLM model name. None → use cogemi_config.yaml.
    config_path:
        Override path to cogemi_config.yaml.
    delay_s:
        Seconds to sleep between LLM calls (rate-limiting).

    Returns
    -------
    Total number of scenario rows written.
    """
    scenarios = load_aesop(aesop_path)
    extractor = LLMFeatureExtractor(model=model, config_path=config_path)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing rows to support resuming interrupted runs
    existing_ids: set = set()
    if out_path.exists():
        with open(out_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                existing_ids.add(row["id"])

    write_header = not out_path.exists() or out_path.stat().st_size == 0

    total_written = 0
    with open(out_path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, quoting=csv.QUOTE_ALL)
        if write_header:
            writer.writeheader()

        for sc in scenarios:
            # Check if all scenarios for this fable are already present
            first_id = f"{sc.id}_0"
            if first_id in existing_ids:
                print(f"  skip {sc.id} (already in output)")
                continue

            moral = sc.anchors["moral"]
            story = sc.anchors["story"][:600]  # truncate long stories
            prompt = _EXPAND_PROMPT.format(
                title=sc.representation,
                moral=moral,
                story=story,
                n=n_per_fable,
            )

            if extractor.model == "stub":
                raw_scenarios = [
                    {"action": "a person does the right thing", "context": "in a social situation", "rating": "right"},
                    {"action": "a person does the wrong thing", "context": "in a social situation", "rating": "wrong"},
                ]
            else:
                raw_scenarios = []
                for attempt in range(3):
                    try:
                        raw = extractor._call(prompt)
                        raw_scenarios = _parse_scenarios(raw)
                        if raw_scenarios:
                            break
                        print(f"  WARNING: no scenarios parsed for {sc.id} (attempt {attempt+1}), raw:\n{raw[:200]}")
                    except Exception as e:
                        print(f"  ERROR calling LLM for {sc.id} (attempt {attempt+1}): {e}")
                        time.sleep(5)
                if not raw_scenarios:
                    print(f"  SKIP {sc.id} after 3 failed attempts")
                    continue
                if delay_s > 0:
                    time.sleep(delay_s)

            for i, s in enumerate(raw_scenarios):
                row_id = f"{sc.id}_{i}"
                if row_id in existing_ids:
                    continue
                writer.writerow({
                    "id": row_id,
                    "fable_id": sc.id,
                    "fable_title": sc.representation,
                    "fable_moral": moral,
                    "action": s["action"],
                    "context": s["context"],
                    "rating": s["rating"],
                })
                total_written += 1

            fh.flush()
            print(f"  {sc.id}: {sc.representation!r} → {len(raw_scenarios)} scenarios")

    return total_written


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main() -> None:
    parser = argparse.ArgumentParser(
        description="Expand Aesop fable morals into NormBank-style action-context scenarios."
    )
    parser.add_argument("--aesop",  default="data/aesop_children_19994.txt",
                        help="Path to Gutenberg Aesop plain-text file")
    parser.add_argument("--out",    default="data/aesop_action_contexts.csv",
                        help="Output CSV path")
    parser.add_argument("--model",  default=None,
                        help="Override LLM model (e.g. qwen3:14b)")
    parser.add_argument("--n",      type=int, default=3,
                        help="Scenarios per fable (default 3)")
    parser.add_argument("--delay",  type=float, default=0.5,
                        help="Seconds between LLM calls (default 0.5)")
    args = parser.parse_args()

    n = expand_aesop_scenarios(
        aesop_path=args.aesop,
        out_path=args.out,
        n_per_fable=args.n,
        model=args.model,
        delay_s=args.delay,
    )
    print(f"\nDone. {n} scenarios written to {args.out}")


if __name__ == "__main__":
    _main()
