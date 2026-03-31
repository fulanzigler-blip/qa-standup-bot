"""
Core logic for the /remind command.
Handles identifying missing squads, sending messages, and logging.
"""
import os
import logging
from datetime import date, timedelta
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.squad import Squad, SquadMember, ReminderLog
from app.models.weekly_report import WeeklyReport

# Assuming a bot client interface exists or is passed in.
# We will define a protocol or interface here for the dependency injection.
from app.bot.client import BotClient

logger = logging.getLogger(__name__)

class ReminderService:
    def __init__(self, db: Session, bot: BotClient):
        self.db = db
        self.bot = bot

    def get_iso_monday(self) -> date:
        """Returns the ISO Monday for the current week."""
        today = date.today()
        # weekday() returns 0 for Monday, 6 for Sunday
        return today - timedelta(days=today.weekday())

    def get_missing_squads(self, week_date: date) -> List[Squad]:
        """
        Identifies squads that have not submitted a weekly update.
        A squad is 'missing' if ANY member has no WeeklyReport for the current week.
        Also filters out squads that have already been reminded this week.
        """
        # 1. Get all squads
        all_squads = self.db.query(Squad).all()

        missing_squads = []

        for squad in all_squads:
            # Check if already reminded (Idempotency check)
            already_reminded = self.db.query(ReminderLog).filter(
                ReminderLog.squad_id == squad.id,
                ReminderLog.week_date == week_date
            ).first()

            if already_reminded:
                logger.info(f"Squad {squad.name} already reminded for {week_date}. Skipping.")
                continue

            # Check submission status
            # Get all member IDs for this squad
            member_ids = [m.telegram_id for m in squad.members]

            if not member_ids:
                logger.warning(f"Squad {squad.name} has no members. Skipping.")
                continue

            # Check if every member has a report for this week
            # Logic: Squad is missing if ANY member has no report
            reports = self.db.query(WeeklyReport.telegram_id).filter(
                WeeklyReport.telegram_id.in_(member_ids),
                WeeklyReport.report_date == week_date
            ).all()

            submitted_ids = {r[0] for r in reports}
            missing_member_ids = [mid for mid in member_ids if mid not in submitted_ids]

            if missing_member_ids:
                missing_squads.append(squad)
                logger.info(f"Squad {squad.name} is missing updates. Missing members: {missing_member_ids}")

        return missing_squads

    async def send_reminders(self, squads: List[Squad], actor_telegram_id: int) -> Tuple[List[str], List[str]]:
        """
        Sends reminders to the list of squads.
        Returns a tuple of (successful_squad_names, failed_squad_names).
        """
        week_date = self.get_iso_monday()
        success_names = []
        failed_names = []

        for squad in squads:
            try:
                # Determine destination: Chat ID or DM individual members
                # Fallback: If telegram_chat_id is NULL, DM members
                targets = []

                if squad.telegram_chat_id:
                    targets.append(squad.telegram_chat_id)
                else:
                    # Fallback to DMs
                    targets = [m.telegram_id for m in squad.members]

                message_text = f"👋 *Weekly Update Reminder*\n\n" \
                               f"Hi team {squad.name}! It looks like your weekly standup update is missing or incomplete.\n\n" \
                               f"Please take a moment to submit your update now.\n" \
                               f"Use the /submit command to report."

                sent_count = 0
                for target_id in targets:
                    try:
                        await self.bot.send_message(chat_id=target_id, text=message_text, parse_mode="Markdown")
                        sent_count += 1
                    except Exception as e:
                        logger.error(f"Failed to send reminder to {target_id} for squad {squad.name}: {e}")

                if sent_count > 0:
                    # Log successful reminder (Idempotency Gate)
                    log_entry = ReminderLog(
                        squad_id=squad.id,
                        week_date=week_date,
                        reminded_by_telegram_id=actor_telegram_id
                    )
                    self.db.add(log_entry)
                    self.db.commit()
                    success_names.append(squad.name)
                else:
                    failed_names.append(squad.name)

            except Exception as e:
                logger.error(f"Critical error processing reminder for squad {squad.name}: {e}")
                self.db.rollback()
                failed_names.append(squad.name)

        return success_names, failed_names
