import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from telegram import Update, Message, Chat, User
from telegram.ext import ContextTypes

from app.bot.handlers.status_handler import StatusHandler
from app.bot.formatters.status_formatter import StatusFormatter


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


def make_session_factory(report=None):
    session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = report
    session.execute.return_value = mock_result

    factory = MagicMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=session)
    factory.return_value.__aexit__ = AsyncMock(return_value=False)
    return factory


@pytest.mark.asyncio
async def test_private_chat_sends_status_directly():
    """Private chat: status text sent directly to the chat."""
    mock_report = MagicMock()
    mock_report.review_status = "pending"
    mock_report.report_date = date(2024, 1, 1)
    mock_report.created_at = None
    mock_report.ai_analysis = ["Deploy service", "Write unit tests"]

    session_factory = make_session_factory(report=mock_report)
    update = make_update(Chat.PRIVATE, user_id=42)
    context = make_context()

    handler = StatusHandler(session_factory)
    await handler.handle(update, context)

    update.effective_message.reply_text.assert_awaited_once()
    args, kwargs = update.effective_message.reply_text.call_args
    assert kwargs.get("parse_mode") == "MarkdownV2"
    # Should NOT DM the user
    context.bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_group_chat_acknowledges_and_dms_user():
    """Group chat: acknowledge in group, send status via DM."""
    mock_report = MagicMock()
    mock_report.review_status = "approved"
    mock_report.report_date = date(2024, 1, 1)
    mock_report.created_at = None
    mock_report.ai_analysis = ["Fix login bug"]

    session_factory = make_session_factory(report=mock_report)
    update = make_update(Chat.SUPERGROUP, user_id=42)
    context = make_context()

    handler = StatusHandler(session_factory)
    await handler.handle(update, context)

    # Group gets the acknowledge message
    update.effective_message.reply_text.assert_awaited_once()
    group_args, group_kwargs = update.effective_message.reply_text.call_args
    assert "DM" in group_args[0] or "Direct Messages" in group_args[0]

    # User gets DM
    context.bot.send_message.assert_awaited_once_with(
        chat_id=42,
        text=pytest.approx(StatusFormatter.format_status(mock_report), rel=1e-3),
        parse_mode="MarkdownV2",
    )


@pytest.mark.asyncio
async def test_no_tasks_returns_no_tasks_message():
    """When service returns None, the no-tasks message is sent."""
    session_factory = make_session_factory(report=None)
    update = make_update(Chat.PRIVATE, user_id=7)
    context = make_context()

    handler = StatusHandler(session_factory)
    await handler.handle(update, context)

    update.effective_message.reply_text.assert_awaited_once()
    args, _ = update.effective_message.reply_text.call_args
    assert "haven" in args[0] or "No" in args[0]


@pytest.mark.asyncio
async def test_db_error_returns_user_friendly_error():
    """When DB raises an exception, a friendly error message is returned."""
    factory = MagicMock()
    session = AsyncMock()
    session.execute.side_effect = Exception("DB connection timeout")
    factory.return_value.__aenter__ = AsyncMock(return_value=session)
    factory.return_value.__aexit__ = AsyncMock(return_value=False)

    update = make_update(Chat.PRIVATE, user_id=5)
    context = make_context()

    handler = StatusHandler(factory)
    await handler.handle(update, context)

    update.effective_message.reply_text.assert_awaited_once()
    args, _ = update.effective_message.reply_text.call_args
    assert "couldn" in args[0] or "Sorry" in args[0]
