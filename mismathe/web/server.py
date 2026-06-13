"""FastAPI app — chat UI + API for MISMATHE.

Identity model: each browser gets a signed `mismathe_uid` cookie holding a
random UUID. That UUID is the Student.external_id. No login, no password —
keep it personal.

Persistence:
- SQLite (live state, fast queries, conversation history)
- memory/ JSONL files (every chat turn, version-controlled in the repo)
- nightly push to GitHub (memory/ + conversations/)
"""
from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import Cookie, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from itsdangerous import BadSignature, URLSafeSerializer
from pydantic import BaseModel

from config import ROOT, settings
from mismathe.content.syllabus import CLASS_11_CHAPTERS, HIGH_PRIORITY_CHAPTERS, subjects
from mismathe.core.agent import respond_to_student
from mismathe.core.modes import get_mode, list_modes
from mismathe.db.database import get_session, init_db
from mismathe.db.models import Student
from mismathe.services.analytics import render_dashboard
from mismathe.services.conversations import log_turn
from mismathe.services.github_memory import restore_if_empty, sync_to_github
from mismathe.services.scheduler import start_scheduler, touch_streak
from mismathe.services.stopwatch import active_session, start_session, stop_active
from mismathe.services.test_engine import generate_test
from mismathe.utils.students import get_or_create_student
from mismathe.web.onboarding import (
    handle_onboarding_turn,
    intro_message,
)


logger = logging.getLogger(__name__)

COOKIE_NAME = "mismathe_uid"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365 * 5  # 5 years
WEB_DIR = ROOT / "web"

_signer = URLSafeSerializer(settings.session_secret, salt="mismathe-uid")


# ---------------------------------------------------------------------------
# Cookie identity
# ---------------------------------------------------------------------------

def _read_uid(raw_cookie: str | None) -> str | None:
    if not raw_cookie:
        return None
    try:
        return _signer.loads(raw_cookie)
    except BadSignature:
        return None


def _new_uid() -> str:
    return uuid.uuid4().hex


def _set_uid_cookie(response: Response, uid: str) -> None:
    signed = _signer.dumps(uid)
    response.set_cookie(
        COOKIE_NAME,
        signed,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
    )


async def _ensure_student(
    response: Response,
    raw_cookie: str | None,
) -> Student:
    uid = _read_uid(raw_cookie)
    if not uid:
        uid = _new_uid()
        _set_uid_cookie(response, uid)
    async with get_session() as session:
        student = await get_or_create_student(session, uid)
        return student


async def _load_student(uid: str) -> Student | None:
    async with get_session() as session:
        from sqlalchemy import select

        result = await session.execute(select(Student).where(Student.external_id == uid))
        return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    restored = await restore_if_empty()
    if restored:
        logger.info("Restored %s student(s) from GitHub snapshots.", restored)
    scheduler = start_scheduler()
    app.state.scheduler = scheduler
    logger.info("MISMATHE web is online on port %s.", settings.port)
    yield
    scheduler.shutdown(wait=False)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="MISMATHE", lifespan=lifespan)


# Pydantic request models
class ChatBody(BaseModel):
    message: str


class StudyStartBody(BaseModel):
    subject: str | None = None
    chapter: str | None = None


class ModeBody(BaseModel):
    mode: str


class TestBody(BaseModel):
    subject: str
    chapter: str | None = None
    difficulty: str = "medium"
    count: int = 10


# ---------------------------------------------------------------------------
# Static / index
# ---------------------------------------------------------------------------

@app.get("/")
async def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

@app.get("/api/state")
async def get_state(
    response: Response,
    mismathe_uid: str | None = Cookie(default=None),
):
    student = await _ensure_student(response, mismathe_uid)
    return {
        "external_id": student.external_id,
        "name": student.name,
        "onboarding_completed": student.onboarding_completed,
        "mentor_mode": student.mentor_mode,
        "streak_days": student.streak_days,
        "modes": [
            {"key": m.key, "label": m.label, "emoji": m.emoji, "description": m.description}
            for m in list_modes()
        ],
        # Intro message — frontend shows this on a brand-new session.
        "intro": intro_message() if not student.onboarding_completed else None,
    }


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

