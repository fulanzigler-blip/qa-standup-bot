import os
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.weekly_report import WeeklyReport


class StatusService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.tz = ZoneInfo(os.getenv("TIMEZONE", "Asia/Jakarta"))

    async def get_user_report(self, telegram_id: int) -> Optional[WeeklyReport]:
        """
        Fetches the report for the current ISO week for a specific user.
        ADR-2: report_date stores the ISO Monday anchor.
        """
        now = datetime.now(self.tz)
        # isoweekday(): Monday=1, Sunday=7
        days_since_monday = now.isoweekday() - 1
        iso_monday = now.date() - timedelta(days=days_since_monday)

        stmt = select(WeeklyReport).where(
            WeeklyReport.telegram_id == telegram_id,
            WeeklyReport.report_date == iso_monday,
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
