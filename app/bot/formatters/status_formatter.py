from telegram.helpers import escape_markdown

from app.services.status_service import DaySummary


class StatusFormatter:
    @staticmethod
    def format_status(day_summaries: list[DaySummary]) -> str:
        """
        Formats weekly task summaries into Telegram MarkdownV2.
        Returns a "no submissions" message if the list is empty.
        """
        if not day_summaries:
            return StatusFormatter.no_tasks_message()

        lines = ["*Your Weekly Status*", ""]

        for summary in day_summaries:
            date_label = escape_markdown(
                summary.date.strftime("%A %Y\\-%m\\-%d"), version=2
            )
            lines.append(f"*{date_label}*")
            for task in summary.tasks:
                safe_title = escape_markdown(task.title, version=2)
                lines.append(f"• {safe_title}")
            lines.append("")

        return "\n".join(lines).strip()

    @staticmethod
    def no_tasks_message() -> str:
        return "_No submissions this week\\._"

    @staticmethod
    def group_acknowledge_message() -> str:
        return "Checking your status\\. Please check your Direct Messages\\."

    @staticmethod
    def error_message() -> str:
        return "Sorry, I couldn't retrieve your status right now\\. Please try again later\\."
