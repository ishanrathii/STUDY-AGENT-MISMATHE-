"""Centralized settings — env-driven, validated at startup."""
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = Field("", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field("claude-opus-4-8", alias="ANTHROPIC_MODEL")

    database_url: str = Field("sqlite+aiosqlite:///data/mismathe.db", alias="DATABASE_URL")
    timezone: str = Field("Asia/Kolkata", alias="TIMEZONE")
    default_mode: str = Field("friend", alias="DEFAULT_MODE")

    # Web server
    host: str = Field("0.0.0.0", alias="HOST")
    port: int = Field(8000, alias="PORT")
    session_secret: str = Field(
        "mismathe-change-me-in-production-please-make-this-random",
        alias="SESSION_SECRET",
    )

    # GitHub memory sync — push memory/ + conversations/ snapshots to GitHub.
    github_memory_sync: bool = Field(True, alias="GITHUB_MEMORY_SYNC")
    git_branch: str = Field("", alias="GIT_BRANCH")  # empty = current branch


settings = Settings()  # type: ignore[call-arg]

# Ensure data + memory directories exist
(ROOT / "data").mkdir(parents=True, exist_ok=True)
(ROOT / "memory").mkdir(parents=True, exist_ok=True)
(ROOT / "memory" / "conversations").mkdir(parents=True, exist_ok=True)
