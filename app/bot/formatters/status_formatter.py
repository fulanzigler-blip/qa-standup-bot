from typing import Optional
from telegram.helpers import escape_markdown

from app.models.weekly_report import WeeklyReport

STATUS_EMOJI = {
    "pending": "\u23f3",
    "approved": "\u2705",
    "rejected": "\u274c",
}


class StatusFormatter:
    @staticmethod
    def format_status(report: Optional[WeeklyReport]) -> str:
        """
        Formats the weekly report into Telegram MarkdownV2.
        Handles: tasks found, no tasks, and missing ai_analysis gracefully.
        """
        if not report:
            return StatusFormatter._no_tasks_message()

        status = (report.review_status or "pending").lower()
        emoji = STATUS_EMOJI.get(status, "\u2753")
        status_label = escape_markdown(status.upper(), version=2)

        submitted_at = ""
        if report.created_at:
            submitted_at = escape_markdown(
                report.created_at.strftime("%Y-%m-%d %H:%M"), version=2
            )

        week_anchor = escape_markdown(str(report.report_date), version=2)

        header = (
            f"*Your Standup Status*\n"
            f"Week of: {week_anchor}\n"
            f"Submitted: {submitted_at or '_unknown_'}\n"
            f"Review status: {emoji} {status_label}\n\n"
        )

        analysis = report.ai_analysis
        if not analysis:
            body = "_No task details parsed from submission\\._"
        elif isinstance(analysis, list):
            body = "*Tasks:*\n"
            for i, item in enumerate(analysis, 1):
                body += f"{i}\\. {escape_markdown(str(item), version=2)}\n"
        elif isinstance(analysis, dict):
            body = "*Tasks:*\n"
            for key, value in analysis.items():
                safe_key = escape_markdown(str(key), version=2)
                safe_val = escape_markdown(str(value), version=2)
                body += f"\u2022 *{safe_key}*: {safe_val}\n"
        else:
            body = f"_{escape_markdown(str(analysis), version=2)}_"

        return header + body

    @staticmethod
    def _no_tasks_message() -> str:
        return "_You haven't submitted a standup for this week yet\\._"

    @staticmethod
    def group_acknowledge_message() -> str:
        return "Checking your status\\. Please check your Direct Messages\\."

    @staticmethod
    def error_message() -> str:
        return "Sorry, I couldn't retrieve your status right now\\. Please try again later\\."
