"""
SQLAlchemy models for Squads and Reminders.
"""
from datetime import date, datetime
from sqlalchemy import Column, Integer, BigInteger, String, Date, TIMESTAMP, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Squad(Base):
    __tablename__ = "squads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    telegram_chat_id = Column(BigInteger, nullable=True) # Nullable allows DM fallback
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    members = relationship("SquadMember", back_populates="squad", cascade="all, delete-orphan")
    reminder_logs = relationship("ReminderLog", back_populates="squad", cascade="all, delete-orphan")

class SquadMember(Base):
    __tablename__ = "squad_members"
    __table_args__ = (UniqueConstraint('squad_id', 'telegram_id', name='_squad_member_uc'),)

    id = Column(Integer, primary_key=True, index=True)
    squad_id = Column(Integer, ForeignKey("squads.id"), nullable=False)
    telegram_id = Column(BigInteger, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    squad = relationship("Squad", back_populates="members")

class ReminderLog(Base):
    __tablename__ = "reminder_log"
    __table_args__ = (UniqueConstraint('squad_id', 'week_date', name='_reminder_squad_week_uc'),)

    id = Column(Integer, primary_key=True, index=True)
    squad_id = Column(Integer, ForeignKey("squads.id"), nullable=False)
    week_date = Column(Date, nullable=False) # Represents the ISO Monday of the week
    reminded_at = Column(TIMESTAMP, default=datetime.utcnow)
    reminded_by_telegram_id = Column(BigInteger, nullable=False)

    # Relationships
    squad = relationship("Squad", back_populates="reminder_logs")
