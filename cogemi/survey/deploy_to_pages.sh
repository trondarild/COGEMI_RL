#!/usr/bin/env bash
# Publish survey pages to the live site.
#
#   ./deploy_to_pages.sh [--dry-run] [--yes] [--only <file.html>]
#
# Copies the manifest below from this directory to the GitHub Pages repo at
# ~/code/trondarild.github.io/cavaa, commits, and pushes. That repo is the
# live site: anything pushed is public within a minute or so.
#
# This is the only sanctioned way to publish. Copying files by hand skips the
# checks below, and the failure they exist to catch — a survey going live with
# an unfilled completion code — is silent and expensive: participants finish
# the study and are redirected to an invalid Prolific submission URL.
#
# Checks, all fatal:
#   1. no *_CC_PLACEHOLDER left in any file being published
#   2. inline JS parses (node, if installed)
#   3. the structural test suite passes
#   4. you confirm the file list, unless --yes
#
# Options:
#   --dry-run       show what would change and stop
#   --yes           skip the confirmation prompt (for non-interactive use)
#   --only FILE     publish one file instead of the whole manifest

set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
REPO="$HOME/code/trondarild.github.io"
PAGES="$REPO/cavaa"
SITE="https://trondarild.github.io/cavaa"
PYTEST_TARGET="tests/test_role_router_survey.py tests/test_role_arm_surveys.py"

# ── Manifest ────────────────────────────────────────────────────────────────
# Explicit on purpose. This directory also holds credentials (pw.txt), scratch
# files and the Supabase schema, none of which belong on a public site.
#
# Current study first.
MANIFEST=(
  appropriateness_survey_aspects_park_prolific_v2_roles.html      # live: role router
  appropriateness_survey_aspects_park_prolific_v2.html            # v2 single-arm
  appropriateness_survey_aspects_park_prolific.html               # v1 park pilot
  appropriateness_survey_aspects_park_role_prolific.html          # role-perspectives pilot
  appropriateness_survey_aspects_ghpages.html
  appropriateness_survey_ghpages.html
  appropriateness_survey_local_test.html
  role_survey_ghpages.html
)

# Deployable only with --only. The three per-arm files were superseded by the
# router before their completion codes were ever set, so they still carry
# placeholders and would block every deploy if they sat in the manifest. Old
# copies remain on the live site, unreferenced by any Prolific study.
SUPERSEDED=(
  appropriateness_survey_aspects_park_prolific_v2_agent.html
  appropriateness_survey_aspects_park_prolific_v2_target.html
  appropriateness_survey_aspects_park_prolific_v2_observer.html
)

DRY_RUN=0
ASSUME_YES=0
ONLY=""

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --yes|-y)  ASSUME_YES=1; shift ;;
    --only)    ONLY="${2:-}"; [ -n "$ONLY" ] || { echo "--only needs a filename" >&2; exit 1; }; shift 2 ;;
    -h|--help) sed -n '2,26p' "$0"; exit 0 ;;
    *)         echo "unknown option: $1" >&2; exit 1 ;;
  esac
done

if [ -n "$ONLY" ]; then
  ONLY="$(basename "$ONLY")"
  found=0
  for f in "${MANIFEST[@]}" "${SUPERSEDED[@]}"; do [ "$f" = "$ONLY" ] && found=1; done
  if [ "$found" -eq 0 ]; then
    echo "refusing: '$ONLY' is not in the manifest — add it to deploy_to_pages.sh first" >&2
    exit 1
  fi
  FILES=("$ONLY")
else
  FILES=("${MANIFEST[@]}")
fi

[ -d "$PAGES" ] || { echo "pages repo not found at $PAGES" >&2; exit 1; }

# ── 1. placeholders ─────────────────────────────────────────────────────────
fail=0
for f in "${FILES[@]}"; do
  [ -f "$SRC/$f" ] || { echo "missing source file: $SRC/$f" >&2; fail=1; continue; }
  if grep -q "_CC_PLACEHOLDER" "$SRC/$f"; then
    echo "!! $f still contains a completion-code placeholder" >&2
    fail=1
  fi
done
if [ "$fail" -ne 0 ]; then
  echo >&2
  echo "Set the code first:  ./set_completion_code_roles.sh <CODE>" >&2
  exit 1
fi

# ── 2. inline JS parses ─────────────────────────────────────────────────────
if command -v node >/dev/null 2>&1; then
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  for f in "${FILES[@]}"; do
    awk '/^<script>/{p=1;next}/^<\/script>/{p=0}p' "$SRC/$f" > "$tmp/chk.js"
    if [ -s "$tmp/chk.js" ] && ! node --check "$tmp/chk.js" 2>"$tmp/err"; then
      echo "!! $f: inline JS does not parse" >&2
      cat "$tmp/err" >&2
      exit 1
    fi
  done
  echo "js      ok (${#FILES[@]} files)"
else
  echo "js      skipped (node not installed)"
fi

# ── 3. structural tests ─────────────────────────────────────────────────────
PY="$(cd "$SRC/../.." && pwd)/.venv/bin/python"
if [ -x "$PY" ]; then
  ( cd "$SRC/../.." && "$PY" -m pytest $PYTEST_TARGET -q >/dev/null ) \
    || { echo "!! structural tests failed — run them to see why:" >&2
         echo "   cd $(cd "$SRC/../.." && pwd) && .venv/bin/python -m pytest $PYTEST_TARGET -v" >&2
         exit 1; }
  echo "tests   ok"
else
  echo "tests   skipped (.venv not found)"
fi

# ── 4. what would change ────────────────────────────────────────────────────
echo
changed=()
for f in "${FILES[@]}"; do
  if [ ! -f "$PAGES/$f" ]; then
    echo "  new       $f"
    changed+=("$f")
  elif ! cmp -s "$SRC/$f" "$PAGES/$f"; then
    echo "  modified  $f"
    changed+=("$f")
  fi
done

if [ ${#changed[@]} -eq 0 ]; then
  echo "  nothing to publish — live site already matches"
  exit 0
fi

echo
echo "Target: $REPO (branch $(git -C "$REPO" branch --show-current)) -> $SITE"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "dry run — nothing copied"
  exit 0
fi

if [ "$ASSUME_YES" -eq 0 ]; then
  printf "Publish %d file(s) to the live site? [y/N] " "${#changed[@]}"
  read -r reply
  case "$reply" in [yY]*) ;; *) echo "aborted"; exit 1 ;; esac
fi

# ── 5. copy, commit, push ───────────────────────────────────────────────────
for f in "${changed[@]}"; do
  cp "$SRC/$f" "$PAGES/$f"
done

cd "$REPO"
git add -- $(printf 'cavaa/%s ' "${changed[@]}")

if git diff --cached --quiet; then
  echo "nothing staged — already committed?"
  exit 0
fi

if [ ${#changed[@]} -eq 1 ]; then
  msg="Deploy ${changed[0]}"
else
  msg="Deploy ${#changed[@]} survey pages"$'\n\n'"$(printf -- '- %s\n' "${changed[@]}")"
fi

git commit -q -m "$msg"
git push -q origin "$(git branch --show-current)"

echo
echo "pushed  $(git rev-parse --short HEAD)"
for f in "${changed[@]}"; do
  echo "  $SITE/$f"
done
echo
echo "Pages rebuilds in ~1 min. Check the study URL returns 200 before publishing on Prolific."
