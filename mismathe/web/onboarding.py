"""Web-version onboarding flow.

When a student first opens the site, MISMATHE asks them the questions defined
in prompts.ONBOARDING_QUESTIONS one at a time. Each user reply updates the
matching column on the Student row, and we return the next question. Once
all questions are answered, onboarding_completed flips to True and free-form
chat takes over.
"""
from __future__ import annotations

import re

from mismathe.core.prompts import (
    ONBOARDING_COMPLETE,
    ONBOARDING_INTRO,
    ONBOARDING_QUESTIONS,
)
from mismathe.db.models import Student


NUMERIC_FIELDS = {
    "current_percentage": float,
    "daily_study_hours_target": float,
    "phone_usage_hours": float,
    "confidence_level": int,
    "stress_level": int,
    "focus_level": int,
}


def _question_keys() -> list[str]:
    return [k for k, _ in ONBOARDING_QUESTIONS]


def next_question_for(stage: str) -> tuple[str, str] | None:
    """Return (field, question_text) for the question following stage, or None if done."""
    keys = _question_keys()
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


def intro_message() -> str:
    return ONBOARDING_INTRO


def complete_message() -> str:
    return ONBOARDING_COMPLETE


def handle_onboarding_turn(student: Student, user_text: str) -> str:
    """Capture the answer for the current stage, advance, return next prompt.

    Mutates the student in-place; caller commits the session.
    """
    stage = student.onboarding_stage or "welcome"

    # First message after the intro: ask question 1
    if stage == "welcome":
        field, question = ONBOARDING_QUESTIONS[0]
        student.onboarding_stage = field
        return question

    field = stage
    try:
        value = _parse_value(field, user_text)
    except ValueError:
        return "Just a number for that one 🙂"

    setattr(student, field, value)

    nxt = next_question_for(field)
    if nxt is None:
        student.onboarding_completed = True
        student.onboarding_stage = "done"
        return complete_message()

    next_field, next_q = nxt
    student.onboarding_stage = next_field
    return next_q
