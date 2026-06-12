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

    # Privacy lock — comma-separated Telegram user ids allowed to use the bot.
    # Empty = open to anyone who finds the bot.
    allowed_user_ids_raw: str = Field("", alias="ALLOWED_USER_IDS")

    # GitHub memory sync — export memory/ JSON snapshots and git push them.
    github_memory_sync: bool = Field(True, alias="GITHUB_MEMORY_SYNC")
    git_branch: str = Field("", alias="GIT_BRANCH")  # empty = current branch

    @property
    def allowed_user_ids(self) -> set[int]:
        raw = self.allowed_user_ids_raw.replace(";", ",")
        return {int(x) for x in (p.strip() for p in raw.split(",")) if x.isdigit()}


settings = Settings()  # type: ignore[call-arg]

# Ensure data directory exists for SQLite
(ROOT / "data").mkdir(parents=True, exist_ok=True)
