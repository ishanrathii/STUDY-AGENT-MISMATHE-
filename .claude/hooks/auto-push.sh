#!/usr/bin/env bash
# Auto-commit & push hook for MISMATHE.
#
# Triggered on the Stop event (end of every Claude Code turn). If the working
# tree has changes, stages them, creates a commit, and pushes to the current
# branch. Exits 0 quickly when there's nothing to do so it never blocks turns.
set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

# Skip if not a git repo
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

# Skip if nothing changed
if git diff --quiet && git diff --cached --quiet && [ -z "$(git status --porcelain)" ]; then
  exit 0
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)"

# Stage everything except secrets (.gitignore already excludes .env)
git add -A

# Build a short commit message from the diff summary
SUMMARY="$(git diff --cached --shortstat 2>/dev/null | sed 's/^ *//')"
[ -z "$SUMMARY" ] && SUMMARY="updates"

git commit -m "chore: auto-sync — $SUMMARY" >/dev/null 2>&1 || exit 0

# Push with simple retry/backoff (network blips)
for delay in 0 2 4 8 16; do
  [ "$delay" -gt 0 ] && sleep "$delay"
  if git push -u origin "$BRANCH" >/dev/null 2>&1; then
    exit 0
  fi
done

# Push failed — leave the commit locally; surface a non-blocking note
echo "[auto-push] push failed after retries on branch $BRANCH" >&2
exit 0
