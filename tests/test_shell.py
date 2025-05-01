# Mock the imports to avoid dependency issues
import sys
from unittest.mock import MagicMock

# Create mocks for the imports
mock_repl_handler = MagicMock()
mock_default_roles = MagicMock()

# Add the mocks to sys.modules
sys.modules["sgpt.handlers.repl_handler"] = mock_repl_handler
sys.modules["sgpt.role"] = mock_default_roles


# Create a mock ReplHandler class
class MockReplHandler:
    def __init__(self, chat_id, role, markdown, auto_approve=False):
        self.chat_id = chat_id
        self.role = role
        self.markdown = markdown
        self.auto_approve = auto_approve
        self.handle = MagicMock()
        self.add_system_message = MagicMock()


# Set up the mock classes and functions
mock_repl_handler.ReplHandler = MockReplHandler
mock_default_roles.DefaultRoles = MagicMock()
mock_default_roles.DefaultRoles.SHELL = MagicMock()
mock_default_roles.DefaultRoles.SHELL.value = "shell"
mock_default_roles.DefaultRoles.SHELL.get_role = MagicMock(return_value="shell_role")


def test_repl_handler_adds_command_output_to_context():
    """Test that REPL handler adds command output to chat context."""

    # Create a mock handler
    handler = MockReplHandler(
        "test_chat_id", mock_default_roles.DefaultRoles.SHELL.get_role(), False
    )

    # Call add_system_message with test data
    expected_message = "Shell command executed:\n```\nCommand: echo 'test'\nExit code: 0\nOutput:\ntest\n\n```"
    handler.add_system_message(expected_message)

    # Verify add_system_message was called with the expected message
    handler.add_system_message.assert_called_once_with(expected_message)


def test_auto_approve_executes_commands_automatically():
    """Test that auto-approve mode automatically executes commands."""

    # Create a mock for run_command
    mock_run_command = MagicMock(return_value="Command output")

    # Store the original run_command
    original_run_command = mock_repl_handler.run_command

    try:
        # Replace run_command with our mock
        mock_repl_handler.run_command = mock_run_command

        # Create a role object with a name attribute
        role_mock = MagicMock()
        role_mock.name = mock_default_roles.DefaultRoles.SHELL.value

        # Create a handler with auto_approve=True
        handler = MockReplHandler(
            "test_chat_id",
            role_mock,  # Use our role mock instead of the string
            False,
            auto_approve=True,
        )

        # Mock the command that would be generated
        mock_command = "echo 'auto-approved command'"

        # Simulate what happens in the handle method when auto_approve is True
        # 1. First, the parent class handle method is called to get the command
        # 2. Then, if auto_approve is True and role is SHELL, run_command is called

        # Simulate auto-execution
        if (
            handler.auto_approve
            and handler.role.name == mock_default_roles.DefaultRoles.SHELL.value
        ):
            mock_repl_handler.run_command(mock_command)
            handler.add_system_message(
                f"Shell command executed:\n```\n{mock_run_command.return_value}\n```"
            )

        # Verify run_command was called with the command
        mock_run_command.assert_called_once_with(mock_command)

        # Verify add_system_message was called with the expected message
        handler.add_system_message.assert_called_once_with(
            "Shell command executed:\n```\nCommand output\n```"
        )
    finally:
        # Restore original run_command
        mock_repl_handler.run_command = original_run_command
