# QA Standup Bot

A Telegram bot for tracking and managing weekly QA squad standups. The bot helps QA squads submit their weekly updates and allows QA Leads to send targeted reminders to squads that haven't submitted yet.

## Features

- Weekly standup submission tracking for QA squads
- `/remind` command for QA Leads to send targeted reminders to squads missing updates
- Squad-based organization with configurable channels
- Idempotent reminder system (no duplicate reminders)
- Authorization control for QA Lead commands

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Telegram Bot API token
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/fulanzigler-blip/qa-standup-bot.git
   cd qa-standup-bot
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

6. Start the bot:
   ```bash
   python -m app.main
   ```

### Configuration

Create a `.env` file with the following variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API token | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` |
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql://user:password@localhost/qa_standup` |
| `QA_LEAD_IDS` | Comma-separated Telegram user IDs for QA Leads | `123456789,987654321` |
| `WEEK_START_DAY` | Day of week for weekly reports (optional, default: Monday) | `Monday` |

### Squad Setup

Before using the `/remind` command, squads must be configured in the database:

1. **Add a squad**:
   - Insert into `squads` table with squad name and `telegram_chat_id`
   - The `telegram_chat_id` is the channel/group ID where reminders will be sent
   - If NULL, reminders will be sent via DM to each member

2. **Add squad members**:
   - Insert into `squad_members` table mapping Telegram user IDs to squad IDs

3. **Verify setup**:
   ```sql
   SELECT s.name, s.telegram_chat_id, COUNT(sm.user_id) as member_count
   FROM squads s
   LEFT JOIN squad_members sm ON s.id = sm.squad_id
   GROUP BY s.id, s.name, s.telegram_chat_id;
   ```

## Usage

### `/remind` Command (QA Lead Only)

Send reminders to squads that haven't submitted their weekly update.

**Syntax:**
```
/remind
```

**Authorization:**
- Only users listed in `QA_LEAD_IDS` can use this command
- If unauthorized user attempts: Access denied message

**Behavior:**
- Identifies squads with at least one member who hasn't submitted a weekly report for the current week
- Sends a reminder message to each squad's configured channel (or DMs members if no channel configured)
- Logs reminders to prevent duplicate sending in the same week
- Responds to QA Lead with a summary of actions taken

**Example User Flow:**

1. QA Lead sends `/remind` command to bot

2. Bot analyzes current week's submissions:
   - Finds Squad A (all members submitted) → Skip
   - Finds Squad B (2 members missing) → Send reminder
   - Finds Squad C (no channel configured) → DM missing members

3. Bot sends reminders:
   ```
   📌 Weekly Update Reminder
   Your squad has not submitted this week's standup update.
   Please submit by Friday at 5 PM.
   Use /submit to provide your update.
   ```

4. Bot responds to QA Lead:
   ```
   ✅ Reminders sent to:
   • Squad B (2 members missing)
   • Squad C (3 members DM'd)

   All squads up to date:
   • Squad A
   ```

### Weekly Report Submission

Squad members submit their weekly updates using the `/submit` command (existing feature).

## Troubleshooting

### `/remind` command not responding

- Verify your Telegram ID is in `QA_LEAD_IDS` environment variable
- Check bot has necessary permissions in squad channels
- Verify database connection is active

### Reminders not reaching squads

- Check `telegram_chat_id` is correctly set for the squad
- Ensure bot is added to the squad channel/group
- If using DM fallback, verify bot can message users directly

### Incorrect squads identified as "missing"

- Verify squad membership in `squad_members` table
- Check `WeeklyReport` table has correct `report_date` values (ISO Monday anchor)
- Confirm all members of a squad have submitted for the week

### Duplicate reminders being sent

- Check `reminder_log` table has entries for the current week
- Verify UNIQUE constraint on `(squad_id, week_date)` exists

## Development

### Running Tests

```bash
pytest
```

### Database Migrations

Create new migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

## License

MIT License - see LICENSE file for details
