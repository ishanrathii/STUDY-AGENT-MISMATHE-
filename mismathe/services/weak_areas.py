"""Weak-area tracking — add, update, resolve, query."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mismathe.db.models import WeakArea


async def record_weakness(
    session: AsyncSession,
    student_id: int,
    *,
    subject: str,
    chapter: str,
    sub_topic: str | None = None,
    weakness_type: str | None = None,
    severity: int = 5,
    notes: str | None = None,
) -> WeakArea:
    """Insert a new weak area (or sharpen an existing one if matched)."""
    existing = await _find_existing(session, student_id, subject, chapter, sub_topic)
    if existing:
        existing.severity = max(existing.severity, severity)
        if notes:
            existing.notes = (existing.notes + "\n" if existing.notes else "") + notes
        existing.resolved = False
        existing.updated_at = datetime.utcnow()
        return existing

    weak = WeakArea(
        student_id=student_id,
        subject=subject,
        chapter=chapter,
        sub_topic=sub_topic,
        weakness_type=weakness_type,
        severity=severity,
        notes=notes,
    )
    session.add(weak)
    await session.flush()
    return weak


async def resolve_weakness(session: AsyncSession, weak_id: int) -> None:
    weak = await session.get(WeakArea, weak_id)
    if weak:
        weak.resolved = True
        weak.updated_at = datetime.utcnow()


async def all_weaknesses(session: AsyncSession, student_id: int) -> list[WeakArea]:
    stmt = (
        select(WeakArea)
        .where(WeakArea.student_id == student_id, WeakArea.resolved.is_(False))
        .order_by(WeakArea.severity.desc(), WeakArea.id.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def _find_existing(
    session: AsyncSession,
    student_id: int,
    subject: str,
    chapter: str,
    sub_topic: str | None,
) -> WeakArea | None:
    stmt = select(WeakArea).where(
        WeakArea.student_id == student_id,
        WeakArea.subject == subject,
        WeakArea.chapter == chapter,
        WeakArea.sub_topic == sub_topic,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
