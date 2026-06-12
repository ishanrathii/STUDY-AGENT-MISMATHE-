"""All slash-command handlers for MISMATHE."""
from __future__ import annotations

import logging
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from mismathe.content.motivation import random_recommendation
from mismathe.content.puzzles import random_puzzle
from mismathe.content.syllabus import HIGH_PRIORITY_CHAPTERS, subjects
from mismathe.core.agent import respond_to_student
from mismathe.core.modes import get_mode, list_modes
from mismathe.db.database import get_session
from mismathe.handlers.onboarding import start_onboarding
from mismathe.services.analytics import render_dashboard
from mismathe.services.scheduler import touch_streak
from mismathe.services.stopwatch import active_session, start_session, stop_active
from mismathe.services.test_engine import generate_test
from mismathe.utils.students import get_or_create_student, get_student


logger = logging.getLogger(__name__)


HELP_TEXT = """\
*MISMATHE — your CET mentor*

/today — your ONE focus for today
/schedule — generate today's schedule
/study — start study stopwatch
/stop — stop active study session
/checkin — daily check-in (mood, hours, what was hard)
/test — generate a test (chapter / weak-area / mock)
/weak — view your weak areas
/revise — spaced-repetition revision queue
/mode — switch mentor mood (strict / calm / motivation / recovery / challenge / focus / friend)
/dashboard — your stats: streak, hours, accuracy
/recover — emergency 7-day recovery plan
/news — academic + CET updates
/puzzle — daily brain teaser
/movie — motivational recommendation
/help — this list

Or just *chat with me* — I'm always here.
"""


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await start_onboarding(update, ctx)


async def cmd_help(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.MARKDOWN)


