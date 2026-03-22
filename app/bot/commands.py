from typing import List

from telegram import BotCommand
from telegram.ext import Application

COMMANDS: List[BotCommand] = [
    BotCommand("status", "Check your submitted tasks for this week"),
]


async def register_commands(application: Application) -> None:
    """
    Registers the defined commands with Telegram so they appear in the bot menu.
    """
    await application.bot.set_my_commands(COMMANDS)
