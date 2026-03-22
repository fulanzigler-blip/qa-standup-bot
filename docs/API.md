# Bot Command Reference

This document describes all available slash commands for the QA Standup Bot.

---

## `/status`

Retrieves a summary of all tasks submitted by the requesting user for the current week (Monday through Sunday, in Asia/Jakarta timezone).

### Behavior by chat type

| Chat Type | Bot behavior |
|-----------|-------------|
| Private   | Sends the status report directly in the chat. |
| Group     | Replies publicly with a confirmation, then sends the full report via Direct Message. |

### Example: private chat

**User sends:**
```
/status
```

**Bot replies (tasks exist):**
```
Your Weekly Status

Monday 2026-03-16
- Fixed login bug
- Reviewed PR #42

Wednesday 2026-03-18
- Deployed to staging
```

**Bot replies (no tasks this week):**
```
No submissions this week.
```

### Example: group chat

**User sends `/status` in a group.**

**Bot replies in the group:**
```
Checking your status. Please check your Direct Messages.
```

**Bot sends to user's DM:**
```
Your Weekly Status

Monday 2026-03-16
- Implemented /status command
```

**If bot cannot DM the user** (user has never started a private chat with the bot):
```
I couldn't send you a DM. Please start a private chat with me first.
```

### Notes

- **Timezone:** All date grouping is based on `Asia/Jakarta` (WIB) by default. Configurable via the `TIMEZONE` environment variable.
- **Week boundary:** Monday 00:00:00 through Sunday 23:59:59 in the configured timezone.
- **Scope:** Current week only. Previous weeks are not accessible via this command.
- **Privacy:** The full task list is never displayed publicly in group chats.
