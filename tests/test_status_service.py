import pytest
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

from app.services.status_service import StatusService, DaySummary

TZ = ZoneInfo("Asia/Jakarta")


def make_task(title: str, created_at: datetime) -> MagicMock:
    task = MagicMock()
    task.title = title
    task.description = ""
    task.created_at = created_at
    return task


@pytest.mark.asyncio
async def test_no_tasks_returns_empty_list():
    """When no tasks exist for the user this week, returns an empty list."""
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    service = StatusService(mock_session)
    result = await service.get_user_weekly_tasks(telegram_id=999)

    assert result == []
    mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_tasks_present_returns_day_summaries():
    """Tasks are grouped into DaySummary objects by local Jakarta date."""
    monday = datetime(2026, 3, 16, 9, 0, 0, tzinfo=TZ)   # Monday
    tuesday = datetime(2026, 3, 17, 10, 0, 0, tzinfo=TZ)  # Tuesday

    task_mon = make_task("Deploy API", monday)
    task_tue = make_task("Write tests", tuesday)

    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = [task_mon, task_tue]
    mock_session.execute.return_value = mock_result

    service = StatusService(mock_session)

    with patch("app.services.status_service.get_current_week_range") as mock_range:
        mock_range.return_value = (date(2026, 3, 16), date(2026, 3, 22))
        result = await service.get_user_weekly_tasks(telegram_id=42)

    assert len(result) == 2
    assert result[0].date == date(2026, 3, 16)
    assert len(result[0].tasks) == 1
    assert result[0].tasks[0].title == "Deploy API"

    assert result[1].date == date(2026, 3, 17)
    assert len(result[1].tasks) == 1
    assert result[1].tasks[0].title == "Write tests"


@pytest.mark.asyncio
async def test_multiple_tasks_same_day_grouped_together():
    """Multiple tasks on the same day are placed in a single DaySummary."""
    monday = datetime(2026, 3, 16, 9, 0, 0, tzinfo=TZ)
    monday2 = datetime(2026, 3, 16, 14, 0, 0, tzinfo=TZ)

    tasks = [make_task("Task A", monday), make_task("Task B", monday2)]

    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = tasks
    mock_session.execute.return_value = mock_result

    service = StatusService(mock_session)

    with patch("app.services.status_service.get_current_week_range") as mock_range:
        mock_range.return_value = (date(2026, 3, 16), date(2026, 3, 22))
        result = await service.get_user_weekly_tasks(telegram_id=42)

    assert len(result) == 1
    assert result[0].date == date(2026, 3, 16)
    assert len(result[0].tasks) == 2


@pytest.mark.asyncio
async def test_days_sorted_ascending():
    """Returned DaySummary list is sorted by date ascending."""
    wednesday = datetime(2026, 3, 18, 10, 0, 0, tzinfo=TZ)
    monday = datetime(2026, 3, 16, 9, 0, 0, tzinfo=TZ)

    tasks = [make_task("Wed task", wednesday), make_task("Mon task", monday)]

    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = tasks
    mock_session.execute.return_value = mock_result

    service = StatusService(mock_session)

    with patch("app.services.status_service.get_current_week_range") as mock_range:
        mock_range.return_value = (date(2026, 3, 16), date(2026, 3, 22))
        result = await service.get_user_weekly_tasks(telegram_id=42)

    dates = [s.date for s in result]
    assert dates == sorted(dates)
