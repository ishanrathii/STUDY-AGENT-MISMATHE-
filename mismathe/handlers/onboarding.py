"""Onboarding flow — captures the initial student profile, question by question."""
from __future__ import annotations

import re

from telegram import Update
from telegram.ext import ContextTypes

from mismathe.core.prompts import (
    ONBOARDING_COMPLETE,
    ONBOARDING_INTRO,
    ONBOARDING_QUESTIONS,
)
from mismathe.db.database import get_session
from mismathe.db.models import Student
from mismathe.utils.students import get_or_create_student


# Fields where we want a numeric value
NUMERIC_FIELDS = {
    "current_percentage": float,
    "daily_study_hours_target": float,
    "phone_usage_hours": float,
    "confidence_level": int,
    "stress_level": int,
    "focus_level": int,
}


def _next_question_for(stage: str) -> tuple[str, str] | None:
    keys = [k for k, _ in ONBOARDING_QUESTIONS]
    if stage == "welcome":
        return ONBOARDING_QUESTIONS[0]
    if stage in keys:
        idx = keys.index(stage)
        if idx + 1 < len(ONBOARDING_QUESTIONS):
            return ONBOARDING_QUESTIONS[idx + 1]
        return None
    return ONBOARDING_QUESTIONS[0]


def _parse_value(field: str, raw: str) -> object:
    raw = raw.strip()
    if field in NUMERIC_FIELDS:
        m = re.search(r"-?\d+(?:\.\d+)?", raw)
        if not m:
            raise ValueError("number please")
        return NUMERIC_FIELDS[field](float(m.group()))
    return raw


async def start_onboarding(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user and update.message
    async with get_session() as session:
        student = await get_or_create_student(session, update.effective_user)
        student.onboarding_stage = "welcome"
        student.onboarding_completed = False
    await update.message.reply_text(ONBOARDING_INTRO)


async def maybe_handle_onboarding(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    """If the student is mid-onboarding, capture the answer and ask the next question.

    Returns True if the message was consumed by onboarding.
    """
    assert update.effective_user and update.message and update.message.text
    text = update.message.text

    async with get_session() as session:
        student = await get_or_create_student(session, update.effective_user)
        if student.onboarding_completed:
            return False

        stage = student.onboarding_stage or "welcome"

        # First incoming message after intro → ask question 1
        if stage == "welcome":
            field, question = ONBOARDING_QUESTIONS[0]
            student.onboarding_stage = field
            await update.message.reply_text(question)
            return True

        # We are currently waiting on an answer for `stage`
        field = stage
        try:
            value = _parse_value(field, text)
        except ValueError:
            await update.message.reply_text("Just a number for that one 🙂")
            return True

        _assign_field(student, field, value)

        nxt = _next_question_for(field)
        if nxt is None:
            student.onboarding_completed = True
            student.onboarding_stage = "done"
            await update.message.reply_text(ONBOARDING_COMPLETE)
        else:
            next_field, next_q = nxt
            student.onboarding_stage = next_field
            await update.message.reply_text(next_q)
        return True


def _assign_field(student: Student, field: str, value: object) -> None:
    setattr(student, field, value)
