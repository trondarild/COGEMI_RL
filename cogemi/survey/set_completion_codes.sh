#!/usr/bin/env bash
# Write the three Prolific completion codes into the v2 role-arm surveys.
#
#   ./set_completion_codes.sh <AGENT_CC> <TARGET_CC> <OBSERVER_CC>
#
# SUPERSEDED. The three-arm design was replaced by the single-study role
# router; use set_completion_code_roles.sh. Kept in case the arms are ever
# run separately.
#
# Patches only. Publishing is a separate step — ./deploy_to_pages.sh.
#
# Idempotent on the placeholders only: once a real code is in place, re-running
# with a different code does nothing. Use git to revert if you need to redo it.

set -euo pipefail

if [ $# -ne 3 ]; then
  echo "usage: $0 <AGENT_CC> <TARGET_CC> <OBSERVER_CC>" >&2
  exit 1
fi

SRC="$(cd "$(dirname "$0")" && pwd)"

set_arm() {
  local role="$1" code="$2"
  local upper file
  upper=$(printf '%s' "$role" | tr '[:lower:]' '[:upper:]')
  file="$SRC/appropriateness_survey_aspects_park_prolific_v2_${role}.html"

  if ! grep -q "${upper}_CC_PLACEHOLDER" "$file"; then
    echo "!! $role: no placeholder left in $file — skipping" >&2
    return
  fi

  perl -pi -e "s/${upper}_CC_PLACEHOLDER/${code}/g" "$file"
  echo "ok  $role -> $code"
}

set_arm agent    "$1"
set_arm target   "$2"
set_arm observer "$3"

echo
echo "Remaining placeholders (should be none):"
grep -l "_CC_PLACEHOLDER" "$SRC"/appropriateness_survey_aspects_park_prolific_v2_*.html || echo "  none"

echo
echo "Next:  ./deploy_to_pages.sh"
