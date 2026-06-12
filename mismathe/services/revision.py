"""Spaced repetition — SM-2 lite for revision items."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mismathe.db.models import RevisionItem


async def add_card(
    session: AsyncSession,
    student_id: int,
    *,
    subject: str,
    chapter: str,
    topic: str,
    content: str | None = None,
) -> RevisionItem:
    item = RevisionItem(
        student_id=student_id,
        subject=subject,
        chapter=chapter,
        topic=topic,
        content=content,
        due_date=date.today(),
    )
    session.add(item)
    await session.flush()
    return item


async def due_today(session: AsyncSession, student_id: int, *, limit: int = 20) -> list[RevisionItem]:
    stmt = (
        select(RevisionItem)
        .where(RevisionItem.student_id == student_id, RevisionItem.due_date <= date.today())
        .order_by(RevisionItem.due_date.asc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def grade_card(session: AsyncSession, item: RevisionItem, quality: int) -> RevisionItem:
    """SM-2: quality 0-5. <3 resets; >=3 advances."""
    quality = max(0, min(5, quality))
    if quality < 3:
        item.repetitions = 0
        item.interval_days = 1
    else:
        item.repetitions += 1
        if item.repetitions == 1:
            item.interval_days = 1
        elif item.repetitions == 2:
            item.interval_days = 6
        else:
            item.interval_days = max(1, round(item.interval_days * item.ease))
        item.ease = max(1.3, item.ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))

    item.last_reviewed = datetime.utcnow()
    item.due_date = date.today() + timedelta(days=item.interval_days)
    return item
