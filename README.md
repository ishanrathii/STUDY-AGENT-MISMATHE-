# MISMATHE

**AI MHT-CET Study Mentor & Life Development Agent**

A Telegram-deployed AI mentor powered by Claude (Anthropic). MISMATHE is not just
a study assistant — it is a mentor, strategist, discipline coach, study planner,
weak-area analyst, performance tracker, productivity coach, and psychology-based
mentor for MHT-CET aspirants.

## Mission

> Help the student achieve 90%+ in MHT-CET while also becoming disciplined,
> confident, emotionally strong, focused, and mentally powerful.

## Core Motto

> "Connect with the student first, then help the student improve."

---

## Features

- Initial deep student analysis (academic + psychological)
- Micro-weakness identification (concepts, formulas, sub-topics)
- Adaptive daily / weekly / monthly schedules
- "One Thing Today" focus system
- Built-in study stopwatch with productivity analytics
- Energy management and peak-focus detection
- Daily check-ins with mood/stress/confidence tracking
- Chapter, topic, weak-area, CET-level mock test generation
- Performance analysis with rank prediction
- Spaced repetition revision system
- 7 mentor mood modes: Strict, Calm, Motivation, Recovery, Challenge, Focus, Friend
- Digital dopamine control coaching
- Identity transformation reinforcement
- Long-term memory (emotional patterns, breakthroughs, weak areas)
- Performance dashboard (accuracy, productivity, weakness heatmaps, streaks)
- Emergency recovery (7-day backlog plans)
- Exam temperament training
- News, motivational movies, puzzles, personality development
- Post-CET college / branch guidance

## Tech Stack

- **Python 3.11+**
- **python-telegram-bot** (v21+, async)
- **anthropic** SDK — Claude `claude-opus-4-8` with adaptive thinking
- **SQLAlchemy** + **SQLite** for persistence
- **APScheduler** for reminders and daily nudges
- **python-dotenv** for config

## Project Structure

```
mismathe/
├── main.py                    # Entry point
├── config.py                  # Settings (env vars)
├── mismathe/
│   ├── bot.py                 # Telegram bot wiring
│   ├── core/
│   │   ├── agent.py           # Claude-powered AI agent
│   │   ├── prompts.py         # System prompts (mentor modes, onboarding)
│   │   ├── memory.py          # Long-term conversation memory
│   │   └── modes.py           # 7 mentor mood modes
│   ├── handlers/              # Telegram command + message handlers
│   ├── db/                    # SQLAlchemy models + session
│   ├── services/              # Stopwatch, scheduler, weak-areas, tests, analytics
│   ├── content/               # Syllabus, motivation library, puzzles
│   └── utils/
└── data/                      # SQLite DB (gitignored)
```

## Setup — connecting the bot to YOUR Telegram

### Step 1 — create your bot (2 minutes, inside Telegram)

1. Open Telegram and search for **@BotFather** (the official bot, blue check).
2. Send `/newbot`.
3. Give it a display name — e.g. `MISMATHE`.
4. Give it a username ending in `bot` — e.g. `mismathe_mentor_bot`.
5. BotFather replies with a **token** like `7012345678:AAH9x...`. Copy it.

That token is what binds this code to *your* bot. Anyone who messages
`@mismathe_mentor_bot` reaches this program.

### Step 2 — get a Claude API key

1. Go to [console.anthropic.com](https://console.anthropic.com) → API Keys.
2. Create a key and copy it.

### Step 3 — run the bot

On the machine that will run the bot (your laptop or a server):

```bash
git clone https://github.com/ishanrathii/STUDY-AGENT-MISMATHE-.git
cd STUDY-AGENT-MISMATHE-
cp .env.example .env
# edit .env: paste TELEGRAM_BOT_TOKEN and ANTHROPIC_API_KEY
pip install -r requirements.txt
python main.py
```

### Step 4 — start chatting

Open Telegram → search your bot's username → press **Start**.
Onboarding begins immediately. That's it — you're connected.

### Step 5 (recommended) — lock the bot to you

Send `/myid` to the bot. It replies with your numeric Telegram id.
Put it in `.env`:

```
ALLOWED_USER_IDS=123456789
```

Restart the bot. Now nobody else can use your mentor, even if they find it.

> **Note:** the bot only replies while `python main.py` is running. For 24/7
> availability run it on an always-on machine (a cheap VPS, Railway, Render,
> Raspberry Pi, or an old laptop that stays on).

## GitHub memory sync

MISMATHE's working memory lives in SQLite (`data/mismathe.db`), but its
long-term brain is **backed up into this repo**:

- Every night at 23:45 (and on `/sync`), each student's profile, long-term
  memories, weak areas, recent check-ins, and test history are exported to
  `memory/student_<telegram_id>.json`, committed, and pushed.
- On startup, if the database is empty but `memory/` snapshots exist (fresh
  machine, fresh clone), the bot **restores** the profile, memories, and weak
  areas automatically — so MISMATHE never forgets you, even across machines.

Controlled by `GITHUB_MEMORY_SYNC` in `.env`. The machine running the bot
needs push access to the repo (HTTPS token or SSH key configured in git).

## Commands

| Command | Purpose |
|---|---|
| `/start` | Initial onboarding + student profile setup |
| `/today` | The ONE most important task for today |
| `/schedule` | View / regenerate today's schedule |
| `/study` | Start the study stopwatch |
| `/stop` | Stop the active study session |
| `/checkin` | Daily check-in (mood, energy, confidence, study hours) |
| `/test` | Generate a test (chapter / weak-area / mock) |
| `/weak` | View / update weak areas |
| `/revise` | Spaced-repetition revision queue |
| `/mode` | Switch mentor mood (strict / calm / motivation / recovery / challenge / focus / friend) |
| `/dashboard` | Performance analytics — streaks, accuracy, productivity |
| `/sync` | Push memory snapshots to GitHub immediately |
| `/myid` | Show your Telegram user id (for the privacy lock) |
| `/recover` | Emergency 7-day recovery plan |
| `/news` | Latest MHT-CET / academic / tech updates |
| `/puzzle` | Daily brain teaser |
| `/movie` | Motivational movie recommendation |
| `/help` | Full command list |

Any free-form message becomes a conversation with MISMATHE — ask doubts, share
feelings, request guidance.

## Auto-push

The repo is configured with a Claude Code hook that auto-commits and pushes any
file edits to the development branch — see `.claude/settings.json`.

## Final Motto

> "MISMATHE does not just help the student crack MHT-CET. MISMATHE helps the
> student become the type of person capable of winning in academics and in
> life."
