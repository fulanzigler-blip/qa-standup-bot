# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-03-22

### Added
- `/status` command: allows engineers to view a summary of all tasks submitted for the current week (Monday-Sunday), grouped by day with date labels.
- `app/utils/week.py`: timezone-aware `get_current_week_range()` utility returning the current Mon-Sun range in Asia/Jakarta (WIB).
- `app/services/status_service.py`: `StatusService` class that queries the `tasks` table filtered by user ID and current week range.
- `app/bot/formatters/status_formatter.py`: MarkdownV2 formatter for weekly status output, including empty-state and error messages.
- `app/bot/handlers/status_handler.py`: handler for `/status` that delivers results via DM in group chats and directly in private chats.
- `tests/test_status_service.py`, `tests/test_status_handler.py`, `tests/test_status_formatter.py`, `tests/test_status_edge_cases.py`: test coverage for all new components (30 tests total).
- `db/migrations/0003_add_user_id_to_tasks.sql`: adds `user_id` foreign key column and indexes to the `tasks` table.

### Changed
- `app/bot/router.py`: registered the new `CommandHandler` for `/status`.

### Known Issues (non-blocking)
- Sub-second boundary precision: tasks created within the last second of Sunday may occasionally be excluded depending on clock resolution.
- Cosmetic double-escaping of date hyphens in MarkdownV2 output (display only, no functional impact). Both issues are tracked for a follow-up fix.