@app.post("/api/chat")
async def chat(
    body: ChatBody,
    response: Response,
    mismathe_uid: str | None = Cookie(default=None),
):
    student = await _ensure_student(response, mismathe_uid)
    user_text = (body.message or "").strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="empty message")

    # Mid-onboarding path
    if not student.onboarding_completed:
        async with get_session() as session:
            fresh = await get_or_create_student(session, student.external_id)
            reply = handle_onboarding_turn(fresh, user_text)
        # Log both turns to the repo too
        log_turn(external_id=student.external_id, role="user", content=user_text,
                 metadata={"phase": "onboarding"})
        log_turn(external_id=student.external_id, role="assistant", content=reply,
                 metadata={"phase": "onboarding"})
        return {"reply": reply, "onboarding": True}

    # Touch streak
    async with get_session() as session:
        fresh = await get_or_create_student(session, student.external_id)
        await touch_streak(fresh)
        student = fresh

    today_ctx = f"Date/time (UTC): {datetime.utcnow().isoformat()}"
    reply = await respond_to_student(student, user_text, today_context=today_ctx)

    log_turn(external_id=student.external_id, role="user", content=user_text)
    log_turn(external_id=student.external_id, role="assistant", content=reply)

    return {"reply": reply, "onboarding": False}


# ---------------------------------------------------------------------------
# Daily-flow commands (all route through the LLM, like the Telegram version)
# ---------------------------------------------------------------------------

async def _ai_command(student: Student, prompt: str, today_ctx: str | None = None) -> str:
    async with get_session() as session:
        fresh = await get_or_create_student(session, student.external_id)
        await touch_streak(fresh)
        student = fresh
    reply = await respond_to_student(student, prompt, today_context=today_ctx, persist=False)
    log_turn(external_id=student.external_id, role="assistant", content=reply,
             metadata={"phase": "command"})
    return reply


@app.post("/api/today")
async def today(response: Response, mismathe_uid: str | None = Cookie(default=None)):
    student = await _ensure_student(response, mismathe_uid)
    if not student.onboarding_completed:
        return {"reply": "Finish setup first — chat with me to get going."}
    prompt = (
        "Give the student their ONE most important task for today. "
        "Just ONE — to reduce overwhelm. Anchor it to a specific weak area "
        "or high-priority chapter from their profile. Be concrete: subject, "
        "chapter, time block, expected outcome. Under 100 words."
    )
    reply = await _ai_command(student, prompt, f"Date/time: {datetime.utcnow().isoformat()}")
    return {"reply": reply}


@app.post("/api/schedule")
async def schedule(response: Response, mismathe_uid: str | None = Cookie(default=None)):
    student = await _ensure_student(response, mismathe_uid)
    if not student.onboarding_completed:
        return {"reply": "Finish setup first."}
    prompt = (
        "Build a realistic study schedule for TODAY for this student. "
        "Consider school/coaching timings, energy patterns, sleep, and target hours. "
        "Hard subjects during peak focus, revision during low energy. "
        "Include breaks. End with the ONE highest-priority block. Bullet list with timings."
    )
    return {"reply": await _ai_command(student, prompt)}


@app.post("/api/checkin")
async def checkin(response: Response, mismathe_uid: str | None = Cookie(default=None)):
    student = await _ensure_student(response, mismathe_uid)
    if not student.onboarding_completed:
        return {"reply": "Finish setup first."}
    prompt = (
        "Run today's daily check-in. Ask the student warmly in ONE conversational message: "
        "(1) what did they study today, (2) productive hours, "
        "(3) what felt hard, (4) energy 1-10, "
        "(5) mood + stress + confidence. "
        "Tell them you'll record their answers as they reply naturally."
    )
    return {"reply": await _ai_command(student, prompt)}


@app.post("/api/revise")
async def revise(response: Response, mismathe_uid: str | None = Cookie(default=None)):
    student = await _ensure_student(response, mismathe_uid)
    if not student.onboarding_completed:
        return {"reply": "Finish setup first."}
    prompt = (
        "Pull together a 20-minute rapid revision session covering the student's top 2 "
        "weak areas. For each: (a) 3 key formulas/concepts, (b) 1 worked example, "
        "(c) 1 trick to remember. End with a single self-test question for each."
    )
    return {"reply": await _ai_command(student, prompt)}


@app.post("/api/weak")
async def weak(response: Response, mismathe_uid: str | None = Cookie(default=None)):
    student = await _ensure_student(response, mismathe_uid)
    if not student.onboarding_completed:
        return {"reply": "Finish setup first."}
    prompt = (
        "List the student's current tracked weak areas (from the system prompt context) "
        "with severity. Then suggest the top 3 to focus on this week. Bullet list."
    )
    return {"reply": await _ai_command(student, prompt)}


@app.post("/api/recover")
async def recover(response: Response, mismathe_uid: str | None = Cookie(default=None)):
    student = await _ensure_student(response, mismathe_uid)
    if not student.onboarding_completed:
        return {"reply": "Finish setup first."}
    async with get_session() as session:
        fresh = await get_or_create_student(session, student.external_id)
        fresh.mentor_mode = "recovery"
        student = fresh
    prompt = (
        "The student fell off track. Build a 7-day RECOVERY plan: "
        "Day 1-2 = tiny momentum, Day 3-5 = ramp to 60% on highest-priority weak areas, "
        "Day 6-7 = full schedule with 1 mock. NO guilt. Day-by-day bullet plan."
    )
    return {"reply": await _ai_command(student, prompt)}


