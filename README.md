# QA Standup Bot

A Telegram bot designed to assist engineering teams with their daily standup rituals. It allows team members to submit their daily updates and track their progress throughout the week.

## Features

- **Task Tracking:** Submit and manage daily standup tasks.
- **Weekly Status Reports:** Query a summary of all tasks submitted for the current week using the `/status` command.
- **Privacy Aware:** In group chats, reports are sent via Direct Message (DM) to maintain privacy.

## Prerequisites

- Python 3.9 or higher
- PostgreSQL 12 or higher
- A Telegram Bot Token (obtained via [@BotFather](https://t.me/botfather))

## Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/fulanzigler-blip/qa-standup-bot.git
   cd qa-standup-bot
   ```

2. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   Create a `.env` file in the root directory:

   ```env
   BOT_TOKEN=your_telegram_bot_token_here
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
   TIMEZONE=Asia/Jakarta
   ```

   > `TIMEZONE` defaults to `Asia/Jakarta` (WIB) if omitted.

4. **Apply database migrations**

   Ensure your PostgreSQL database is running, then apply all migration files in order:

   ```bash
   psql $DATABASE_URL -f db/migrations/0003_add_user_id_to_tasks.sql
   ```

5. **Run the bot**
   ```bash
   python -m app.main
   ```

   The bot will start polling Telegram for updates.

---

## Usage

### Checking your weekly status

The `/status` command retrieves a summary of all tasks you have submitted for the current week (Monday-Sunday).

**In a private chat:**
1. Open a chat with the bot.
2. Send:
   ```
   /status
   ```
3. The bot replies immediately with your weekly report.

**In a group chat:**
1. Send `/status` in the group.
2. The bot replies publicly: *"Checking your status. Please check your Direct Messages."*
3. Check your Direct Messages with the bot for the full report.

> **Note:** If the bot cannot DM you (e.g. you have never started a private chat with it), it will let you know in the group and ask you to start a private conversation first.

### Report format

Tasks are grouped by day. If no tasks were submitted this week, a friendly message is shown.

**Example output:**
```
Your Weekly Status

Monday 2026-03-16
- Fixed login bug
- Reviewed PR #42

Tuesday 2026-03-17
- Updated documentation
- Deployed to staging
```

**No submissions:**
```
No submissions this week.
```

---

## Deployment Guide

The bot is hosted on a Hetzner VPS.

### Deploying a new version

1. **Connect to the server** via SSH.

2. **Pull the latest code**
   ```bash
   cd /path/to/qa-standup-bot
   git pull origin main
   ```

3. **Apply any new database migrations**

   Check `db/migrations/` for new `.sql` files and apply them:
   ```bash
   psql $DATABASE_URL -f db/migrations/XXXX_migration_name.sql
   ```

4. **Restart the service**
   ```bash
   sudo systemctl restart qa-standup-bot
   ```

### Rollback procedure

If a critical issue is detected after deployment:

1. **Revert the code**
   ```bash
   cd /path/to/qa-standup-bot
   git revert HEAD --no-edit
   git push origin main
   ```

2. **Restart the service**
   ```bash
   sudo systemctl restart qa-standup-bot
   ```

3. **Database rollback** — If a schema migration was included, reverse it manually or restore from a backup.

> **TBD:** Docker and docker-compose setup files are not yet present in the repository. The bot currently runs directly on the host OS via a systemd service.
