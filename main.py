"""MISMATHE entry point — bootstraps DB, scheduler, and the Telegram bot."""
from __future__ import annotations

import asyncio
import logging

from mismathe.bot import build_application
from mismathe.db.database import init_db
from mismathe.services.github_memory import restore_if_empty
from mismathe.services.scheduler import start_scheduler


logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("mismathe")


async def _startup(app) -> None:
    await init_db()
    restored = await restore_if_empty()
    if restored:
        logger.info("Memory restored from GitHub snapshots for %s student(s).", restored)
    start_scheduler(app)
    logger.info("MISMATHE is online.")


def main() -> None:
    application = build_application()
    application.post_init = _startup
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown requested. Bye.")
