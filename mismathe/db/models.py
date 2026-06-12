"""SQLAlchemy ORM models — students, sessions, weak areas, tests, conversations."""
from __future__ import annotations

from datetime import datetime, date

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Student(Base):
    """Core student profile — accumulated through onboarding and check-ins."""

    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # external_id: opaque per-browser identifier (cookie UUID). One student per browser.
    external_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    display_handle: Mapped[str | None] = mapped_column(String(64))
    name: Mapped[str | None] = mapped_column(String(120))

    # Academic profile
    standard: Mapped[str] = mapped_column(String(16), default="11")
    current_percentage: Mapped[float | None] = mapped_column(Float)
    target_percentage: Mapped[float] = mapped_column(Float, default=90.0)

    # Routine
    school_timing: Mapped[str | None] = mapped_column(String(120))
    coaching_timing: Mapped[str | None] = mapped_column(String(120))
    daily_study_hours_target: Mapped[float | None] = mapped_column(Float)
    sleep_schedule: Mapped[str | None] = mapped_column(String(120))

    # Strengths / weaknesses (free-text, AI-curated)
    strong_subjects: Mapped[str | None] = mapped_column(Text)
    weak_subjects: Mapped[str | None] = mapped_column(Text)
    fear_areas: Mapped[str | None] = mapped_column(Text)
    learning_style: Mapped[str | None] = mapped_column(String(120))

    # Psychology
    confidence_level: Mapped[int | None] = mapped_column(Integer)  # 1-10
    stress_level: Mapped[int | None] = mapped_column(Integer)  # 1-10
    focus_level: Mapped[int | None] = mapped_column(Integer)  # 1-10
    motivation_level: Mapped[int | None] = mapped_column(Integer)  # 1-10
    phone_usage_hours: Mapped[float | None] = mapped_column(Float)
    social_media_addiction: Mapped[int | None] = mapped_column(Integer)  # 1-10

    # Operational
    mentor_mode: Mapped[str] = mapped_column(String(20), default="friend")
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    onboarding_stage: Mapped[str] = mapped_column(String(40), default="welcome")

    # Streak
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    last_active_date: Mapped[date | None] = mapped_column(Date)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    weak_areas: Mapped[list["WeakArea"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    study_sessions: Mapped[list["StudySession"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    checkins: Mapped[list["DailyCheckin"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    tests: Mapped[list["TestAttempt"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    memories: Mapped[list["Memory"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    messages: Mapped[list["ConversationMessage"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    revision_items: Mapped[list["RevisionItem"]] = relationship(back_populates="student", cascade="all, delete-orphan")


class WeakArea(Base):
    """Micro-weakness — concept / formula / sub-topic level, not just chapter."""

    __tablename__ = "weak_areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)

    subject: Mapped[str] = mapped_column(String(40))  # Physics / Chemistry / Math
    chapter: Mapped[str] = mapped_column(String(120))
    sub_topic: Mapped[str | None] = mapped_column(String(200))
    weakness_type: Mapped[str | None] = mapped_column(String(60))  # concept | formula | speed | application

    severity: Mapped[int] = mapped_column(Integer, default=5)  # 1-10
    confidence: Mapped[int] = mapped_column(Integer, default=3)  # 1-10
    notes: Mapped[str | None] = mapped_column(Text)

    last_practiced_at: Mapped[datetime | None] = mapped_column(DateTime)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    student: Mapped[Student] = relationship(back_populates="weak_areas")


class StudySession(Base):
    """A single study stopwatch session — used for productivity analytics."""

    __tablename__ = "study_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)

    subject: Mapped[str | None] = mapped_column(String(40))
    chapter: Mapped[str | None] = mapped_column(String(120))
    activity: Mapped[str] = mapped_column(String(40), default="study")  # study | revision | mock | doubt

    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)

    focus_quality: Mapped[int | None] = mapped_column(Integer)  # 1-10, asked post-session
    notes: Mapped[str | None] = mapped_column(Text)
    distractions: Mapped[int] = mapped_column(Integer, default=0)

    student: Mapped[Student] = relationship(back_populates="study_sessions")


class DailyCheckin(Base):
    """End-of-day check-in for mood, energy, productivity."""

    __tablename__ = "daily_checkins"
    __table_args__ = (UniqueConstraint("student_id", "checkin_date", name="uq_student_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)

    checkin_date: Mapped[date] = mapped_column(Date, default=date.today)

    what_studied: Mapped[str | None] = mapped_column(Text)
    productive_hours: Mapped[float | None] = mapped_column(Float)
    difficult_topics: Mapped[str | None] = mapped_column(Text)
    revised: Mapped[bool] = mapped_column(Boolean, default=False)

    energy_level: Mapped[int | None] = mapped_column(Integer)  # 1-10
    mood: Mapped[int | None] = mapped_column(Integer)  # 1-10
    confidence: Mapped[int | None] = mapped_column(Integer)
    stress: Mapped[int | None] = mapped_column(Integer)
    distractions: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    student: Mapped[Student] = relationship(back_populates="checkins")


class TestAttempt(Base):
    """Record of a generated and attempted test."""

    __tablename__ = "test_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)

    test_type: Mapped[str] = mapped_column(String(40))  # chapter | weak | mock | speed | formula
    subject: Mapped[str | None] = mapped_column(String(40))
    chapter: Mapped[str | None] = mapped_column(String(120))
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")  # easy | medium | hard | cet

    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    correct: Mapped[int] = mapped_column(Integer, default=0)
    incorrect: Mapped[int] = mapped_column(Integer, default=0)
    skipped: Mapped[int] = mapped_column(Integer, default=0)
    accuracy: Mapped[float | None] = mapped_column(Float)
    time_taken_minutes: Mapped[float | None] = mapped_column(Float)

    weak_topics_identified: Mapped[str | None] = mapped_column(Text)
    feedback: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    student: Mapped[Student] = relationship(back_populates="tests")


class Memory(Base):
    """Long-term memory — emotional patterns, breakthroughs, fears, milestones."""

    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)

    kind: Mapped[str] = mapped_column(String(40))  # emotional | breakthrough | fear | milestone | habit
    content: Mapped[str] = mapped_column(Text)
    importance: Mapped[int] = mapped_column(Integer, default=5)  # 1-10
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    student: Mapped[Student] = relationship(back_populates="memories")


class ConversationMessage(Base):
    """Short-term conversation log — the last ~50 turns are sent back to Claude."""

    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)

    role: Mapped[str] = mapped_column(String(16))  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    student: Mapped[Student] = relationship(back_populates="messages")


class RevisionItem(Base):
    """Spaced-repetition card — concept / formula scheduled for next review."""

    __tablename__ = "revision_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)

    subject: Mapped[str] = mapped_column(String(40))
    chapter: Mapped[str] = mapped_column(String(120))
    topic: Mapped[str] = mapped_column(String(200))
    content: Mapped[str | None] = mapped_column(Text)

    ease: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=1)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)

    due_date: Mapped[date] = mapped_column(Date, default=date.today)
    last_reviewed: Mapped[datetime | None] = mapped_column(DateTime)

    student: Mapped[Student] = relationship(back_populates="revision_items")
