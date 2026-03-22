import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update, Message, Chat, User
from telegram.ext import ContextTypes

from app.bot.handlers.status_handler import StatusHandler
from app.bot.formatters.status_formatter import StatusFormatter
from app.services.status_service import DaySummary


def make_task(title: str) -> MagicMock:
    t = MagicMock()
    t.title = title
    return t


def make_update(chat_type: str, user_id: int = 42) -> Update:
    user = MagicMock(spec=User)
    user.id = user_id

    chat = MagicMock(spec=Chat)
    chat.type = chat_type

    message = MagicMock(spec=Message)
    message.reply_text = AsyncMock()

    update = MagicMock(spec=Update)
    update.effective_user = user
    update.effective_chat = chat
    update.effective_message = message
    return update


def make_context() -> ContextTypes.DEFAULT_TYPE:
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = AsyncMock()
    context.bot.send_message = AsyncMock()
    return context


def make_session_factory(day_summaries=None):
    session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result

    factory = MagicMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=session)
    factory.return_value.__aexit__ = AsyncMock(return_value=False)

    # Patch StatusService.get_user_weekly_tasks to return desired summaries
    factory._day_summaries = day_summaries if day_summaries is not None else []
    return factory


@pytest.mark.asyncio
async def test_private_chat_sends_status_directly():
    """Private chat: status sent directly without DM."""
    summaries = [DaySummary(date=date(2026, 3, 16), tasks=[make_task("Task A")])]
    factory = make_session_factory()

    with patch("app.services.status_service.StatusService.get_user_weekly_tasks",
               new=AsyncMock(return_value=summaries)):
        handler = StatusHandler(factory)
        update = make_update(Chat.PRIVATE, user_id=42)
        context = make_context()
        await handler.handle(update, context)

    update.effective_message.reply_text.assert_awaited_once()
    _, kwargs = update.effective_message.reply_text.call_args
    assert kwargs.get("parse_mode") == "MarkdownV2"
    context.bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_group_chat_acknowledges_and_dms_user():
    """Group chat: ack in group, full status sent via DM."""
    summaries = [DaySummary(date=date(2026, 3, 16), tasks=[make_task("Fix bug")])]
    factory = make_session_factory()

    with patch("app.services.status_service.StatusService.get_user_weekly_tasks",
               new=AsyncMock(return_value=summaries)):
        handler = StatusHandler(factory)
        update = make_update(Chat.SUPERGROUP, user_id=42)
        context = make_context()
        await handler.handle(update, context)

    update.effective_message.reply_text.assert_awaited_once()
    args, _ = update.effective_message.reply_text.call_args
    assert "Direct Messages" in args[0] or "DM" in args[0]

    context.bot.send_message.assert_awaited_once()
    _, dm_kwargs = context.bot.send_message.call_args
    assert dm_kwargs.get("chat_id") == 42


@pytest.mark.asyncio
async def test_no_tasks_returns_no_tasks_message():
    """Empty summaries: the no-tasks message is sent."""
    factory = make_session_factory()

    with patch("app.services.status_service.StatusService.get_user_weekly_tasks",
               new=AsyncMock(return_value=[])):
        handler = StatusHandler(factory)
        update = make_update(Chat.PRIVATE, user_id=7)
        context = make_context()
        await handler.handle(update, context)

    update.effective_message.reply_text.assert_awaited_once()
    args, _ = update.effective_message.reply_text.call_args
    assert "No submissions" in args[0] or "haven" in args[0]


@pytest.mark.asyncio
async def test_db_error_returns_user_friendly_error():
    """DB exception: friendly error message sent to user."""
    factory = MagicMock()
    session = AsyncMock()
    session.execute.side_effect = Exception("DB timeout")
    factory.return_value.__aenter__ = AsyncMock(return_value=session)
    factory.return_value.__aexit__ = AsyncMock(return_value=False)

    handler = StatusHandler(factory)
    update = make_update(Chat.PRIVATE, user_id=5)
    context = make_context()
    await handler.handle(update, context)

    update.effective_message.reply_text.assert_awaited_once()
    args, _ = update.effective_message.reply_text.call_args
    assert "couldn" in args[0] or "Sorry" in args[0]
