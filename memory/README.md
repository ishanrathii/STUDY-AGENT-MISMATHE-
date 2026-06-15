# MISMATHE memory — the agent's brain in your repo

This folder is what makes MISMATHE remember you across machines and
restarts. Two kinds of files live here.

## `student_<short_uid>.json`

One snapshot per browser session (the UID comes from a signed cookie
created on first visit). Contains:

- Profile — name, current %, timings, sleep, learning style, fears,
  confidence/stress/focus levels, streak, mentor mode
- Long-term memories — emotional patterns, breakthroughs, milestones
- Weak areas — subject, chapter, sub-topic, severity, weakness type
- Recent check-ins (last 30) and tests (last 20) for reference

Written by `mismathe.services.github_memory.export_all()`, triggered:

- nightly at 23:45 by the scheduler
- on demand via the `📤 Sync memory to GitHub` button in the sidebar
- on the `/api/sync` endpoint

On startup, if the live SQLite database is empty but these snapshots exist
(fresh clone on a new machine), `restore_if_empty()` rebuilds the profile,
long-term memories, and weak areas from these files.

## `conversations/<short_uid>/<YYYY-MM-DD>.jsonl`

A complete, append-only log of every chat turn — user message *and*
assistant reply — with timestamps and metadata (onboarding phase,
command phase, etc.). One file per student per day.

This is the durable, human-readable, version-controlled record of every
conversation. The SQLite database can be wiped and the agent will still
know who you are because of these files.

---

**Do not hand-edit while the app is running.** Your edits may be
overwritten by the next sync. Edit the live database instead, or stop
the app first.
