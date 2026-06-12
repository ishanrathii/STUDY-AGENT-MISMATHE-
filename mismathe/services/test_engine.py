"""Test generation — uses Claude to produce CET-style questions.

Returns rendered question blocks; grading is handled by free-form chat.
"""
from __future__ import annotations

from mismathe.core.agent import generate_with_prompt


TEST_GEN_SYSTEM = """\
You are MISMATHE's exam architect — a senior MHT-CET problem setter.

Generate practice questions that match the MHT-CET pattern:
- Single-correct MCQs with 4 options (A, B, C, D)
- CET-level conceptual + numerical mix
- Cover the specified topic, subject, and difficulty
- For each question, append the correct answer and a 1-2 line explanation

Format STRICTLY as:
Q1. <question text>
A) <option>
B) <option>
C) <option>
D) <option>
Answer: <letter>
Why: <brief explanation>

(blank line between questions)

Do not add intro or outro text. Just the questions.
"""


async def generate_test(
    *,
    subject: str,
    chapter: str | None,
    test_type: str,  # chapter | weak | mock | speed | formula
    difficulty: str = "medium",
    count: int = 10,
    weak_topics: list[str] | None = None,
) -> str:
    user_prompt_parts = [
        f"Generate {count} {difficulty}-difficulty MHT-CET style questions.",
        f"Subject: {subject}",
    ]
    if chapter:
        user_prompt_parts.append(f"Chapter: {chapter}")
    user_prompt_parts.append(f"Test type: {test_type}")
    if weak_topics:
        user_prompt_parts.append("Focus extra on these weak topics: " + ", ".join(weak_topics))
    if test_type == "speed":
        user_prompt_parts.append("Bias toward quick-solve shortcut-friendly questions.")
    if test_type == "formula":
        user_prompt_parts.append("Bias toward formula-application questions.")

    return await generate_with_prompt(
        system_prompt=TEST_GEN_SYSTEM,
        user_message="\n".join(user_prompt_parts),
        max_tokens=4096,
    )
