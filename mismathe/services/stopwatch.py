"""Study stopwatch — tracks active sessions per student."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mismathe.db.models import StudySession


async def start_session(
    session: AsyncSession,
    student_id: int,
    *,
    subject: str | None = None,
    chapter: str | None = None,
    activity: str = "study",
) -> StudySession:
    """Start a new active session. Closes any open one first."""
    open_one = await _active_session(session, student_id)
    if open_one:
        await stop_session(session, open_one)

    new_session = StudySession(
        student_id=student_id,
        subject=subject,
        chapter=chapter,
        activity=activity,
        started_at=datetime.utcnow(),
    )
    session.add(new_session)
    await session.flush()
    return new_session


async def stop_session(session: AsyncSession, study_session: StudySession) -> StudySession:
    if study_session.ended_at is None:
        study_session.ended_at = datetime.utcnow()
        delta = study_session.ended_at - study_session.started_at
        study_session.duration_minutes = max(1, int(delta.total_seconds() // 60))
    return study_session


async def active_session(session: AsyncSession, student_id: int) -> StudySession | None:
    return await _active_session(session, student_id)


async def _active_session(session: AsyncSession, student_id: int) -> StudySession | None:
    stmt = (
        select(StudySession)
        .where(
            StudySession.student_id == student_id,
            StudySession.ended_at.is_(None),
        )
        .order_by(StudySession.id.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def stop_active(session: AsyncSession, student_id: int) -> StudySession | None:
    active = await _active_session(session, student_id)
    if active is None:
        return None
    return await stop_session(session, active)
