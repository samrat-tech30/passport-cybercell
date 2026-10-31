#!/usr/bin/env bash
# The MCP server + pipeline are FROZEN for the demo (decided by Samrat, 2026-10-31; prompts/J2-judge-review.md).
# `bash scripts/frozen.sh`         -> fails if any tracked file under the frozen paths changed
# `bash scripts/frozen.sh update`  -> re-record the hashes (only on purpose, with a line in docs/DECISIONS.md)
set -euo pipefail
cd "$(dirname "$0")/.."

PATHS=(
  integrations/gmail_mcp
  integrations/passport_gateway
  integrations/nimbus_mcp
  integrations/claude_desktop_setup.py
  integrations/demo_agent/gmail_attacks.py
  backend/app/gate
  backend/app/tools
  backend/app/api/gateway_routes.py
  backend/app/api/schemas.py
  backend/app/sessions.py
  backend/app/config.py
)
MANIFEST=scripts/frozen.sha256

hash_all() {
  local sum="sha256sum"
  command -v sha256sum >/dev/null 2>&1 || sum="shasum -a 256"
  git ls-files -- "${PATHS[@]}" | LC_ALL=C sort | while read -r f; do $sum "$f"; done
}

if [ "${1:-check}" = "update" ]; then
  hash_all > "$MANIFEST"
  echo "frozen: recorded $(wc -l < "$MANIFEST" | tr -d ' ') files in $MANIFEST"
  exit 0
fi

now=$(mktemp "${TMPDIR:-/tmp}/passport-frozen.XXXXXX")  # BSD mktemp needs a template (docs/LESSONS.md)
trap 'rm -f "$now"' EXIT
hash_all > "$now"
if ! diff -q "$MANIFEST" "$now" > /dev/null; then
  echo "FAIL: the frozen MCP server / pipeline changed (prompts/J2-judge-review.md: don't touch these):"
  diff "$MANIFEST" "$now" | grep '^[<>]' | awk '{print "  " $1 " " $3}' | sort -u -k2
  echo "If this change is really wanted: bash scripts/frozen.sh update, and add a line to docs/DECISIONS.md."
  exit 1
fi
echo "frozen: $(wc -l < "$MANIFEST" | tr -d ' ') pipeline files unchanged"
