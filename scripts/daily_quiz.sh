#!/bin/bash
#
# Generate the day's quiz automatically (intended for cron).
#
# Setup:
#   1. Put your API key in a .env file at the repo root (git-ignored):
#        echo 'ANTHROPIC_API_KEY=sk-...' > .env
#   2. Make this script executable:  chmod +x scripts/daily_quiz.sh
#   3. Add a crontab entry (runs 7am daily; cron has a minimal env, so use
#      absolute paths and log the output):
#
#        0 7 * * *  /ABSOLUTE/PATH/TO/hsse-system/scripts/daily_quiz.sh >> /ABSOLUTE/PATH/TO/hsse-system/quizzes/cron.log 2>&1
#
# Override the exam or question count via env vars:
#   QUIZ_EXAM=CSP QUIZ_N=15 scripts/daily_quiz.sh
#
set -euo pipefail

# Resolve repo root from this script's location, regardless of cwd (cron runs from $HOME).
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

# Load ANTHROPIC_API_KEY (and any other vars) from .env — cron does not inherit your shell env.
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# Activate a local virtualenv if one exists.
if [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "$(date -Is) ERROR: ANTHROPIC_API_KEY not set (create a .env or export it)." >&2
  exit 1
fi

echo "$(date -Is) Generating ${QUIZ_EXAM:-ASP} quiz (${QUIZ_N:-10} questions)..."
python quiz_engine.py --exam "${QUIZ_EXAM:-ASP}" -n "${QUIZ_N:-10}" >/dev/null
echo "$(date -Is) Done -> quizzes/quiz_$(date +%F).json"
