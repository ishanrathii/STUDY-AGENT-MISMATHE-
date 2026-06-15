"""MISMATHE AI agent — wraps the Anthropic Claude API.

Uses claude-opus-4-8 with adaptive thinking + high effort for the most
intelligent, identity-aware mentoring.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Iterable

from anthropic import AsyncAnthropic

from config import settings
from mismathe.core.memory import (
    add_memory,
    append_message,
    long_term_summary,
    profile_summary,
    recent_messages,
    weak_areas_summary,
)
from mismathe.core.prompts import build_system_prompt
from mismathe.db.database import get_session
from mismathe.db.models import Student


logger = logging.getLogger(__name__)

_client = AsyncAnthropic(api_key=settings.anthropic_api_key)


async def respond_to_student(
    student: Student,
    user_message: str,
    *,
    today_context: str | None = None,
    extra_system: str | None = None,
    persist: bool = True,
) -> str:
    """Send a message to MISMATHE and return the reply text.

    Loads recent history + profile + weak areas + long-term memory and
    composes them into the system prompt so the model has full context.
    """
    async with get_session() as session:
        history = await recent_messages(session, student.id)
        profile = await profile_summary(student)
        weak = await weak_areas_summary(session, student.id)
        memories = await long_term_summary(session, student.id)

    system_prompt = build_system_prompt(
        mode_key=student.mentor_mode,
        student_profile=profile,
        weak_areas_summary=weak,
        long_term_memory=memories,
        today_context=today_context,
    )
    if extra_system:
        system_prompt = system_prompt + "\n\n" + extra_system

    messages = list(history) + [{"role": "user", "content": user_message}]

    reply = await _call_claude(system_prompt, messages)

    if persist:
        async with get_session() as session:
            await append_message(session, student.id, "user", user_message)
            await append_message(session, student.id, "assistant", reply)

    return reply


async def generate_with_prompt(
    *,
    system_prompt: str,
    user_message: str,
    max_tokens: int = 4096,
) -> str:
    """Stateless one-shot helper for tests, schedules, analytics."""
    return await _call_claude(system_prompt, [{"role": "user", "content": user_message}], max_tokens=max_tokens)


async def remember(student_id: int, *, kind: str, content: str, importance: int = 5) -> None:
    """Quick wrapper to write a long-term memory."""
    async with get_session() as session:
        await add_memory(session, student_id, kind=kind, content=content, importance=importance)


async def _call_claude(
    system_prompt: str,
    messages: Iterable[dict],
    *,
    max_tokens: int = 4096,
) -> str:
    """Single Claude call with adaptive thinking + retries."""
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = await _client.messages.create(
                model=settings.anthropic_model,
                max_tokens=max_tokens,
                thinking={"type": "adaptive"},
                output_config={"effort": "high"},
                system=system_prompt,
                messages=list(messages),
            )
            chunks = [block.text for block in response.content if block.type == "text"]
            return "\n".join(chunks).strip() or "(I'm here. Tell me more.)"
        except Exception as exc:  # noqa: BLE001 - log and retry then surface a friendly fallback
            last_error = exc
            logger.warning("Claude call failed (attempt %s): %s", attempt + 1, exc)
            await asyncio.sleep(2 ** attempt)

    logger.error("Claude call exhausted retries: %s", last_error)
    return (
        "Hmm, my brain just glitched 😅 — give me a moment and try again. "
        "If it keeps happening, ping the admin."
    )
