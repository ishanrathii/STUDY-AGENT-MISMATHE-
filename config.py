"""Centralized settings — env-driven, validated at startup."""
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")
    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field("claude-opus-4-8", alias="ANTHROPIC_MODEL")

    database_url: str = Field("sqlite+aiosqlite:///data/mismathe.db", alias="DATABASE_URL")
    timezone: str = Field("Asia/Kolkata", alias="TIMEZONE")
    default_mode: str = Field("friend", alias="DEFAULT_MODE")
    admin_user_id: int | None = Field(None, alias="ADMIN_USER_ID")


settings = Settings()  # type: ignore[call-arg]

# Ensure data directory exists for SQLite
(ROOT / "data").mkdir(parents=True, exist_ok=True)
