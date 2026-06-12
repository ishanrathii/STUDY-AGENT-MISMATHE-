"""GitHub-backed memory persistence.

The live database is SQLite (fast, local). This module makes the agent's
memory durable and portable by exporting every student's brain — profile,
long-term memories, weak areas, check-ins, test history — to JSON files
under memory/ and pushing them to the GitHub repo.

Flow:
- export_all()        DB -> memory/student_<telegram_id>.json
- sync_to_github()    export_all() + git add/commit/push (retries with backoff)
- restore_if_empty()  on startup, if the DB has no students but memory/ files
                      exist (fresh machine, fresh clone), rebuild profile,
                      memories, and weak areas from the JSON snapshots.

Runs daily at 23:45 via the scheduler, and on demand via /sync.
"""
from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path

from sqlalchemy import func, select

from config import ROOT, settings
from mismathe.db.database import get_session
from mismathe.db.models import (
    DailyCheckin,
    Memory,
    Student,
    TestAttempt,
    WeakArea,
)


logger = logging.getLogger(__name__)

MEMORY_DIR = ROOT / "memory"


def _iso(value) -> str | None:
    return value.isoformat() if value is not None else None


async def export_all() -> list[Path]:
    """Write one JSON snapshot per student. Returns written paths."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    async with get_session() as session:
        students = (await session.execute(select(Student))).scalars().all()
        for student in students:
            snapshot = await _snapshot_student(session, student)
            path = MEMORY_DIR / f"student_{student.telegram_user_id}.json"
            path.write_text(
                json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            written.append(path)

    logger.info("Exported %s memory snapshot(s) to %s", len(written), MEMORY_DIR)
    return written


async def _snapshot_student(session, student: Student) -> dict:
    memories = (
        (
            await session.execute(
                select(Memory)
                .where(Memory.student_id == student.id)
                .order_by(Memory.id.asc())
            )
        )
        .scalars()
        .all()
    )
    weak_areas = (
        (
            await session.execute(
                select(WeakArea)
                .where(WeakArea.student_id == student.id)
                .order_by(WeakArea.id.asc())
            )
        )
        .scalars()
        .all()
    )
    checkins = (
        (
            await session.execute(
                select(DailyCheckin)
                .where(DailyCheckin.student_id == student.id)
                .order_by(DailyCheckin.checkin_date.desc())
                .limit(30)
            )
        )
        .scalars()
        .all()
    )
    tests = (
        (
            await session.execute(
                select(TestAttempt)
                .where(TestAttempt.student_id == student.id)
                .order_by(TestAttempt.id.desc())
                .limit(20)
            )
        )
        .scalars()
        .all()
    )

    return {
        "format_version": 1,
        "exported_at": datetime.utcnow().isoformat(),
        "telegram_user_id": student.telegram_user_id,
        "telegram_username": student.telegram_username,
        "name": student.name,
        "profile": {
            "standard": student.standard,
            "current_percentage": student.current_percentage,
            "target_percentage": student.target_percentage,
            "school_timing": student.school_timing,
            "coaching_timing": student.coaching_timing,
            "daily_study_hours_target": student.daily_study_hours_target,
            "sleep_schedule": student.sleep_schedule,
            "strong_subjects": student.strong_subjects,
            "weak_subjects": student.weak_subjects,
            "fear_areas": student.fear_areas,
            "learning_style": student.learning_style,
            "confidence_level": student.confidence_level,
            "stress_level": student.stress_level,
            "focus_level": student.focus_level,
            "motivation_level": student.motivation_level,
            "phone_usage_hours": student.phone_usage_hours,
            "social_media_addiction": student.social_media_addiction,
            "mentor_mode": student.mentor_mode,
            "onboarding_completed": student.onboarding_completed,
            "streak_days": student.streak_days,
            "last_active_date": _iso(student.last_active_date),
        },
        "memories": [
            {
                "kind": m.kind,
                "content": m.content,
                "importance": m.importance,
                "created_at": _iso(m.created_at),
            }
            for m in memories
        ],
        "weak_areas": [
            {
                "subject": w.subject,
                "chapter": w.chapter,
                "sub_topic": w.sub_topic,
                "weakness_type": w.weakness_type,
                "severity": w.severity,
                "confidence": w.confidence,
                "notes": w.notes,
                "resolved": w.resolved,
            }
            for w in weak_areas
        ],
        "recent_checkins": [
            {
                "date": _iso(c.checkin_date),
                "what_studied": c.what_studied,
                "productive_hours": c.productive_hours,
                "difficult_topics": c.difficult_topics,
                "revised": c.revised,
                "energy_level": c.energy_level,
                "mood": c.mood,
                "confidence": c.confidence,
                "stress": c.stress,
            }
            for c in checkins
        ],
        "recent_tests": [
            {
                "test_type": t.test_type,
                "subject": t.subject,
                "chapter": t.chapter,
                "difficulty": t.difficulty,
                "total_questions": t.total_questions,
                "correct": t.correct,
                "accuracy": t.accuracy,
                "created_at": _iso(t.created_at),
            }
            for t in tests
        ],
    }


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True
    )


def _git_push_memory() -> bool:
    """git add memory/ + commit + push, with retry/backoff. Blocking — run in a thread."""
    if _git("rev-parse", "--is-inside-work-tree").returncode != 0:
        logger.warning("Not a git repo — skipping GitHub memory sync.")
        return False

    _git("add", "memory")
    if _git("diff", "--cached", "--quiet").returncode == 0:
        logger.info("Memory unchanged — nothing to push.")
        return True

    stamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    commit = _git("commit", "-m", f"memory: sync snapshots ({stamp})")
    if commit.returncode != 0:
        logger.warning("Memory commit failed: %s", commit.stderr.strip())
        return False

    branch = settings.git_branch or _git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip() or "main"
    for delay in (0, 2, 4, 8, 16):
        if delay:
            time.sleep(delay)
        push = _git("push", "-u", "origin", branch)
        if push.returncode == 0:
            logger.info("Memory pushed to origin/%s.", branch)
            return True
    logger.error("Memory push failed after retries (branch %s).", branch)
    return False


async def sync_to_github() -> bool:
    """Export snapshots and push them. Returns True on success/no-op."""
    await export_all()
    if not settings.github_memory_sync:
        logger.info("GITHUB_MEMORY_SYNC disabled — snapshots written locally only.")
        return True
    return await asyncio.to_thread(_git_push_memory)


async def restore_if_empty() -> int:
    """If the DB has no students but snapshots exist, rebuild from JSON.

    Restores profile, long-term memories, and weak areas (the agent's brain).
    Check-in / test history stays in the snapshot for reference but isn't
    re-inserted. Returns the number of students restored.
    """
    if not MEMORY_DIR.exists():
        return 0
    snapshots = sorted(MEMORY_DIR.glob("student_*.json"))
    if not snapshots:
        return 0

    async with get_session() as session:
        count = (await session.execute(select(func.count(Student.id)))).scalar() or 0
        if count > 0:
            return 0

        restored = 0
        for path in snapshots:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Skipping corrupt snapshot %s: %s", path.name, exc)
                continue

            profile = data.get("profile", {})
            student = Student(
                telegram_user_id=data["telegram_user_id"],
                telegram_username=data.get("telegram_username"),
                name=data.get("name"),
                standard=profile.get("standard", "11"),
                current_percentage=profile.get("current_percentage"),
                target_percentage=profile.get("target_percentage", 90.0),
                school_timing=profile.get("school_timing"),
                coaching_timing=profile.get("coaching_timing"),
                daily_study_hours_target=profile.get("daily_study_hours_target"),
                sleep_schedule=profile.get("sleep_schedule"),
                strong_subjects=profile.get("strong_subjects"),
                weak_subjects=profile.get("weak_subjects"),
                fear_areas=profile.get("fear_areas"),
                learning_style=profile.get("learning_style"),
                confidence_level=profile.get("confidence_level"),
                stress_level=profile.get("stress_level"),
                focus_level=profile.get("focus_level"),
                motivation_level=profile.get("motivation_level"),
                phone_usage_hours=profile.get("phone_usage_hours"),
                social_media_addiction=profile.get("social_media_addiction"),
                mentor_mode=profile.get("mentor_mode", settings.default_mode),
                onboarding_completed=profile.get("onboarding_completed", False),
                onboarding_stage="done" if profile.get("onboarding_completed") else "welcome",
                streak_days=profile.get("streak_days", 0),
            )
            session.add(student)
            await session.flush()

            for m in data.get("memories", []):
                session.add(
                    Memory(
                        student_id=student.id,
                        kind=m.get("kind", "note"),
                        content=m.get("content", ""),
                        importance=m.get("importance", 5),
                    )
                )
            for w in data.get("weak_areas", []):
                session.add(
                    WeakArea(
                        student_id=student.id,
                        subject=w.get("subject", ""),
                        chapter=w.get("chapter", ""),
                        sub_topic=w.get("sub_topic"),
                        weakness_type=w.get("weakness_type"),
                        severity=w.get("severity", 5),
                        confidence=w.get("confidence", 3),
                        notes=w.get("notes"),
                        resolved=w.get("resolved", False),
                    )
                )
            restored += 1

        if restored:
            logger.info("Restored %s student(s) from GitHub memory snapshots.", restored)
        return restored
