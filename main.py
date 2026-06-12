"""MISMATHE entry point — bootstraps DB, scheduler, and the Telegram bot."""
from __future__ import annotations

import asyncio
import logging

from mismathe.bot import build_application
from mismathe.db.database import init_db
from mismathe.services.scheduler import start_scheduler


logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("mismathe")


async def _startup(app) -> None:
    await init_db()
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
