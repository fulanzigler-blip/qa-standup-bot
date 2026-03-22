import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes

from app.bot.handlers.remind_handler import remind_command

@pytest.fixture
def update():
    u = Update(1)
    u.effective_user = MagicMock(id=12345, first_name="Test")
    u.message = MagicMock()
    u.message.reply_text = AsyncMock()
    return u

@pytest.fixture
def context():
    c = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    c.bot = MagicMock()
    c.bot.send_message = AsyncMock()
    return c

@pytest.mark.asyncio
async def test_unauthorized_user(update, context):
    """Test that non-QA Leads are rejected."""
    # Set env var to NOT include user ID 12345
    with patch.dict(os.environ, {"QA_LEAD_IDS": "99999"}):
        await remind_command(update, context)

    update.message.reply_text.assert_called_once()
    args = update.message.reply_text.call_args[0][0]
    assert "permission" in args.lower()

@pytest.mark.asyncio
@patch("app.bot.handlers.remind_handler.get_db")
@patch("app.bot.handlers.remind_handler.ReminderService")
async def test_authorized_user_success(mock_service_class, mock_get_db, update, context):
    """Test successful execution by QA Lead."""
    # Mock Env
    with patch.dict(os.environ, {"QA_LEAD_IDS": "12345"}):
        # Mock DB Session
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db]) # generator behavior

        # Mock Service behavior
        mock_instance = MagicMock()
        mock_instance.get_iso_monday.return_value = "2023-01-01"
        mock_instance.get_missing_squads.return_value = [] # All submitted
        mock_service_class.return_value = mock_instance

        await remind_command(update, context)

        # Verify service was initialized with DB and Bot
        mock_service_class.assert_called_once_with(mock_db, context.bot)

        # Verify logic path
        mock_instance.get_missing_squads.assert_called_once()

        # Verify response
        update.message.reply_text.assert_called_once()
        response = update.message.reply_text.call_args[0][0]
        assert "No reminders needed" in response or "All squads" in response
