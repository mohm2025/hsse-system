#!/bin/bash
# Install Python dependencies so tests, linting, and the quiz engine run in
# Claude Code on the web sessions. Async: the session starts immediately while
# this installs in the background (asyncTimeout caps it at 5 minutes).
set -euo pipefail

# Only needed in remote (web) sessions; local environments manage their own deps.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo '{"async": true, "asyncTimeout": 300000}'

cd "${CLAUDE_PROJECT_DIR:-.}"
echo "[session-start] Installing dependencies..."
python -m pip install -r requirements.txt -r requirements-dev.txt
echo "[session-start] Done."
