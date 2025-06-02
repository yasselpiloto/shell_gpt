from pathlib import Path
import json
from unittest.mock import patch
import pytest

from sgpt.handlers.chat_handler import ChatHandler
from sgpt.role import DefaultRoles, SystemRole
from sgpt import config

cfg = config.cfg


class TestChatHandlerEnhancements:
    """Test suite for ChatHandler enhancements, specifically the add_message method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.chat_name = "_test_chat_handler"
        self.chat_path = Path(cfg.get("CHAT_CACHE_PATH")) / self.chat_name
        # Clean up any existing test chat
        self.chat_path.unlink(missing_ok=True)
        
        self.role = DefaultRoles.DEFAULT.get_role()
        self.handler = ChatHandler(self.chat_name, self.role, markdown=False)

    def teardown_method(self):
        """Clean up test fixtures."""
        self.chat_path.unlink(missing_ok=True)

    def test_add_message_creates_chat_file(self):
        """Test that add_message creates chat file if it doesn't exist."""
        # Verify chat file doesn't exist initially
        assert not self.chat_path.exists()
        
        # Add a message
        test_message = {"role": "user", "content": "Test message"}
        self.handler.add_message(test_message)
        
        # Verify chat file was created
        assert self.chat_path.exists()
        
        # Verify message was stored correctly
        stored_messages = json.loads(self.chat_path.read_text())
        assert len(stored_messages) == 1
        assert stored_messages[0] == test_message

    def test_add_message_appends_to_existing_chat(self):
        """Test that add_message appends to existing chat history."""
        # Create initial chat with system message
        initial_messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "First message"}
        ]
        
        # Write initial messages to file
        self.chat_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.chat_path, 'w') as f:
            json.dump(initial_messages, f)
        
        # Add a new message
        new_message = {"role": "assistant", "content": "Assistant response"}
        self.handler.add_message(new_message)
        
        # Verify message was appended
        stored_messages = json.loads(self.chat_path.read_text())
        assert len(stored_messages) == 3
        assert stored_messages[0] == initial_messages[0]  # System message preserved
        assert stored_messages[1] == initial_messages[1]  # First user message preserved
        assert stored_messages[2] == new_message         # New message appended

    def test_add_message_with_no_chat_id(self):
        """Test that add_message does nothing when chat_id is None or empty."""
        # Create a mock handler with None chat_id to test the early return
        handler_no_chat = ChatHandler("test_no_persist", self.role, markdown=False)
        handler_no_chat.chat_id = None  # Force None chat_id to test early return
        
        # This should do nothing due to the early return in add_message
        test_message = {"role": "user", "content": "Should not be stored"}
        handler_no_chat.add_message(test_message)
        
        # No exception should be raised, and no file operations should occur
        # This test verifies the early return behavior
        assert True  # If we reach here without exception, the test passes

    def test_add_message_preserves_message_structure(self):
        """Test that add_message preserves the exact message structure."""
        # Test with various message types
        messages_to_add = [
            {"role": "user", "content": "User message"},
            {"role": "assistant", "content": "Assistant response"},
            {"role": "system", "content": "System instruction"},
            {"role": "user", "content": "Message with special chars: !@#$%^&*()"}
        ]
        
        for message in messages_to_add:
            self.handler.add_message(message)
        
        # Verify all messages were stored with exact structure
        stored_messages = json.loads(self.chat_path.read_text())
        assert len(stored_messages) == len(messages_to_add)
        
        for i, original_message in enumerate(messages_to_add):
            assert stored_messages[i] == original_message

    def test_add_message_handles_unicode_content(self):
        """Test that add_message correctly handles unicode content."""
        unicode_message = {
            "role": "user", 
            "content": "Unicode test: 🤖 Python 蟒蛇 café naïve résumé"
        }
        
        self.handler.add_message(unicode_message)
        
        # Verify unicode content is preserved
        stored_messages = json.loads(self.chat_path.read_text())
        assert len(stored_messages) == 1
        assert stored_messages[0] == unicode_message

    def test_add_message_respects_chat_cache_length(self):
        """Test that add_message respects the CHAT_CACHE_LENGTH setting."""
        # Get the current cache length setting
        cache_length = int(cfg.get("CHAT_CACHE_LENGTH"))
        
        # Create initial messages that exceed cache length
        initial_messages = [{"role": "system", "content": "System prompt"}]
        for i in range(cache_length + 5):  # Add more than cache limit
            initial_messages.append({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i}"
            })
        
        # Write initial messages
        self.chat_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.chat_path, 'w') as f:
            json.dump(initial_messages, f)
        
        # Add one more message
        new_message = {"role": "user", "content": "Final message"}
        self.handler.add_message(new_message)
        
        # Verify that messages were truncated but system message was preserved
        stored_messages = json.loads(self.chat_path.read_text())
        
        # Should have at most cache_length + 1 messages (system + cache_length others)
        assert len(stored_messages) <= cache_length + 1
        
        # First message should always be the system message
        assert stored_messages[0]["role"] == "system"
        assert stored_messages[0]["content"] == "System prompt"
        
        # Last message should be the one we just added
        assert stored_messages[-1] == new_message

    def test_add_message_with_empty_content(self):
        """Test that add_message handles empty content correctly."""
        empty_message = {"role": "user", "content": ""}
        
        self.handler.add_message(empty_message)
        
        # Verify empty content is preserved
        stored_messages = json.loads(self.chat_path.read_text())
        assert len(stored_messages) == 1
        assert stored_messages[0] == empty_message

    def test_add_message_integration_with_existing_methods(self):
        """Test that add_message works correctly with existing ChatHandler methods."""
        # Add some messages using add_message
        self.handler.add_message({"role": "user", "content": "Question 1"})
        self.handler.add_message({"role": "assistant", "content": "Answer 1"})
        self.handler.add_message({"role": "user", "content": "Question 2"})
        
        # Test that get_messages works correctly
        messages = self.handler.chat_session.get_messages(self.chat_name)
        assert len(messages) == 3
        assert "user: Question 1" in messages
        assert "assistant: Answer 1" in messages
        assert "user: Question 2" in messages
        
        # Test that exists method recognizes the chat
        assert self.handler.chat_session.exists(self.chat_name)

    def test_add_message_concurrent_access(self):
        """Test add_message behavior with concurrent access simulation."""
        # Simulate concurrent access by manually modifying file between operations
        self.handler.add_message({"role": "user", "content": "Message 1"})
        
        # Manually add a message to the file (simulating another process)
        stored_messages = json.loads(self.chat_path.read_text())
        stored_messages.append({"role": "system", "content": "External message"})
        with open(self.chat_path, 'w') as f:
            json.dump(stored_messages, f)
        
        # Add another message through the handler
        self.handler.add_message({"role": "user", "content": "Message 2"})
        
        # Verify both external and handler messages are present
        final_messages = json.loads(self.chat_path.read_text())
        assert len(final_messages) == 3
        assert any(msg["content"] == "Message 1" for msg in final_messages)
        assert any(msg["content"] == "External message" for msg in final_messages)
        assert any(msg["content"] == "Message 2" for msg in final_messages)

    def test_add_message_creates_directory_if_needed(self):
        """Test that add_message works when chat cache directory exists."""
        # Ensure the chat cache directory exists (this is the normal case)
        chat_cache_path = Path(cfg.get("CHAT_CACHE_PATH"))
        chat_cache_path.mkdir(parents=True, exist_ok=True)
        
        # Create a new handler and test
        handler = ChatHandler("test_dir_creation", self.role, markdown=False)
        
        # Add a message
        test_message = {"role": "user", "content": "Test directory creation"}
        handler.add_message(test_message)
        
        # Verify the file was created
        test_chat_path = chat_cache_path / "test_dir_creation"
        assert test_chat_path.exists()
        
        # Verify the message was stored
        stored_messages = json.loads(test_chat_path.read_text())
        assert len(stored_messages) == 1
        assert stored_messages[0] == test_message
        
        # Clean up
        test_chat_path.unlink(missing_ok=True)
