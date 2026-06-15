"""APScheduler — nightly memory sync, daily streak guard.

In the web version, daily nudges go to the user via the in-app inbox table
(the "today" panel) rather than push notifications, so the scheduler's main
job is durable persistence + streak bookkeeping.
"""
from __future__ import annotations

import logging
from datetime import date

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from config import settings
from mismathe.db.database import get_session
from mismathe.db.models import Student
from mismathe.services.github_memory import sync_to_github


logger = logging.getLogger(__name__)


def start_scheduler() -> AsyncIOScheduler:
    """Wire up cron jobs against the running event loop."""
    tz = pytz.timezone(settings.timezone)
    scheduler = AsyncIOScheduler(timezone=tz)

    scheduler.add_job(
        _streak_guard,
        CronTrigger(hour=23, minute=30, timezone=tz),
        id="streak_guard",
        replace_existing=True,
    )
    scheduler.add_job(
        _nightly_memory_sync,
        CronTrigger(hour=23, minute=45, timezone=tz),
        id="memory_sync",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started in %s.", settings.timezone)
    return scheduler


async def _nightly_memory_sync() -> None:
    """Push memory snapshots to GitHub every night."""
    try:
        await sync_to_github()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Nightly memory sync failed: %s", exc)


async def _streak_guard() -> None:
    """Reset streaks for students who went silent more than a day."""
    today = date.today()
    async with get_session() as session:
        result = await session.execute(select(Student).where(Student.onboarding_completed.is_(True)))
        for student in result.scalars().all():
            last = student.last_active_date
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
