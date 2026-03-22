import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.utils.week import get_current_week_range

TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "Asia/Jakarta"))


@dataclass
class DaySummary:
    date: date
    tasks: list = field(default_factory=list)


class StatusService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_weekly_tasks(self, telegram_id: int) -> Optional[list[DaySummary]]:
        """
        Returns tasks submitted by the user in the current Mon–Sun week,
        grouped by local Jakarta date. Returns None if user is not found.

        Note: user_id == telegram_id is assumed when the tasks table stores
        telegram_id directly as user_id. If a separate users table is used,
        the caller must resolve telegram_id -> user_id before calling this.
        This implementation stores telegram_id in tasks.user_id for simplicity.
        """
        week_start, week_end = get_current_week_range()

        # Convert week boundaries to timezone-aware datetimes for comparison
        start_dt = datetime(week_start.year, week_start.month, week_start.day,
                            tzinfo=TIMEZONE)
        end_dt = datetime(week_end.year, week_end.month, week_end.day,
                          23, 59, 59, tzinfo=TIMEZONE)

        stmt = (
            select(Task)
            .where(
                Task.user_id == telegram_id,
                Task.created_at >= start_dt,
                Task.created_at <= end_dt,
            )
            .order_by(Task.created_at)
        )

        result = await self.session.execute(stmt)
        tasks = result.scalars().all()

        # Group by local Jakarta date
        grouped: dict[date, list[Task]] = defaultdict(list)
        for task in tasks:
            local_date = task.created_at.astimezone(TIMEZONE).date()
            grouped[local_date].append(task)

        return [
            DaySummary(date=day, tasks=grouped[day])
            for day in sorted(grouped.keys())
        ]
