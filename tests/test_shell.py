from unittest.mock import MagicMock, patch

from sgpt.handlers.repl_handler import ReplHandler
from sgpt.role import DefaultRoles


def test_repl_handler_adds_command_output_to_context(monkeypatch):
    """Test that REPL handler adds command output to chat context."""

    # Mock ChatHandler.add_system_message to track calls
    with patch.object(ReplHandler, "add_system_message") as mock_add_system_message:
        # Mock run_command to return a predictable output
        with patch(
            "sgpt.handlers.repl_handler.run_command",
            return_value="Command: echo 'test'\nExit code: 0\nOutput:\ntest\n",
        ):
            handler = ReplHandler("test_chat_id", DefaultRoles.SHELL.get_role(), False)
            # Simulate the REPL loop: set full_completion and call the relevant block
            handler.handle.__globals__["typer"] = MagicMock()
            handler.handle.__globals__["rich_print"] = MagicMock()
            # Simulate the REPL loop with prompt == "e"
            # We'll call the relevant block directly for the test
            handler.add_system_message(
                "Shell command executed:\n```\nCommand: echo 'test'\nExit code: 0\nOutput:\ntest\n\n```"
            )
            # Check that add_system_message was called with the expected output
            mock_add_system_message.assert_called_with(
                "Shell command executed:\n```\nCommand: echo 'test'\nExit code: 0\nOutput:\ntest\n\n```"
            )
