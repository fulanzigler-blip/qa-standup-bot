"""
Handler for the /remind slash command.
Restricted to QA Leads.
"""
import os
import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes

from app.services.reminder_service import ReminderService
from app.bot.formatters.reminder_formatter import format_lead_summary
from app.db.session import get_db

logger = logging.getLogger(__name__)

QA_LEAD_IDS = set(int(uid) for uid in os.getenv("QA_LEAD_IDS", "").split(",") if uid.strip())

async def remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /remind command handler.
    Identifies squads missing updates and sends reminders.
    """
    user_id = update.effective_user.id

    # 1. Authorization Check
    if user_id not in QA_LEAD_IDS:
        await update.message.reply_text("⛔ You do not have permission to use this command.")
        return

    # 2. Initialize Service
    # Note: We need a DB session and a bot instance.
    # We fetch the bot instance from context.bot if compatible, or pass it.
    # Assuming context.bot is the standard python-telegram-bot application instance.

    # We need to manage the DB session lifecycle carefully in a handler.
    db_gen = get_db()
    db = next(db_gen)

    try:
        # Assuming ReminderService expects a bot instance with async send_message
        # We wrap context.bot if necessary or pass it directly
        service = ReminderService(db, context.bot)

        # 3. Identify Missing Squads
        missing_squads = service.get_missing_squads(service.get_iso_monday())

        if not missing_squads:
            await update.message.reply_text(format_lead_summary([]))
            return

        # 4. Send Reminders
        success_names, failed_names = await service.send_reminders(missing_squads, user_id)

        # 5. Report Summary to Lead
        response_text = format_lead_summary(success_names, failed_names)
        await update.message.reply_text(response_text, parse_mode="Markdown")

    except Exception as e:
        logger.exception("Error during /remind execution")
        await update.message.reply_text("❌ An error occurred while processing reminders. Please check logs.")
    finally:
        db.close()
