"""Student lookup / creation helpers — used by all handlers."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import User

from config import settings
from mismathe.db.models import Student


async def get_or_create_student(session: AsyncSession, tg_user: User) -> Student:
    stmt = select(Student).where(Student.telegram_user_id == tg_user.id)
    result = await session.execute(stmt)
    student = result.scalar_one_or_none()
    if student is None:
        student = Student(
            telegram_user_id=tg_user.id,
            telegram_username=tg_user.username,
            name=tg_user.first_name,
            mentor_mode=settings.default_mode,
        )
        session.add(student)
        await session.flush()
    return student


async def get_student(session: AsyncSession, tg_user_id: int) -> Student | None:
    stmt = select(Student).where(Student.telegram_user_id == tg_user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
