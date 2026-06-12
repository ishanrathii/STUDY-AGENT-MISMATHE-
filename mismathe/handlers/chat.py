"""Free-form chat handler — fallback when no command matches.

Routes the message to MISMATHE if onboarding is done; otherwise delegates
to the onboarding flow.
"""
from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from mismathe.core.agent import respond_to_student
from mismathe.db.database import get_session
from mismathe.handlers.onboarding import maybe_handle_onboarding
from mismathe.services.scheduler import touch_streak
from mismathe.utils.students import get_or_create_student


logger = logging.getLogger(__name__)


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text or not update.effective_user:
        return

    # Mid-onboarding capture
    if await maybe_handle_onboarding(update, ctx):
        return

    text = update.message.text

    async with get_session() as session:
        student = await get_or_create_student(session, update.effective_user)
        await touch_streak(student)

    try:
        await ctx.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    except Exception:  # noqa: BLE001
        pass

    reply = await respond_to_student(student, text)
    await update.message.reply_text(reply)
