from app.bot.commands import COMMANDS


def test_status_command_exists() -> None:
    """Verify that the /status command is defined."""
    status_commands = [cmd for cmd in COMMANDS if cmd.command == "status"]
    assert len(status_commands) == 1, "Status command should be defined exactly once"


def test_status_command_description() -> None:
    """Verify that the /status command has the correct description."""
    status_cmd = next((cmd for cmd in COMMANDS if cmd.command == "status"), None)
    assert status_cmd is not None
    assert status_cmd.description == "Check your submitted tasks for this week"