@app.post("/api/news")
async def news(response: Response, mismathe_uid: str | None = Cookie(default=None)):
    student = await _ensure_student(response, mismathe_uid)
    if not student.onboarding_completed:
        return {"reply": "Finish setup first."}
    prompt = (
        "Give the student 3 bullet updates: "
        "(1) recent MHT-CET/HSC pattern news, "
        "(2) one motivating science/tech development, "
        "(3) one productivity insight. "
        "If you don't have recent news, give evergreen high-value updates and say so."
    )
    return {"reply": await _ai_command(student, prompt)}


# ---------------------------------------------------------------------------
# Mode
# ---------------------------------------------------------------------------

@app.post("/api/mode")
async def set_mode(
    body: ModeBody,
    response: Response,
    mismathe_uid: str | None = Cookie(default=None),
):
    student = await _ensure_student(response, mismathe_uid)
    mode = get_mode(body.mode)
    async with get_session() as session:
        fresh = await get_or_create_student(session, student.external_id)
        fresh.mentor_mode = mode.key
    return {
        "mode": mode.key,
        "label": mode.label,
        "emoji": mode.emoji,
        "description": mode.description,
    }


# ---------------------------------------------------------------------------
# Stopwatch
# ---------------------------------------------------------------------------

@app.post("/api/study/start")
async def study_start(
    body: StudyStartBody,
    response: Response,
    mismathe_uid: str | None = Cookie(default=None),
):
    student = await _ensure_student(response, mismathe_uid)
    async with get_session() as session:
        fresh = await get_or_create_student(session, student.external_id)
        await touch_streak(fresh)
        sess = await start_session(session, fresh.id, subject=body.subject, chapter=body.chapter)
        sess_id = sess.id
        subject = sess.subject
        chapter = sess.chapter
    return {"session_id": sess_id, "subject": subject, "chapter": chapter}


@app.post("/api/study/stop")
async def study_stop(
    response: Response,
    mismathe_uid: str | None = Cookie(default=None),
):
    student = await _ensure_student(response, mismathe_uid)
    async with get_session() as session:
        fresh = await get_or_create_student(session, student.external_id)
        sess = await stop_active(session, fresh.id)
    if sess is None:
        return {"active": False}
    return {
        "active": True,
        "session_id": sess.id,
        "duration_minutes": sess.duration_minutes,
        "subject": sess.subject,
        "chapter": sess.chapter,
    }


@app.get("/api/study/active")
async def study_active(
    response: Response,
    mismathe_uid: str | None = Cookie(default=None),
):
    student = await _ensure_student(response, mismathe_uid)
    async with get_session() as session:
        sess = await active_session(session, student.id)
    if sess is None:
        return {"active": False}
    return {
        "active": True,
        "started_at": sess.started_at.isoformat() + "Z",
        "subject": sess.subject,
        "chapter": sess.chapter,
    }


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.get("/api/dashboard")
async def dashboard(
    response: Response,
    mismathe_uid: str | None = Cookie(default=None),
):
    student = await _ensure_student(response, mismathe_uid)
    async with get_session() as session:
        fresh = await get_or_create_student(session, student.external_id)
        await touch_streak(fresh)
        text = await render_dashboard(session, fresh.id, fresh.streak_days)
    return {"reply": text}


# ---------------------------------------------------------------------------
# Test generation
# ---------------------------------------------------------------------------

@app.post("/api/test")
async def make_test(
    body: TestBody,
    response: Response,
    mismathe_uid: str | None = Cookie(default=None),
):
    student = await _ensure_student(response, mismathe_uid)
    test_text = await generate_test(
        subject=body.subject,
        chapter=body.chapter,
        test_type="chapter" if body.chapter else "mock",
        difficulty=body.difficulty,
        count=body.count,
    )
    log_turn(external_id=student.external_id, role="assistant", content=test_text,
             metadata={"phase": "test", "subject": body.subject, "chapter": body.chapter})
    return {"reply": test_text}


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

@app.post("/api/sync")
async def sync():
    ok = await sync_to_github()
    return {"ok": ok}


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "mismathe", "model": settings.anthropic_model}


# ---------------------------------------------------------------------------
# Syllabus
# ---------------------------------------------------------------------------

@app.get("/api/syllabus")
async def syllabus():
    """Return the full chapter list per subject with marks weightage."""
    return {
        "subjects": subjects(),
        "chapters": CLASS_11_CHAPTERS,
        "priority": HIGH_PRIORITY_CHAPTERS,
    }


# Friendly error JSON
@app.exception_handler(500)
async def _internal_error(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"error": "internal_error"})
