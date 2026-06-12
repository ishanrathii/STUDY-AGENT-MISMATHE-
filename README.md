# MISMATHE

**AI MHT-CET Study Mentor & Life Development Agent — Web Edition**

A Claude-powered AI mentor that lives in your browser. MISMATHE is not just
a study tool — it's a mentor, strategist, discipline coach, weak-area analyst,
and psychology-based life mentor for MHT-CET aspirants.

## Mission

> Help the student achieve 90%+ in MHT-CET while becoming disciplined,
> confident, emotionally strong, focused, and mentally powerful.

## Core Motto

> "Connect with the student first, then help the student improve."

---

## Features

- Chat-style web UI (single page, mobile-friendly, dark theme)
- Initial deep student analysis through guided onboarding
- Micro-weakness tracking (concepts, formulas, sub-topics — not just chapters)
- AI-generated daily / weekly schedules
- "One Thing Today" focus system
- Built-in study stopwatch with productivity analytics
- Daily check-ins (mood, energy, confidence, study hours)
- Chapter / weak-area / mock test generation (CET-level MCQs with answers + explanations)
- Spaced repetition revision queue
- 7 mentor mood modes: Strict, Calm, Motivation, Recovery, Challenge, Focus, Friend
- Performance dashboard — streak, hours, accuracy, weak areas
- 7-day emergency recovery plans
- Long-term memory — emotional patterns, breakthroughs, weak areas
- **Every chat saved to the GitHub repo** (see "Persistence" below)
- Daily auto-sync to GitHub at 23:45 + manual `Sync` button
- Brain teasers, motivational movie recs, personality development missions

## Tech Stack

- **Python 3.11+**, **FastAPI**, **uvicorn**
- **anthropic** SDK — Claude `claude-opus-4-8` with adaptive thinking
- **SQLAlchemy** (async) + **SQLite** for live state
- **APScheduler** for nightly memory sync + streak guard
- **Vanilla JS / HTML / CSS** — no frontend framework, no build step

## Project Structure

```
mismathe/
├── main.py                          # uvicorn entry point
├── config.py                        # env-driven settings
├── web/                             # Static frontend
│   ├── index.html
│   ├── style.css
│   └── app.js
├── mismathe/
│   ├── web/
│   │   ├── server.py                # FastAPI app + all routes
│   │   └── onboarding.py            # web onboarding flow
│   ├── core/
│   │   ├── agent.py                 # Claude integration
│   │   ├── prompts.py               # MISMATHE soul + onboarding script
│   │   ├── memory.py                # conversation + long-term memory
│   │   └── modes.py                 # 7 mentor modes
│   ├── db/
│   │   ├── database.py              # async SQLAlchemy engine
│   │   └── models.py                # Student, WeakArea, StudySession, etc.
│   ├── services/
│   │   ├── conversations.py         # writes every chat turn to memory/
│   │   ├── github_memory.py         # exports + git push of memory/
│   │   ├── scheduler.py             # nightly cron jobs
│   │   ├── stopwatch.py             # study session tracking
│   │   ├── weak_areas.py            # micro-weakness tracking
│   │   ├── revision.py              # SM-2 spaced repetition
│   │   ├── test_engine.py           # CET-style test generation
│   │   └── analytics.py             # dashboard rendering
│   ├── content/
│   │   ├── syllabus.py              # Class 11 PCM chapters + CET priorities
│   │   ├── motivation.py            # movie/book recommendations
│   │   └── puzzles.py               # brain teasers
│   └── utils/
└── memory/                          # version-controlled brain
    ├── student_<short_uid>.json     # one snapshot per browser
    └── conversations/<short_uid>/<YYYY-MM-DD>.jsonl
```

---

## Setup — running the website locally

### 1. Get a Claude API key

Go to [console.anthropic.com](https://console.anthropic.com) → API Keys → create
a key. You'll need this; the agent's brain runs on Claude.

### 2. Clone, configure, install

```bash
git clone https://github.com/ishanrathii/STUDY-AGENT-MISMATHE-.git
cd STUDY-AGENT-MISMATHE-
cp .env.example .env
# Edit .env — paste your ANTHROPIC_API_KEY and pick a SESSION_SECRET
pip install -r requirements.txt
```

### 3. Run

```bash
python main.py
```

Open **http://localhost:8000** in your browser. That's it.

The first time you load the page, MISMATHE introduces itself and walks you
through ~13 onboarding questions (name, current %, timings, weak/strong
subjects, fears, stress, focus, etc.). Once that's done, every chat message
becomes a normal conversation with your mentor.

### 4. (Optional) Run on a server for 24/7 availability

Any cheap VPS (Railway, Render, Fly.io, a small DigitalOcean droplet, even an
old laptop that stays on):

```bash
python main.py
```

For production, put it behind nginx + a real `SESSION_SECRET`, and run
under systemd or supervisord so it restarts on crash.

---

## Persistence — your chats are saved to GitHub

This is the whole point: MISMATHE's brain lives in this repo, not on a
single machine.

**Live state** sits in `data/mismathe.db` (SQLite — fast, local, gitignored).

**Durable record** is written in two places under `memory/`:

| File | Contents |
|---|---|
| `memory/student_<short_uid>.json` | Your profile, long-term memories, weak areas, recent check-ins, recent test history |
| `memory/conversations/<short_uid>/<YYYY-MM-DD>.jsonl` | Every chat turn — user message + AI reply — with timestamp |

Both are committed and pushed to GitHub:

- **Every night at 23:45** (timezone-aware, default `Asia/Kolkata`)
- **On demand** via the `📤 Sync memory to GitHub` button in the sidebar
- **The Stop hook** in `.claude/settings.json` also commits on code changes

The machine running the site needs git push access to this repo (HTTPS
token, SSH key, or `gh auth`).

When the bot starts on a **fresh machine** with an empty database but the
`memory/` snapshots present, it restores your profile, long-term memories,
and weak areas automatically — so MISMATHE never forgets you.

---

## Mentor modes

Switch with the buttons in the sidebar.

| Mode | When to use it |
|---|---|
| 🔥 Strict | High discipline, sharp accountability, no-excuses urgency |
| 🧘 Calm | Overwhelmed days — soft, grounding, stress-reducing |
| 🚀 Motivation | Confidence dip — vision-forward, identity-building |
| 🩹 Recovery | Fell off track — zero-guilt restart, tiny first step |
| 🎯 Challenge | Gamified missions, streaks, XP energy |
| 🎧 Focus | Deep work mode — minimal words, single task |
| 🤝 Friend | Default — casual Gen-Z best-friend energy |

---

## Privacy

- Identity is a signed cookie (`mismathe_uid`) holding a random UUID. No
  email, no password, no third-party tracker.
- Conversation files in `memory/conversations/` are pushed to **your** GitHub
  repo. If the repo is private, your data is private. If you make it public,
  your chats are public — keep that in mind.
- Set a long random `SESSION_SECRET` in `.env` so cookies can't be forged.

---

## Auto-push hooks

The repo has a Claude Code Stop hook that auto-commits and pushes any code
changes I make during a Claude Code session — see `.claude/settings.json`.
This is separate from the runtime memory sync above.

## Final Motto

> "MISMATHE does not just help the student crack MHT-CET. MISMATHE helps the
> student become the type of person capable of winning in academics and in
> life."
