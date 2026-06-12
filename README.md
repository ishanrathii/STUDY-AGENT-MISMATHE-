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

## Setup

1. Copy `.env.example` to `.env` and fill in:
   - `TELEGRAM_BOT_TOKEN` — from @BotFather
   - `ANTHROPIC_API_KEY` — from console.anthropic.com
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the bot:
   ```bash
   python main.py
   ```

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
