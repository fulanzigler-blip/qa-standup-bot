import os
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo

TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "Asia/Jakarta"))


def get_current_week_range() -> tuple[date, date]:
    """
    Returns (monday, sunday) of the current week in Asia/Jakarta timezone.
    Uses isoweekday() so Monday=1, Sunday=7.
    """
    today = datetime.now(tz=TIMEZONE).date()
    monday = today - timedelta(days=today.isoweekday() - 1)
    sunday = monday + timedelta(days=6)
    return monday, sunday
