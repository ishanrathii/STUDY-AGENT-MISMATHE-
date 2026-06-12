"""APScheduler-based daily nudges — check-in reminder, motivation, streak guard."""
from __future__ import annotations

import logging
from datetime import date, datetime

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from config import settings
from mismathe.core.agent import respond_to_student
from mismathe.db.database import get_session
from mismathe.db.models import Student


logger = logging.getLogger(__name__)


def start_scheduler(application) -> AsyncIOScheduler:
    """Wire up cron jobs against the running telegram application."""
    tz = pytz.timezone(settings.timezone)
    scheduler = AsyncIOScheduler(timezone=tz)

    scheduler.add_job(
        _morning_focus,
        CronTrigger(hour=7, minute=30, timezone=tz),
        args=[application],
        id="morning_focus",
        replace_existing=True,
    )
    scheduler.add_job(
        _evening_checkin_nudge,
        CronTrigger(hour=21, minute=30, timezone=tz),
        args=[application],
        id="evening_checkin",
        replace_existing=True,
    )
    scheduler.add_job(
        _streak_guard,
        CronTrigger(hour=23, minute=30, timezone=tz),
        args=[application],
        id="streak_guard",
        replace_existing=True,
    )

    scheduler.start()
    application.bot_data["scheduler"] = scheduler
    logger.info("Scheduler started in %s.", settings.timezone)
    return scheduler


async def _all_active_students() -> list[Student]:
    async with get_session() as session:
        stmt = select(Student).where(Student.onboarding_completed.is_(True))
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def _morning_focus(application) -> None:
    bot = application.bot
    for student in await _all_active_students():
        prompt = (
            "It's morning. In ONE short message: (1) greet the student warmly, "
            "(2) name the ONE most important thing they should focus on today, "
            "(3) end with a tiny push. Keep it under 60 words."
        )
        try:
            reply = await respond_to_student(student, prompt, today_context="It is morning.", persist=False)
            await bot.send_message(chat_id=student.telegram_user_id, text=reply)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Morning nudge failed for %s: %s", student.telegram_user_id, exc)


async def _evening_checkin_nudge(application) -> None:
    bot = application.bot
    text = (
        "Hey 👋 — quick check-in time.\n\n"
        "Reply /checkin to log today (mood, hours, what felt hard). "
        "Even if today was off, just log it. Awareness > avoidance."
    )
    for student in await _all_active_students():
        try:
            await bot.send_message(chat_id=student.telegram_user_id, text=text)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Check-in nudge failed for %s: %s", student.telegram_user_id, exc)


async def _streak_guard(application) -> None:
    """Auto-roll the streak counter at end of day."""
    today = date.today()
    async with get_session() as session:
        result = await session.execute(select(Student).where(Student.onboarding_completed.is_(True)))
        for student in result.scalars().all():
            last = student.last_active_date
            if last == today:
                continue  # already counted via interaction
            # If they were active yesterday, freeze streak (counted earlier); else reset.
            if last and (today - last).days > 1:
                student.streak_days = 0


async def touch_streak(student: Student) -> None:
    """Bump the streak when the student interacts. Idempotent per day."""
    today = date.today()
    if student.last_active_date == today:
        return
    if student.last_active_date and (today - student.last_active_date).days == 1:
        student.streak_days += 1
    else:
        student.streak_days = 1
    student.last_active_date = today
