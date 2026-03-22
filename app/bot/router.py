from telegram.ext import Application, CommandHandler

from app.bot.handlers.status_handler import StatusHandler


def setup_router(application: Application, session_factory) -> None:
    """Registers all bot command handlers with the application."""
    status_handler = StatusHandler(session_factory)
    application.add_handler(CommandHandler("status", status_handler.handle))
