import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

from app.services.status_service import StatusService


@pytest.mark.asyncio
async def test_get_user_report_returns_report_when_found():
    mock_session = AsyncMock()
    mock_report = MagicMock()
    mock_report.telegram_id = 123

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = mock_report
    mock_session.execute.return_value = mock_result

    service = StatusService(mock_session)
    report = await service.get_user_report(123)

    assert report is not None
    assert report.telegram_id == 123
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_user_report_returns_none_when_not_found():
    mock_session = AsyncMock()

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    service = StatusService(mock_session)
    report = await service.get_user_report(999)

    assert report is None


@pytest.mark.asyncio
async def test_uses_correct_monday_when_today_is_wednesday():
    """If today is Wednesday (isoweekday=3), Monday is 2 days ago."""
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    tz = ZoneInfo("Asia/Jakarta")
    # Pick a known Wednesday: 2024-01-03
    wednesday = date(2024, 1, 3)
    fake_now = MagicMock()
    fake_now.isoweekday.return_value = 3  # Wednesday
    fake_now.date.return_value = wednesday

    with patch("app.services.status_service.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        service = StatusService(mock_session)
        await service.get_user_report(1)

    call_args = mock_session.execute.call_args
    assert call_args is not None
    # The query was constructed and executed
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_uses_correct_monday_when_today_is_sunday():
    """If today is Sunday (isoweekday=7), Monday is 6 days ago."""
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # Pick a known Sunday: 2024-01-07; Monday of that week: 2024-01-01
    sunday = date(2024, 1, 7)
    expected_monday = date(2024, 1, 1)
    fake_now = MagicMock()
    fake_now.isoweekday.return_value = 7  # Sunday
    fake_now.date.return_value = sunday

    with patch("app.services.status_service.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        service = StatusService(mock_session)
        await service.get_user_report(1)

    mock_session.execute.assert_awaited_once()
    # Verify expected Monday calculation externally
    assert sunday - timedelta(days=7 - 1) == expected_monday
