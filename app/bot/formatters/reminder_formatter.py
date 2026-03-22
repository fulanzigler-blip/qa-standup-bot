"""
Formatters for reminder messages.
"""

def format_squad_reminder(squad_name: str) -> str:
    """
    Formats the message sent to a squad channel or member.
    """
    return (
        f"👋 *Weekly Update Reminder*\n\n"
        f"Hi team {squad_name}! It looks like your weekly standup update is missing or incomplete.\n\n"
        f"Please take a moment to submit your update now so we can keep track of blockers and progress.\n"
        f"Use the /submit command to report."
    )

def format_no_reminders_needed() -> str:
    """
    Formats the response when all squads have submitted.
    """
    return "✅ All squads have submitted their weekly updates. No reminders needed."

def format_lead_summary(reminded_squads: list[str], skipped_squads: list[str] = None) -> str:
    """
    Formats the summary sent back to the QA Lead.
    """
    if not reminded_squads:
        return format_no_reminders_needed()

    msg = "🔔 *Reminders Sent*\n\n"
    msg += f"Sent reminders to **{len(reminded_squads)}** squad(s):\n"
    for squad in reminded_squads:
        msg += f"• {squad}\n"

    if skipped_squads:
        msg += f"\n⚠️ Skipped {len(skipped_squads)} squad(s) due to missing chat configuration or members."

    return msg
