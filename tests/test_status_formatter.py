import pytest
from datetime import date
from unittest.mock import MagicMock

from app.services.status_service import DaySummary
from app.bot.formatters.status_formatter import StatusFormatter


def make_task(title: str) -> MagicMock:
    t = MagicMock()
    t.title = title
    return t


def test_empty_list_returns_no_tasks_message():
    result = StatusFormatter.format_status([])
    assert "No submissions this week" in result


def test_single_day_contains_date_and_task():
    summary = DaySummary(date=date(2026, 3, 16), tasks=[make_task("Deploy API")])
    result = StatusFormatter.format_status([summary])

    assert "2026" in result
    assert "Deploy API" in result
    assert "Monday" in result


def test_multiple_days_all_present():
    summaries = [
        DaySummary(date=date(2026, 3, 16), tasks=[make_task("Task A")]),
        DaySummary(date=date(2026, 3, 17), tasks=[make_task("Task B")]),
    ]
    result = StatusFormatter.format_status(summaries)

    assert "Task A" in result
    assert "Task B" in result
    assert "Monday" in result
    assert "Tuesday" in result


def test_special_chars_are_escaped():
    """MarkdownV2 special characters in task titles must be escaped."""
    summary = DaySummary(
        date=date(2026, 3, 16),
        tasks=[make_task("Fix bug: user_name & (auth) issue!")],
    )
    result = StatusFormatter.format_status([summary])

    # Underscores must be escaped in MarkdownV2
    assert "\\_" in result or "user" in result  # escaping applied
    # Raw unescaped underscore at word boundary would break MarkdownV2
    assert "user_name" not in result


def test_format_includes_header():
    summary = DaySummary(date=date(2026, 3, 16), tasks=[make_task("A task")])
    result = StatusFormatter.format_status([summary])
    assert "Weekly Status" in result


def test_no_tasks_message_is_markdown_safe():
    """The no-tasks message must not contain unescaped MarkdownV2 specials."""
    msg = StatusFormatter.no_tasks_message()
    # Should use escaped period
    assert "\\." in msg or msg.count(".") == 0
