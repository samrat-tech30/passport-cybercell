#!/usr/bin/env bash
# The one check that must pass before anything counts as done (and before every merge to main).
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== backend: lint"
(cd backend && .venv/bin/ruff check . && .venv/bin/ruff format --check .)
echo "== backend: tests"
(cd backend && .venv/bin/pytest -q)
echo "== backend: eval (shield ON must let 0 attacks through)"
(cd backend && .venv/bin/python -m app.eval_runner --no-save | tee /tmp/passport-eval.txt | tail -5)
grep -E "^\| Attacks that got through \| [0-9]+ / [0-9]+ \| 0 / [0-9]+ \|" /tmp/passport-eval.txt >/dev/null \
  || { echo "FAIL: an attack got through with the shield ON"; exit 1; }
echo "== frontend: typecheck + build"
(cd frontend && npm run --silent build)
echo "== guard hook over all source files"
for f in $(find backend/app frontend/src -type f \( -name '*.py' -o -name '*.ts' -o -name '*.tsx' -o -name '*.css' \)); do
  echo "{\"tool_input\":{\"file_path\":\"$f\"}}" | CLAUDE_PROJECT_DIR="$PWD" node .claude/hooks/guard.mjs
done
echo "ALL CHECKS PASSED"
