"""Conversation + long-term memory helpers.

Short-term: last N turns of ConversationMessage (sent back to Claude).
Long-term: curated Memory rows (emotional patterns, fears, breakthroughs).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mismathe.db.models import ConversationMessage, Memory, Student, WeakArea


SHORT_TERM_TURNS = 30  # how many recent turns to replay to Claude


async def append_message(session: AsyncSession, student_id: int, role: str, content: str) -> None:
    session.add(ConversationMessage(student_id=student_id, role=role, content=content))


async def recent_messages(session: AsyncSession, student_id: int, limit: int = SHORT_TERM_TURNS) -> list[dict]:
    stmt = (
        select(ConversationMessage)
        .where(ConversationMessage.student_id == student_id)
        .order_by(ConversationMessage.id.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    rows = list(reversed(result.scalars().all()))
    return [{"role": r.role, "content": r.content} for r in rows]


async def add_memory(
    session: AsyncSession,
    student_id: int,
    *,
    kind: str,
    content: str,
    importance: int = 5,
) -> None:
    session.add(Memory(student_id=student_id, kind=kind, content=content, importance=importance))


async def long_term_summary(session: AsyncSession, student_id: int, limit: int = 15) -> str | None:
    stmt = (
        select(Memory)
        .where(Memory.student_id == student_id)
        .order_by(Memory.importance.desc(), Memory.id.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    rows = result.scalars().all()
    if not rows:
        return None
    return "\n".join(f"- [{m.kind}] {m.content}" for m in rows)


async def profile_summary(student: Student) -> str:
    parts: list[str] = [f"Name: {student.name or 'unknown'}", f"Standard: {student.standard}"]
    if student.current_percentage is not None:
        parts.append(f"Current %: {student.current_percentage}")
    parts.append(f"Target %: {student.target_percentage}")
    if student.school_timing:
        parts.append(f"Daily timings: {student.school_timing}")
    if student.daily_study_hours_target is not None:
        parts.append(f"Study target: {student.daily_study_hours_target} hrs/day")
    if student.sleep_schedule:
        parts.append(f"Sleep: {student.sleep_schedule}")
    if student.strong_subjects:
        parts.append(f"Strong: {student.strong_subjects}")
    if student.weak_subjects:
        parts.append(f"Weak: {student.weak_subjects}")
    if student.fear_areas:
        parts.append(f"Fears: {student.fear_areas}")
    if student.learning_style:
        parts.append(f"Learning style: {student.learning_style}")
    if student.confidence_level is not None:
        parts.append(f"Confidence: {student.confidence_level}/10")
    if student.stress_level is not None:
        parts.append(f"Stress: {student.stress_level}/10")
    if student.focus_level is not None:
        parts.append(f"Focus: {student.focus_level}/10")
    if student.streak_days:
        parts.append(f"Current streak: {student.streak_days} days")
    return "\n".join(parts)


async def weak_areas_summary(session: AsyncSession, student_id: int, limit: int = 12) -> str | None:
    stmt = (
        select(WeakArea)
        .where(WeakArea.student_id == student_id, WeakArea.resolved.is_(False))
        .order_by(WeakArea.severity.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    rows = result.scalars().all()
    if not rows:
        return None
    lines = []
    for w in rows:
        topic = f"{w.subject} → {w.chapter}"
        if w.sub_topic:
            topic += f" → {w.sub_topic}"
        if w.weakness_type:
            topic += f" ({w.weakness_type})"
        lines.append(f"- {topic} — severity {w.severity}/10")
    return "\n".join(lines)
