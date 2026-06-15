#!/usr/bin/env bash
# Session-start hook: ensure Python dependencies are installable + import OK.
set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

# Soft-install requirements if pip is available (don't fail the session).
if command -v pip >/dev/null 2>&1 && [ -f requirements.txt ]; then
  pip install --quiet --disable-pip-version-check -r requirements.txt >/dev/null 2>&1 || true
fi

exit 0
