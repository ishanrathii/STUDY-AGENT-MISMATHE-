# MISMATHE memory snapshots

This folder holds the agent's long-term memory, exported from the live
database — one `student_<telegram_id>.json` per student.

- **Written by:** the nightly memory sync (23:45) and the `/sync` command.
- **Read by:** `restore_if_empty()` on startup — if the local database is
  empty (fresh machine / fresh clone), the profile, long-term memories, and
  weak areas are rebuilt from these files.

Do not hand-edit while the bot is running; your edits may be overwritten by
the next sync.
