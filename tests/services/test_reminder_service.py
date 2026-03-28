import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, MagicMock, patch

from app.db.base import Base
from app.models.squad import Squad, SquadMember, ReminderLog
from app.models.weekly_report import WeeklyReport
from app.services.reminder_service import ReminderService

# Setup in-memory DB
ENGINE = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=ENGINE)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=ENGINE)

@pytest.fixture
def mock_bot():
    bot = MagicMock()
    bot.send_message = AsyncMock()
    return bot

def test_get_iso_monday():
    service = ReminderService(None, None) # DB not needed for this specific method
    today = date.today()
    expected_monday = today - timedelta(days=today.weekday())
    assert service.get_iso_monday() == expected_monday

def test_get_missing_squads_all_submitted(db, mock_bot):
    """
    Scenario: 2 Squads. All members submitted.
    Expected: Empty list.
    """
    # Setup Data
    week_date = date(2023, 10, 23) # Monday

    squad1 = Squad(name="Alpha", telegram_chat_id=100)
    squad2 = Squad(name="Beta", telegram_chat_id=200)
    db.add_all([squad1, squad2])
    db.commit()

    member1 = SquadMember(squad_id=squad1.id, telegram_id=1001)
    member2 = SquadMember(squad_id=squad2.id, telegram_id=2001)
    db.add_all([member1, member2])
    db.commit()

    # Add reports
    report1 = WeeklyReport(telegram_id=1001, report_date=week_date, content="Done")
    report2 = WeeklyReport(telegram_id=2001, report_date=week_date, content="Done")
    db.add_all([report1, report2])
    db.commit()

    service = ReminderService(db, mock_bot)
    missing = service.get_missing_squads(week_date)

    assert len(missing) == 0

def test_get_missing_squads_partial_submission(db, mock_bot):
    """
    Scenario: Squad has 2 members, 1 submitted.
    Expected: Squad is in missing list (as per tech spec: ANY member missing).
    """
    week_date = date(2023, 10, 23)

    squad = Squad(name="Gamma", telegram_chat_id=300)
    db.add(squad)
    db.commit()

    mem1 = SquadMember(squad_id=squad.id, telegram_id=3001)
    mem2 = SquadMember(squad_id=squad.id, telegram_id=3002)
    db.add_all([mem1, mem2])
    db.commit()

    # Only mem1 submitted
    report = WeeklyReport(telegram_id=3001, report_date=week_date, content="Done")
    db.add(report)
    db.commit()

    service = ReminderService(db, mock_bot)
    missing = service.get_missing_squads(week_date)

    assert len(missing) == 1
    assert missing[0].name == "Gamma"

def test_idempotency(db, mock_bot):
    """
    Scenario: Squad missing, but already in ReminderLog for this week.
    Expected: Squad not returned in missing list.
    """
    week_date = date(2023, 10, 23)

    squad = Squad(name="Delta", telegram_chat_id=400)
    db.add(squad)
    db.commit()

    mem = SquadMember(squad_id=squad.id, telegram_id=4001)
    db.add(mem)
    db.commit()

    # Add reminder log (simulating previous run)
    log = ReminderLog(squad_id=squad.id, week_date=week_date, reminded_by_telegram_id=999)
    db.add(log)
    db.commit()

    service = ReminderService(db, mock_bot)
    missing = service.get_missing_squads(week_date)

    assert len(missing) == 0

@pytest.mark.asyncio
async def test_send_reminders_success(db, mock_bot):
    """
    Scenario: Send reminder to a squad with a chat ID.
    Expected: Message sent to chat, ReminderLog created.
    """
    week_date = date(2023, 10, 23)
    squad = Squad(name="Epsilon", telegram_chat_id=500)
    db.add(squad)
    db.commit()

    service = ReminderService(db, mock_bot)
    success, failed = await service.send_reminders([squad], actor_telegram_id=999)

    assert len(success) == 1
    assert "Epsilon" in success
    assert len(failed) == 0

    # Verify bot called
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    assert call_args[1]['chat_id'] == 500
    assert "Epsilon" in call_args[1]['text']

    # Verify Log
    log = db.query(ReminderLog).filter(ReminderLog.squad_id == squad.id).first()
    assert log is not None
    assert log.week_date == week_date

@pytest.mark.asyncio
async def test_send_reminders_fallback_dm(db, mock_bot):
    """
    Scenario: Squad has NO chat ID.
    Expected: Message sent to individual members.
    """
    week_date = date(2023, 10, 23)
    squad = Squad(name="Zeta", telegram_chat_id=None) # No group chat
    db.add(squad)
    db.commit()

    mem1 = SquadMember(squad_id=squad.id, telegram_id=6001)
    mem2 = SquadMember(squad_id=squad.id, telegram_id=6002)
    db.add_all([mem1, mem2])
    db.commit()

    service = ReminderService(db, mock_bot)
    success, failed = await service.send_reminders([squad], actor_telegram_id=999)

    assert len(success) == 1
    assert mock_bot.send_message.call_count == 2 # Called for each member

    # Verify chat IDs used were the member IDs
    ids_called = [call[1]['chat_id'] for call in mock_bot.send_message.call_args_list]
    assert 6001 in ids_called
    assert 6002 in ids_called
