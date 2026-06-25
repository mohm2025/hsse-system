#!/bin/bash
# Install Python dependencies so tests and the quiz engine run in
# Claude Code on the web sessions. Synchronous: the session waits until
# this completes, guaranteeing deps are ready before any tool runs.
set -euo pipefail

# Only needed in remote (web) sessions; local environments manage their own deps.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}"

echo "[session-start] Installing Python dependencies..."
python -m pip install -r requirements.txt
echo "[session-start] Done."
