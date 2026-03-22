from sqlalchemy import String, Date, JSON, Integer, DateTime
from sqlalchemy.orm import mapped_column, Mapped
from datetime import date, datetime

from app.db.database import Base


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    report_date: Mapped[date] = mapped_column(Date)  # ISO Monday anchor (ADR-2)
    ai_analysis: Mapped[dict] = mapped_column(JSON, nullable=True)
    review_status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
