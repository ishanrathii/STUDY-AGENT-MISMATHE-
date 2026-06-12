"""Performance dashboard — streaks, hours, accuracy, weak-area trends."""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mismathe.db.models import DailyCheckin, StudySession, TestAttempt, WeakArea


async def study_hours_last_n_days(session: AsyncSession, student_id: int, days: int = 7) -> float:
    since = date.today() - timedelta(days=days)
    stmt = select(func.coalesce(func.sum(StudySession.duration_minutes), 0)).where(
        StudySession.student_id == student_id,
        StudySession.started_at >= since,
        StudySession.ended_at.is_not(None),
    )
    result = await session.execute(stmt)
    minutes = result.scalar() or 0
    return round(minutes / 60.0, 1)


async def avg_accuracy(session: AsyncSession, student_id: int, days: int = 30) -> float | None:
    since = date.today() - timedelta(days=days)
    stmt = select(func.avg(TestAttempt.accuracy)).where(
        TestAttempt.student_id == student_id,
        TestAttempt.created_at >= since,
        TestAttempt.accuracy.is_not(None),
    )
    result = await session.execute(stmt)
    val = result.scalar()
    return round(val, 1) if val is not None else None


async def unresolved_weak_count(session: AsyncSession, student_id: int) -> int:
    stmt = select(func.count(WeakArea.id)).where(
        WeakArea.student_id == student_id, WeakArea.resolved.is_(False)
    )
    result = await session.execute(stmt)
    return int(result.scalar() or 0)


async def checkin_days_last_n(session: AsyncSession, student_id: int, days: int = 7) -> int:
    since = date.today() - timedelta(days=days)
    stmt = select(func.count(DailyCheckin.id)).where(
        DailyCheckin.student_id == student_id, DailyCheckin.checkin_date >= since
    )
    result = await session.execute(stmt)
    return int(result.scalar() or 0)


async def render_dashboard(session: AsyncSession, student_id: int, streak: int) -> str:
    week_hours = await study_hours_last_n_days(session, student_id, days=7)
    month_acc = await avg_accuracy(session, student_id, days=30)
    open_weak = await unresolved_weak_count(session, student_id)
    week_checkins = await checkin_days_last_n(session, student_id, days=7)

    lines = [
        "📊 *YOUR DASHBOARD*",
        "",
        f"🔥 Streak: *{streak}* days",
        f"🕒 Study (last 7 days): *{week_hours} hrs*",
        f"🎯 Accuracy (last 30 days): *{month_acc}%*" if month_acc is not None else "🎯 Accuracy: no tests yet — try /test",
        f"📌 Open weak areas: *{open_weak}*",
        f"✅ Daily check-ins this week: *{week_checkins}/7*",
    ]
    return "\n".join(lines)
