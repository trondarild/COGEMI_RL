#!/usr/bin/env bash
# Write the Prolific completion code into the single-study role-router survey.
#
#   ./set_completion_code_roles.sh <COMPLETION_CODE>
#
# Patches only. Publishing is a separate step — ./deploy_to_pages.sh — which
# refuses to push any file still carrying a placeholder.
#
# One study, one code — the three-arm script (set_completion_codes.sh) applies
# only to the superseded per-arm files.
#
# Idempotent on the placeholder only: once a real code is in place, re-running
# with a different code does nothing. Use git to revert if you need to redo it.

set -euo pipefail

if [ $# -ne 1 ]; then
  echo "usage: $0 <COMPLETION_CODE>" >&2
  exit 1
fi

CODE="$1"
SRC="$(cd "$(dirname "$0")" && pwd)"
FILE="$SRC/appropriateness_survey_aspects_park_prolific_v2_roles.html"

if ! grep -q "ROLES_CC_PLACEHOLDER" "$FILE"; then
  echo "!! no placeholder left in $FILE — nothing to do" >&2
  exit 1
fi

perl -pi -e "s/ROLES_CC_PLACEHOLDER/${CODE}/g" "$FILE"
echo "ok  roles -> $CODE"

echo
echo "Remaining placeholders (should be none):"
grep -l "ROLES_CC_PLACEHOLDER" "$FILE" || echo "  none"

echo
echo "Next:  ./deploy_to_pages.sh"
