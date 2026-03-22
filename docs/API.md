# QA Standup Bot - Command API

This document describes the command interface for the QA Standup Bot.

## Authorization

Certain commands require QA Lead authorization. Authorization is controlled via the `QA_LEAD_IDS` environment variable, which contains a comma-separated list of authorized Telegram user IDs.

## Commands

### `/remind`

Send reminders to squads that have not submitted their weekly update.

**Authorization:** QA Lead only

**Request Format:**
```
/remind
```

**Parameters:** None

**Behavior:**
1. Identifies the current week using ISO Monday anchor (ADR-2)
2. Queries database for squads missing weekly reports
3. Sends reminder messages to configured channels or via DM
4. Logs reminders to prevent duplicates (idempotent)
5. Returns summary to QA Lead

**Success Response - Reminders Sent:**
```
✅ Reminders sent to the following squads:

• Squad Alpha (3 members missing update)
• Squad Beta (2 members missing update)

Squads up to date:
• Squad Gamma
• Squad Delta
```

**Success Response - All Caught Up:**
```
✅ All squads have submitted their weekly updates!
No reminders needed this week.

Squad status:
• Squad Alpha - Complete
• Squad Beta - Complete
• Squad Gamma - Complete
• Squad Delta - Complete
```

**Error Response - Unauthorized:**
```
❌ You are not authorized to use this command.
Only QA Leads can send reminders.
```

**Error Response - No Squads Configured:**
```
❌ No squads are configured in the system.
Please add squads before sending reminders.
```

### `/status`

Retrieves a summary of all tasks submitted by the requesting user for the current week (Monday through Sunday, in Asia/Jakarta timezone).

**Authorization:** All users

**Request Format:**
```
/status
```

**Behavior by chat type:**

| Chat Type | Bot behavior |
|-----------|-------------|
| Private   | Sends the status report directly in the chat. |
| Group     | Replies publicly with a confirmation, then sends the full report via Direct Message. |

**Example (tasks exist):**
```
Your Weekly Status

Monday 2026-03-16
- Fixed login bug
- Reviewed PR #42

Wednesday 2026-03-18
- Deployed to staging
```

**Example (no tasks this week):**
```
No submissions this week.
```

## Internal API

The following internal service methods are available for developers:

### ReminderService

```python
class ReminderService:
    def find_missing_squads(self, week_date: date) -> List[Squad]:
        """
        Find squads with at least one member missing a weekly report.

        Args:
            week_date: The Monday of the current week (ISO format)

        Returns:
            List of Squad objects missing reports
        """

    def send_reminders(self, squads: List[Squad], week_date: date) -> ReminderSummary:
        """
        Send reminder messages to squads and log for idempotency.

        Args:
            squads: List of squads to remind
            week_date: The Monday of the current week (ISO format)

        Returns:
            ReminderSummary object with results
        """

    def get_reminder_summary(self, week_date: date) -> str:
        """
        Generate a formatted summary of reminder actions for QA Lead.

        Args:
            week_date: The Monday of the current week (ISO format)

        Returns:
            Formatted string with reminder summary
        """
```

### RemindHandler

```python
class RemindHandler:
    async def handle_remind_command(self, update: Update, context: CallbackContext):
        """
        Handle the /remind Telegram command.

        Validates authorization, triggers reminder service, and sends response.
        """
```

## Data Model

### Squad
```python
class Squad(Base):
    id: int (Primary Key)
    name: str (Squad name)
    telegram_chat_id: Optional[int] (Channel/group ID for reminders)
    created_at: datetime
    updated_at: datetime
```

### SquadMember
```python
class SquadMember(Base):
    id: int (Primary Key)
    squad_id: int (Foreign Key to Squad)
    user_id: int (Telegram user ID)
    created_at: datetime
```

### ReminderLog
```python
class ReminderLog(Base):
    id: int (Primary Key)
    squad_id: int (Foreign Key to Squad)
    week_date: date (Monday of the week)
    reminded_at: datetime
    method: str (Enum: 'channel', 'dm')

    # Unique constraint on (squad_id, week_date) for idempotency
```

## Error Handling

| Error Code | Description | User Message |
|-----------|-------------|--------------|
| `UNAUTHORIZED` | User not in QA_LEAD_IDS | ❌ You are not authorized to use this command. |
| `NO_SQUADS` | No squads configured | ❌ No squads are configured in the system. |
| `ALL_SUBMITTED` | All squads caught up | ✅ All squads have submitted their weekly updates! |

## Rate Limiting

No rate limiting is implemented for the `/remind` command. The idempotency mechanism (via `reminder_log`) prevents duplicate reminders in the same week.

## Examples

### Python - Using ReminderService directly

```python
from app.services.reminder_service import ReminderService
from datetime import date

service = ReminderService()
week_date = date.today()  # Assumes today is Monday or service handles it

# Find missing squads
missing_squads = service.find_missing_squads(week_date)

# Send reminders
summary = service.send_reminders(missing_squads, week_date)

# Get formatted summary
message = service.get_reminder_summary(week_date)
print(message)
```

### SQL - Query for missing squads manually

```sql
-- Find squads with at least one member missing a weekly report
SELECT DISTINCT s.id, s.name, s.telegram_chat_id
FROM squads s
JOIN squad_members sm ON s.id = sm.squad_id
WHERE NOT EXISTS (
    SELECT 1
    FROM weekly_reports wr
    WHERE wr.telegram_id = sm.user_id
    AND wr.report_date = date_trunc('week', CURRENT_DATE)::date
    -- report_date should be the Monday of the current week
);
```
