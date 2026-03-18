# cogemi/data/aesop.py
"""
Aesop's Fables loader for COGEMI.

Parses the plain-text Project Gutenberg edition of "The Aesop for Children"
(Gutenberg ID 19994) and extracts fables as COGEMI Scenarios.

Each fable becomes one ``Scenario`` with:
  - ``id``: ``aesop_{index}`` (zero-padded to 3 digits, e.g. ``aesop_001``)
  - ``representation``: the fable title (title-cased)
  - ``anchors``:
      ``action``  — one-sentence description of the protagonist's key action,
                    derived from the moral (stripped of imperative framing)
      ``moral``   — the verbatim moral text from the book
      ``story``   — the full fable story text (cleaned)

Also provides ``extract_scenarios_to_csv()`` to write the parsed data to a CSV
file suitable for review and manual annotation.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import List, Optional, Tuple

from cogemi.observe.scenario import Scenario

# ---------------------------------------------------------------------------
# Internal parsing helpers
# ---------------------------------------------------------------------------

# A fable title is an all-caps line (allowing Æ and other characters)
# surrounded by blank lines.  We match lines that are entirely uppercase
# (possibly with spaces, hyphens, commas, ampersands, and 'Æ').
_TITLE_RE = re.compile(r"^[A-ZÆ][A-ZÆ ,\-'&]+$")

# Moral lines are wrapped in underscores: _text_
# A moral may span multiple lines.
_MORAL_START_RE = re.compile(r"^_(.+)")
_MORAL_END_RE = re.compile(r"(.+)_$")

# Illustration captions / TOC entries to skip
_SKIP_RE = re.compile(r"^\[Illustration|^A LIST OF THE FABLES|^THE ÆSOP FOR CHILDREN")

_GUTENBERG_START = "*** START OF THE PROJECT GUTENBERG EBOOK"
_GUTENBERG_END = "*** END OF THE PROJECT GUTENBERG EBOOK"


def _parse_fables(text: str) -> List[dict]:
    """Parse raw Gutenberg plain text and return a list of fable dicts.

    Each dict has keys: ``title``, ``story``, ``moral``.
    """
    # Strip Gutenberg boilerplate
    start = text.find(_GUTENBERG_START)
    end = text.find(_GUTENBERG_END)
    if start != -1:
        text = text[start:]
    if end != -1:
        text = text[:end]

    lines = text.splitlines()

    fables: List[dict] = []
    current_title: Optional[str] = None
    story_lines: List[str] = []
    moral_lines: List[str] = []
    in_moral = False
    prev_blank = True  # track whether previous line was blank

    # Skip the table of contents (lines before first real fable text)
    # We detect the TOC end by finding "THE WOLF AND THE KID" (first fable)
    in_toc = True

    for i, raw_line in enumerate(lines):
        line = raw_line.rstrip()

        # Skip Gutenberg header / illustration markers
        if _SKIP_RE.match(line):
            continue

        # Detect start of content (first fable title)
        if in_toc:
            if _TITLE_RE.match(line) and len(line) >= 6 and "ÆSOP" not in line:
                in_toc = False
                current_title = line.title()
                prev_blank = False
            continue

        is_blank = line.strip() == ""

        # --- Moral handling ---
        if in_moral:
            chunk = line.strip("_").strip()
            if chunk:
                moral_lines.append(chunk)
            if line.rstrip().endswith("_"):
                in_moral = False
            prev_blank = is_blank
            continue

        if line.startswith("_") and not line.startswith("["):
            # Skip inline emphasis: _word_ followed by more text on the same line
            # e.g. "_agreed_ to let a judge decide..." — not a moral
            if re.match(r"^_\w+_\s+\S", line):
                if current_title and not is_blank:
                    story_lines.append(line.strip())
                prev_blank = is_blank
                continue
            moral_text = line.strip("_").strip()
            if line.endswith("_"):
                # single-line moral: _text_
                in_moral = False
                moral_lines = [moral_text]
            else:
                # multi-line moral starts here, continues until a line ending with _
                in_moral = True
                moral_lines = [moral_text]
            prev_blank = False
            continue

        # --- Title detection ---
        # All-caps line preceded by a blank line
        if prev_blank and _TITLE_RE.match(line) and len(line) >= 4 and "ÆSOP" not in line:
            # Save the previous fable
            if current_title and moral_lines:
                fables.append({
                    "title": current_title,
                    "story": " ".join(
                        l for l in story_lines if l.strip() and not l.startswith("[")
                    ).strip(),
                    "moral": " ".join(moral_lines).strip(),
                })
            current_title = line.title()
            story_lines = []
            moral_lines = []
            prev_blank = False
            continue

        # --- Story body ---
        if current_title and not is_blank and not line.startswith("["):
            story_lines.append(line.strip())

        prev_blank = is_blank

    # Save last fable
    if current_title and moral_lines:
        fables.append({
            "title": current_title,
            "story": " ".join(
                l for l in story_lines if l.strip() and not l.startswith("[")
            ).strip(),
            "moral": " ".join(moral_lines).strip(),
        })

    # Filter out spurious entries (copyright notices, very short morals)
    fables = [
        f for f in fables
        if len(f["moral"]) >= 20
        and not f["moral"].lower().startswith("copyright")
        and len(f["story"]) >= 100
    ]

    return fables


def _moral_to_action(moral: str) -> str:
    """Derive an action description from the fable moral.

    The moral sentence itself (minus trailing period) is used directly as the
    action anchor.  The LLM feature extractor will handle structured extraction
    later.
    """
    return moral.rstrip(".")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_aesop(
    path: str | Path,
    max_fables: Optional[int] = None,
) -> List[Scenario]:
    """Parse Aesop fables and return a list of COGEMI ``Scenario`` objects.

    Parameters
    ----------
    path:
        Path to the Gutenberg plain-text file (e.g. ``data/aesop_children_19994.txt``).
    max_fables:
        If given, return only the first ``max_fables`` fables.

    Returns
    -------
    List of ``Scenario`` objects, one per fable.
    """
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    fables = _parse_fables(text)
    if max_fables is not None:
        fables = fables[:max_fables]

    scenarios: List[Scenario] = []
    for idx, fable in enumerate(fables):
        scenario_id = f"aesop_{idx:03d}"
        action = _moral_to_action(fable["moral"])
        scenarios.append(
            Scenario(
                id=scenario_id,
                representation=fable["title"],
                anchors={
                    "action": action,
                    "moral": fable["moral"],
                    "story": fable["story"],
                },
                origin={"source": "aesop_children_19994", "fable_index": idx},
            )
        )
    return scenarios


def extract_scenarios_to_csv(
    path: str | Path,
    out_path: str | Path,
    max_fables: Optional[int] = None,
) -> int:
    """Parse Aesop fables and write them to a CSV file.

    CSV columns: ``id``, ``title``, ``action``, ``moral``, ``story``

    Returns the number of rows written.
    """
    scenarios = load_aesop(path, max_fables=max_fables)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["id", "title", "action", "moral", "story"],
            quoting=csv.QUOTE_ALL,
        )
        writer.writeheader()
        for sc in scenarios:
            writer.writerow({
                "id": sc.id,
                "title": sc.representation,
                "action": sc.anchors["action"],
                "moral": sc.anchors["moral"],
                "story": sc.anchors["story"],
            })

    return len(scenarios)
