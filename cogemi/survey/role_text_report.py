#!/usr/bin/env python3
"""Extract every word the three arms show a participant, into one page.

    python3 cogemi/survey/role_text_report.py > data/role-text-report.md

The framing text lives in the survey HTML, not in Supabase — the database
records which arm a participant was in, not what they read. This reads the
router and prints what differs between arms and what does not, so the three
can be checked against each other without clicking through 47 items in a
browser three times.
"""
import html
import pathlib
import re
import sys

ROUTER = pathlib.Path(__file__).with_name(
    "appropriateness_survey_aspects_park_prolific_v2_roles.html")

ROLES = ["agent", "target", "observer"]


def text(s):
    """Strip tags and decode entities — these strings are written as HTML."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def role_text(src):
    block = src[src.index("var ROLE_TEXT = {"):src.index("\n};", src.index("var ROLE_TEXT"))]
    out = {}
    for role in ROLES:
        seg = block[block.index(f"  {role}: {{"):]
        out[role] = {
            # label is double-quoted, the rest single — accept either
            key: text(re.search(rf"{key}:\s*(['\"])(.*?)\1\s*,?\n", seg, re.S).group(2))
            for key in ("label", "intro", "q1", "q2")
        }
    return out


def shared_questions(src):
    """Questions fixed in the markup, identical in every arm."""
    labels = {
        "q3-phase":           "Q3 empirical",
        "confidence-phase":   "Confidence",
        "disagreement-phase": "Perceived disagreement",
    }
    out = {}
    for div, name in labels.items():
        seg = src[src.index(f'<div id="{div}"'):]
        out[name] = text(re.search(r'<p class="question">(.*?)</p>', seg, re.S).group(1))
    out["Aspect ranking"] = text(
        re.search(r'<p class="aspect-prompt">(.*?)</p>', src, re.S).group(1))
    return out


def scenarios(src):
    pool = re.findall(r'\{ id:"([^"]+)",\s*\n\s*en:"([^"]+)"', src)
    anchors = {
        m.group(1): (m.group(2), m.group(3) == "true")
        for m in re.finditer(
            r'(\w+):\s*\{ who:"([^"]+)",\s*directed:(true|false)',
            src[src.index("var TARGET_ANCHORS = {"):])
    }
    return [(sid, html.unescape(en)) + anchors.get(sid, ("— MISSING —", None))
            for sid, en in pool]


def main():
    src = ROUTER.read_text(encoding="utf-8")
    rt, shared, items = role_text(src), shared_questions(src), scenarios(src)
    w = sys.stdout.write

    w("# Role text — what each arm shows\n\n")
    w(f"Generated from `{ROUTER.name}`. Regenerate with "
      "`python3 cogemi/survey/role_text_report.py > data/role-text-report.md`.\n\n")
    w("Everything below the first section is identical in all three arms, "
      "except the target anchor, which only the target arm sees.\n\n")

    w("## Differs between arms\n\n")
    for key, name in [("label", "Phase label"), ("intro", "Consent intro"),
                      ("q1", "Q1 personal"), ("q2", "Q2 injunctive")]:
        w(f"### {name}\n\n")
        for role in ROLES:
            w(f"- **{role}** — {rt[role][key]}\n")
        w("\n")

    w("## Identical in all arms\n\n")
    for name, q in shared.items():
        w(f"- **{name}** — {q}\n")
    w("\n")

    directed = sum(1 for *_, d in items if d)
    w(f"## Target anchors ({len(items)} items, {directed} directed, "
      f"{len(items) - directed} incidental)\n\n")
    w("Shown under the vignette in the target arm only. `directed` means the "
      "action is aimed at that person; incidental means it merely lands on "
      "them.\n\n")
    w("| scenario | vignette | in this situation you are | directed |\n")
    w("|---|---|---|:--:|\n")
    for sid, en, who, d in items:
        flag = "•" if d else ""
        w(f"| `{sid}` | {en} | {who} | {flag} |\n")


if __name__ == "__main__":
    main()