async def cmd_today(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user and update.message
    async with get_session() as session:
        student = await get_or_create_student(session, update.effective_user)
        await touch_streak(student)
        if not student.onboarding_completed:
            await update.message.reply_text("Let's finish setting you up first — type /start.")
            return

    prompt = (
        "Give the student their ONE most important task for today. "
        "Just ONE — to reduce overwhelm. Anchor it to a specific weak area "
        "or high-priority chapter from their profile. Be concrete: subject, "
        "chapter, time block, expected outcome. Under 100 words."
    )
    reply = await respond_to_student(student, prompt, today_context=f"Date/time: {datetime.utcnow().isoformat()}", persist=False)
    await update.message.reply_text(reply)


async def cmd_schedule(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user and update.message
    async with get_session() as session:
        student = await get_or_create_student(session, update.effective_user)
        await touch_streak(student)
        if not student.onboarding_completed:
            await update.message.reply_text("Run /start to set up first.")
            return

    prompt = (
        "Build a realistic study schedule for TODAY for this student. "
        "Consider their school/coaching timings, energy patterns, sleep, and target hours. "
        "Hard subjects during peak focus, revision during low energy. "
        "Include breaks. End with the ONE highest-priority block. "
        "Use bullet list with timings."
    )
    reply = await respond_to_student(student, prompt, persist=False)
    await update.message.reply_text(reply)


async def cmd_study(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user and update.message
    args_text = " ".join(update.message.text.split()[1:]) if update.message.text else ""
    subject = args_text.split("/")[0].strip() if "/" in args_text else args_text or None
    chapter = args_text.split("/", 1)[1].strip() if "/" in args_text else None

    async with get_session() as session:
        student = await get_or_create_student(session, update.effective_user)
        await touch_streak(student)
        sess = await start_session(session, student.id, subject=subject, chapter=chapter)

    where = f"{subject}" + (f" → {chapter}" if chapter else "") if subject else "study"
    await update.message.reply_text(
        f"⏱️ Stopwatch ON — *{where}*\n\nGo deep. Reply /stop when you're done.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_stop(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user and update.message
    async with get_session() as session:
        student = await get_or_create_student(session, update.effective_user)
        sess = await stop_active(session, student.id)

    if sess is None:
        await update.message.reply_text("No active session. /study to start one.")
        return
    await update.message.reply_text(
        f"✅ Logged *{sess.duration_minutes} minutes* on "
        f"*{sess.subject or 'study'}{(' → ' + sess.chapter) if sess.chapter else ''}*.\n\n"
        f"How focused were you? Reply with a number 1-10.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_checkin(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Start an AI-driven check-in conversation."""
    assert update.effective_user and update.message
    async with get_session() as session:
        student = await get_or_create_student(session, update.effective_user)
        await touch_streak(student)
        if not student.onboarding_completed:
            await update.message.reply_text("Run /start first.")
            return

    prompt = (
        "Run today's daily check-in. Ask the student warmly: "
        "(1) what did they study today, (2) productive hours, "
        "(3) what felt hard, (4) energy level 1-10, "
        "(5) mood + stress + confidence. Mix all into ONE conversational "
        "message, not a form. Tell them I'll record their answers as they reply naturally."
    )
    reply = await respond_to_student(student, prompt, persist=False)
    await update.message.reply_text(reply)


async def cmd_test(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user and update.message
    parts = update.message.text.split() if update.message.text else []
    subject = parts[1].capitalize() if len(parts) > 1 else None
    chapter = " ".join(parts[2:]) if len(parts) > 2 else None

    if subject is None or subject not in subjects():
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(s, callback_data=f"test:{s}")] for s in subjects()])
        await update.message.reply_text("Which subject?", reply_markup=kb)
        return

    await update.message.reply_text("⚙️ Generating your test — give me a few seconds…")
    test_text = await generate_test(
        subject=subject,
        chapter=chapter,
        test_type="chapter" if chapter else "mock",
        difficulty="medium",
        count=10,
    )
    await update.message.reply_text(test_text)


async def cmd_weak(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user and update.message
    async with get_session() as session:
        student = await get_or_create_student(session, update.effective_user)
    prompt = (
        "List the student's current tracked weak areas (from the system prompt context) "
        "with severity. Then suggest the top 3 to focus on this week. Be specific. Bullet list."
    )
    reply = await respond_to_student(student, prompt, persist=False)
    await update.message.reply_text(reply)


async def cmd_revise(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user and update.message
    async with get_session() as session:
        student = await get_or_create_student(session, update.effective_user)

    prompt = (
        "Pull together a 20-minute rapid revision session for the student "
        "covering their top 2 weak areas. For each: (a) 3 key formulas/concepts, "
        "(b) 1 worked example, (c) 1 trick to remember. End with a single "
        "self-test question for each."
    )
    reply = await respond_to_student(student, prompt, persist=False)
    await update.message.reply_text(reply)


async def cmd_mode(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message
    rows = []
    for m in list_modes():
        rows.append([InlineKeyboardButton(f"{m.emoji} {m.label}", callback_data=f"mode:{m.key}")])
    kb = InlineKeyboardMarkup(rows)
    await update.message.reply_text("Pick a mentor mode:", reply_markup=kb)


async def on_mode_callback(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    assert query and query.from_user and query.data
    await query.answer()
    _, mode_key = query.data.split(":", 1)
    mode = get_mode(mode_key)

    async with get_session() as session:
        student = await get_or_create_student(session, query.from_user)
        student.mentor_mode = mode.key

    await query.edit_message_text(f"{mode.emoji} Switched to *{mode.label} Mode*.\n\n_{mode.description}_", parse_mode=ParseMode.MARKDOWN)


async def on_test_callback(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    assert query and query.data
    await query.answer()
    _, subject = query.data.split(":", 1)
    await query.edit_message_text(f"⚙️ Generating a {subject} mock test — hang on…")

    test_text = await generate_test(
        subject=subject,
        chapter=None,
        test_type="mock",
        difficulty="medium",
        count=10,
    )
    if query.message:
        await query.message.reply_text(test_text)


async def cmd_dashboard(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user and update.message
    async with get_session() as session:
        student = await get_or_create_student(session, update.effective_user)
        await touch_streak(student)
        text = await render_dashboard(session, student.id, student.streak_days)
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_recover(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user and update.message
    async with get_session() as session:
        student = await get_or_create_student(session, update.effective_user)
        student.mentor_mode = "recovery"

    prompt = (
        "The student has fallen off track. Build a 7-day RECOVERY plan: "
        "Day 1-2 = re-build tiny momentum (1 short focus block, 1 revision, 1 self-care). "
        "Day 3-5 = ramp to 60% of normal load on highest-priority weak areas only. "
        "Day 6-7 = full schedule with 1 mock. NO guilt language. Frame as a clean restart. "
        "Output as a day-by-day bullet plan."
    )
    reply = await respond_to_student(student, prompt, persist=False)
    await update.message.reply_text("🩹 RECOVERY MODE activated. Past is past. Let's go.\n\n" + reply)


async def cmd_news(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user and update.message
    async with get_session() as session:
        student = await get_or_create_student(session, update.effective_user)
    prompt = (
        "Give the student 3 bullet updates: "
        "(1) any recent MHT-CET / HSC pattern news the student should know, "
        "(2) one motivating science/tech development of the week, "
        "(3) one productivity insight. "
        "If you don't have real recent news, give evergreen high-value updates and say so."
    )
    reply = await respond_to_student(student, prompt, persist=False)
    await update.message.reply_text(reply)


async def cmd_puzzle(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message
    p = random_puzzle()
    text = f"🧩 *Brain teaser*\n\n{p.question}"
    if p.hint:
        text += f"\n\n_Hint: {p.hint}_"
    text += f"\n\n||{p.answer}||"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)


async def cmd_movie(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message
    r = random_recommendation()
    await update.message.reply_text(
        f"🎬 *{r.title}* ({r.kind})\n\n_{r.why}_",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_priority(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Show high-weightage MHT-CET chapters."""
    assert update.message
    lines = ["📌 *High-weightage MHT-CET chapters*\n"]
    for subj, chapters in HIGH_PRIORITY_CHAPTERS.items():
        lines.append(f"*{subj}*")
        lines.extend(f"  • {c}" for c in chapters)
        lines.append("")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
