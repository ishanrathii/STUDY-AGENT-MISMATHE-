"""Telegram bot wiring — registers all command + message handlers."""
from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import settings
from mismathe.handlers import commands
from mismathe.handlers.chat import handle_message


logger = logging.getLogger(__name__)


async def _on_error(update: object, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Update %s caused error: %s", update, ctx.error, exc_info=ctx.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "Something glitched on my side. Try again in a moment — I'm still here."
            )
        except Exception:  # noqa: BLE001
            pass


def build_application() -> Application:
    app = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .concurrent_updates(True)
        .build()
    )

    app.add_handler(CommandHandler("start", commands.cmd_start))
    app.add_handler(CommandHandler("help", commands.cmd_help))
    app.add_handler(CommandHandler("today", commands.cmd_today))
    app.add_handler(CommandHandler("schedule", commands.cmd_schedule))
    app.add_handler(CommandHandler("study", commands.cmd_study))
    app.add_handler(CommandHandler("stop", commands.cmd_stop))
    app.add_handler(CommandHandler("checkin", commands.cmd_checkin))
    app.add_handler(CommandHandler("test", commands.cmd_test))
    app.add_handler(CommandHandler("weak", commands.cmd_weak))
    app.add_handler(CommandHandler("revise", commands.cmd_revise))
    app.add_handler(CommandHandler("mode", commands.cmd_mode))
    app.add_handler(CommandHandler("dashboard", commands.cmd_dashboard))
    app.add_handler(CommandHandler("recover", commands.cmd_recover))
    app.add_handler(CommandHandler("news", commands.cmd_news))
    app.add_handler(CommandHandler("puzzle", commands.cmd_puzzle))
    app.add_handler(CommandHandler("movie", commands.cmd_movie))
    app.add_handler(CommandHandler("priority", commands.cmd_priority))

    app.add_handler(CallbackQueryHandler(commands.on_mode_callback, pattern=r"^mode:"))
    app.add_handler(CallbackQueryHandler(commands.on_test_callback, pattern=r"^test:"))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.add_error_handler(_on_error)

    return app
