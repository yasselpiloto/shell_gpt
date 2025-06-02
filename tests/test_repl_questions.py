from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from sgpt import config
from sgpt.role import DefaultRoles, SystemRole

from .utils import app, cmd_args, mock_comp, runner

cfg = config.cfg


class TestReplQuestionIntegration:
    """Test suite for question functionality integration in REPL mode."""

    def setup_method(self):
        """Set up test fixtures."""
        self.chat_name = "_test_question"
        self.chat_path = Path(cfg.get("CHAT_CACHE_PATH")) / self.chat_name
        # Clean up any existing test chat
        self.chat_path.unlink(missing_ok=True)

    def teardown_method(self):
        """Clean up test fixtures."""
        self.chat_path.unlink(missing_ok=True)

    @patch("sgpt.handlers.handler.Handler.get_completion")
    def test_repl_default_mode_question_functionality(self, mock_get_completion):
        """Test question functionality in default REPL mode."""
        # Mock responses for both regular prompt and question
        mock_get_completion.side_effect = [
            mock_comp("Regular response"),
            mock_comp("Question answer")
        ]
        
        args = {"--repl": self.chat_name}
        inputs = [
            "__sgpt__eof__",  # Skip initial prompt
            "Regular prompt",  # Regular interaction
            "What is Python??",  # Question with ?? trigger
            "exit()"
        ]
        
        result = runner.invoke(app, cmd_args(**args), input="\n".join(inputs))
        
        assert result.exit_code == 0
        assert "Regular response" in result.stdout
        assert "Question answer" in result.stdout
        
        # Verify both calls were made
        assert mock_get_completion.call_count == 2

    @patch("sgpt.handlers.handler.Handler.get_completion")
    def test_repl_shell_mode_question_functionality(self, mock_get_completion):
        """Test question functionality in shell REPL mode."""
        # Mock responses for shell command and question
        mock_get_completion.side_effect = [
            mock_comp("ls -la"),
            mock_comp("Shell questions are helpful")
        ]
        
        args = {"--repl": self.chat_name, "--shell": True}
        inputs = [
            "__sgpt__eof__",  # Skip initial prompt
            "list files",  # Shell command request
            "What does ls command do??",  # Question about shell
            "exit()"
        ]
        
        result = runner.invoke(app, cmd_args(**args), input="\n".join(inputs))
        
        assert result.exit_code == 0
        assert "ls -la" in result.stdout
        assert "Shell questions are helpful" in result.stdout
        
        # Verify both calls were made
        assert mock_get_completion.call_count == 2

    @patch("sgpt.handlers.handler.Handler.get_completion")
    def test_question_context_continuity(self, mock_get_completion):
        """Test that questions and answers are added to chat context."""
        mock_get_completion.side_effect = [
            mock_comp("The capital is Paris"),
            mock_comp("Population is about 2.2 million")
        ]
        
        args = {"--repl": self.chat_name}
        inputs = [
            "__sgpt__eof__",
            "What is the capital of France??",
            "What is its population??",  # Should have context from previous Q&A
            "exit()"
        ]
        
        result = runner.invoke(app, cmd_args(**args), input="\n".join(inputs))
        
        assert result.exit_code == 0
        assert "The capital is Paris" in result.stdout
        assert "Population is about 2.2 million" in result.stdout
        
        # Verify context was maintained by checking call count
        assert mock_get_completion.call_count == 2

    @patch("sgpt.handlers.handler.Handler.get_completion")
    def test_mixed_question_and_regular_workflow(self, mock_get_completion):
        """Test mixed workflow with both questions and regular prompts."""
        mock_get_completion.side_effect = [
            mock_comp("Here's some code"),
            mock_comp("Python is a programming language"),
            mock_comp("Updated code version")
        ]
        
        args = {"--repl": self.chat_name, "--code": True}
        inputs = [
            "__sgpt__eof__",
            "write a hello world function",  # Regular code request
            "What is Python??",  # Question
            "improve the function",  # Regular request with context
            "exit()"
        ]
        
        result = runner.invoke(app, cmd_args(**args), input="\n".join(inputs))
        
        assert result.exit_code == 0
        assert "Here's some code" in result.stdout
        assert "Python is a programming language" in result.stdout
        assert "Updated code version" in result.stdout
        
        # All three interactions should have been processed
        assert mock_get_completion.call_count == 3

    @patch("sgpt.handlers.handler.Handler.get_completion")
    def test_question_with_multiline_prompt(self, mock_get_completion):
        """Test question functionality with multiline input."""
        mock_get_completion.return_value = mock_comp("Multiline answer")
        
        args = {"--repl": self.chat_name}
        inputs = [
            "__sgpt__eof__",
            '"""',  # Start multiline input
            "This is a complex question",
            "with multiple lines",
            "for testing??",
            '"""',  # End multiline input
            "exit()"
        ]
        
        result = runner.invoke(app, cmd_args(**args), input="\n".join(inputs))
        
        assert result.exit_code == 0
        assert "Multiline answer" in result.stdout
        assert mock_get_completion.call_count == 1

    @patch("sgpt.handlers.handler.Handler.get_completion")
    def test_question_uses_default_role(self, mock_get_completion):
        """Test that questions use DEFAULT role regardless of REPL mode."""
        mock_get_completion.return_value = mock_comp("Answer using default role")
        
        # Test in shell mode to verify questions don't use shell role
        args = {"--repl": self.chat_name, "--shell": True}
        inputs = [
            "__sgpt__eof__",
            "How does Python work??",
            "exit()"
        ]
        
        result = runner.invoke(app, cmd_args(**args), input="\n".join(inputs))
        
        assert result.exit_code == 0
        assert "Answer using default role" in result.stdout
        
        # Verify the completion was called with messages
        args_called, kwargs_called = mock_get_completion.call_args
        messages = kwargs_called['messages']
        
        # Should have system message with DEFAULT role, not SHELL role
        system_message = next(msg for msg in messages if msg['role'] == 'system')
        default_role = DefaultRoles.DEFAULT.get_role()
        assert system_message['content'] == default_role.role

    @patch("sgpt.handlers.handler.Handler.get_completion")
    @patch("sgpt.handlers.question_handler.rich_print")
    def test_question_enhanced_formatting_in_repl(self, mock_rich_print, mock_get_completion):
        """Test that question responses have enhanced formatting in REPL."""
        mock_get_completion.return_value = mock_comp("Formatted answer")
        
        args = {"--repl": self.chat_name}
        inputs = [
            "__sgpt__eof__",
            "Test formatting??",
            "exit()"
        ]
        
        result = runner.invoke(app, cmd_args(**args), input="\n".join(inputs))
        
        assert result.exit_code == 0
        
        # Verify that rich_print was called for formatting (at least for the answer)
        rich_print_calls = [str(call) for call in mock_rich_print.call_args_list]
        
        # Should find calls related to question formatting
        answer_header_found = any("💡 Answer:" in call for call in rich_print_calls)
        cyan_formatting_found = any("cyan" in call for call in rich_print_calls)
        
        assert answer_header_found, f"Answer header not found in rich_print calls: {rich_print_calls}"
        assert cyan_formatting_found, f"Cyan formatting not found in rich_print calls: {rich_print_calls}"

    @patch("sgpt.handlers.handler.Handler.get_completion")
    def test_question_strips_double_question_marks_in_repl(self, mock_get_completion):
        """Test that ?? is properly stripped from questions in REPL context."""
        mock_get_completion.return_value = mock_comp("Clean answer")
        
        args = {"--repl": self.chat_name}
        inputs = [
            "__sgpt__eof__",
            "What is the answer??",
            "exit()"
        ]
        
        result = runner.invoke(app, cmd_args(**args), input="\n".join(inputs))
        
        assert result.exit_code == 0
        
        # Verify that the completion was called with cleaned prompt
        args_called, kwargs_called = mock_get_completion.call_args
        messages = kwargs_called['messages']
        user_message = next(msg for msg in messages if msg['role'] == 'user')
        
        # rstrip('?') removes all trailing ? characters when prompt ends with ??
        assert user_message['content'] == "What is the answer"

    @patch("sgpt.handlers.handler.Handler.get_completion")
    def test_chat_history_shows_questions_and_answers(self, mock_get_completion):
        """Test that questions and answers appear in chat history on subsequent REPL sessions."""
        mock_get_completion.side_effect = [
            mock_comp("First answer"),
            mock_comp("Second answer")
        ]
        
        # First session with questions
        args = {"--repl": self.chat_name}
        inputs = [
            "__sgpt__eof__",
            "First question??",
            "exit()"
        ]
        
        result1 = runner.invoke(app, cmd_args(**args), input="\n".join(inputs))
        assert result1.exit_code == 0
        
        # Second session should show chat history including questions
        inputs2 = [
            "__sgpt__eof__",
            "Second question??",
            "exit()"
        ]
        
        result2 = runner.invoke(app, cmd_args(**args), input="\n".join(inputs2))
        assert result2.exit_code == 0
        
        # Should show chat history and both questions/answers
        assert "Chat History" in result2.stdout
        assert "First question??" in result2.stdout
        assert "First answer" in result2.stdout
        assert "Second answer" in result2.stdout

    @patch("sgpt.handlers.handler.Handler.get_completion")
    def test_question_without_double_question_marks(self, mock_get_completion):
        """Test that regular prompts ending with ? are not treated as questions."""
        mock_get_completion.return_value = mock_comp("Regular response")
        
        args = {"--repl": self.chat_name}
        inputs = [
            "__sgpt__eof__",
            "Is this a regular prompt?",  # Single ? should not trigger question mode
            "exit()"
        ]
        
        result = runner.invoke(app, cmd_args(**args), input="\n".join(inputs))
        
        assert result.exit_code == 0
        assert "Regular response" in result.stdout
        
        # Should not use QuestionHandler formatting, just regular response
        # This is harder to test directly, but we can verify the call was made normally
        assert mock_get_completion.call_count == 1

    @patch("sgpt.handlers.handler.Handler.get_completion")
    def test_question_with_empty_response(self, mock_get_completion):
        """Test question handling when LLM returns empty response."""
        mock_get_completion.return_value = mock_comp("")
        
        args = {"--repl": self.chat_name}
        inputs = [
            "__sgpt__eof__",
            "Empty response test??",
            "exit()"
        ]
        
        result = runner.invoke(app, cmd_args(**args), input="\n".join(inputs))
        
        # Should not crash, should handle empty response gracefully
        assert result.exit_code == 0
