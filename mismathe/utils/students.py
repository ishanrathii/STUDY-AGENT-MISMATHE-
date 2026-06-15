"""Student lookup / creation helpers — used by web routes."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from mismathe.db.models import Student


async def get_or_create_student(
    session: AsyncSession,
    external_id: str,
    *,
    display_handle: str | None = None,
) -> Student:
    """Find or create the student for this browser session."""
    stmt = select(Student).where(Student.external_id == external_id)
    result = await session.execute(stmt)
    student = result.scalar_one_or_none()
    if student is None:
        student = Student(
            external_id=external_id,
            display_handle=display_handle,
            mentor_mode=settings.default_mode,
        )
        session.add(student)
        await session.flush()
    return student


async def get_student(session: AsyncSession, external_id: str) -> Student | None:
    stmt = select(Student).where(Student.external_id == external_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
