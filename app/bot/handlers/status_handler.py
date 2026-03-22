import logging

from telegram import Update, Chat
from telegram.ext import ContextTypes

from app.services.status_service import StatusService
from app.bot.formatters.status_formatter import StatusFormatter

logger = logging.getLogger(__name__)


class StatusHandler:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_user or not update.effective_message:
            return

        telegram_id = update.effective_user.id
        chat_type = update.effective_chat.type
        is_private = chat_type == Chat.PRIVATE

        try:
            async with self.session_factory() as session:
                service = StatusService(session)
                day_summaries = await service.get_user_weekly_tasks(telegram_id)
                status_text = StatusFormatter.format_status(day_summaries)

            if is_private:
                await update.effective_message.reply_text(
                    status_text, parse_mode="MarkdownV2"
                )
            else:
                # ADR: In group chats, acknowledge publicly and DM the result
                await update.effective_message.reply_text(
                    StatusFormatter.group_acknowledge_message(),
                    parse_mode="MarkdownV2",
                )
                try:
                    await context.bot.send_message(
                        chat_id=telegram_id,
                        text=status_text,
                        parse_mode="MarkdownV2",
                    )
                except Exception as dm_error:
                    logger.warning("Failed to DM user %s: %s", telegram_id, dm_error)
                    await update.effective_message.reply_text(
                        "I couldn't send you a DM\\. Please start a private chat with me first\\.",
                        parse_mode="MarkdownV2",
                    )

        except Exception:
            logger.exception("Error processing /status for user %s", telegram_id)
            await update.effective_message.reply_text(
                StatusFormatter.error_message(), parse_mode="MarkdownV2"
            )
