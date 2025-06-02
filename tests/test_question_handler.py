from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from sgpt.handlers.question_handler import QuestionHandler
from sgpt.role import DefaultRoles, SystemRole
from sgpt import config

from .utils import mock_comp

cfg = config.cfg


class TestQuestionHandler:
    """Test suite for QuestionHandler functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.role = DefaultRoles.DEFAULT.get_role()
        self.handler = QuestionHandler(self.role, markdown=False)

    @patch("sgpt.handlers.handler.Handler.get_completion")
    def test_question_handler_strips_double_question_marks(self, mock_get_completion):
        """Test that QuestionHandler correctly strips ?? suffix from prompts."""
        mock_get_completion.return_value = mock_comp("This is the answer")
        
        prompt_with_suffix = "What is the capital of France??"
        result = self.handler.handle(prompt=prompt_with_suffix)
        
        # Verify that the completion was called with the cleaned prompt
        args, kwargs = mock_get_completion.call_args
        messages = kwargs['messages']
        user_message = next(msg for msg in messages if msg['role'] == 'user')
        
        # rstrip('?') removes all trailing ? characters when prompt ends with ??
        assert user_message['content'] == "What is the capital of France"
        assert result == "This is the answer"

    @patch("sgpt.handlers.handler.Handler.get_completion")
    def test_question_handler_handles_prompt_without_suffix(self, mock_get_completion):
        """Test that QuestionHandler works with prompts that don't end with ??."""
        mock_get_completion.return_value = mock_comp("This is the answer")
        
        prompt_without_suffix = "What is the capital of France"
        result = self.handler.handle(prompt=prompt_without_suffix)
        
        # Verify that the completion was called with the original prompt
        args, kwargs = mock_get_completion.call_args
        messages = kwargs['messages']
        user_message = next(msg for msg in messages if msg['role'] == 'user')
        
        assert user_message['content'] == "What is the capital of France"
        assert result == "This is the answer"

    @patch("sgpt.handlers.handler.Handler.get_completion")
    @patch("sgpt.handlers.question_handler.rich_print")
    def test_question_handler_visual_formatting(self, mock_rich_print, mock_get_completion):
        """Test that QuestionHandler applies enhanced visual formatting."""
        mock_get_completion.return_value = mock_comp("This is a multi-line\nanswer response")
        
        result = self.handler.handle(prompt="Test question??")
        
        # Verify that rich_print was called for formatting
        assert mock_rich_print.call_count >= 2  # At least header and content
        
        # Check that the first call includes the answer header
        first_call = mock_rich_print.call_args_list[0]
        assert "💡 Answer:" in str(first_call)
        
        # Check that the second call includes the formatted response
        second_call = mock_rich_print.call_args_list[1]
        formatted_response = str(second_call)
        assert "cyan" in formatted_response  # Should use cyan color
        assert "    " in formatted_response  # Should be indented

    @patch("sgpt.handlers.handler.Handler.get_completion")
    def test_question_handler_inherits_from_default_handler(self, mock_get_completion):
        """Test that QuestionHandler correctly inherits from DefaultHandler."""
        mock_get_completion.return_value = mock_comp("Test response")
        
        # Test that it has the same make_messages behavior as DefaultHandler
        messages = self.handler.make_messages("Test prompt")
        
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[0]['content'] == self.role.role
        assert messages[1]['role'] == 'user'
        assert messages[1]['content'] == "Test prompt"

    @patch("sgpt.handlers.handler.Handler.get_completion")
    def test_question_handler_passes_kwargs_to_completion(self, mock_get_completion):
        """Test that QuestionHandler passes additional kwargs to get_completion."""
        mock_get_completion.return_value = mock_comp("Test response")
        
        # Call with additional parameters
        self.handler.handle(
            prompt="Test??",
            model="gpt-3.5-turbo",
            temperature=0.5,
            top_p=0.9,
            caching=True
        )
        
        # Verify that all kwargs were passed through
        args, kwargs = mock_get_completion.call_args
        assert 'model' in kwargs
        assert 'temperature' in kwargs
        assert 'top_p' in kwargs
        assert 'caching' in kwargs

    @patch("sgpt.handlers.handler.Handler.get_completion")
    def test_question_handler_collects_streaming_response(self, mock_get_completion):
        """Test that QuestionHandler properly collects streaming responses."""
        # Mock a streaming response
        def streaming_generator():
            yield "Part 1 "
            yield "Part 2 "
            yield "Part 3"
        
        mock_get_completion.return_value = streaming_generator()
        
        result = self.handler.handle(prompt="Test question??")
        
        # Should collect all parts into a single response
        assert result == "Part 1 Part 2 Part 3"

    def test_question_handler_initialization(self):
        """Test that QuestionHandler initializes correctly."""
        # Test with markdown enabled
        handler_with_md = QuestionHandler(self.role, markdown=True)
        assert handler_with_md.role == self.role
        assert handler_with_md.markdown == ("APPLY MARKDOWN" in self.role.role)
        
        # Test with markdown disabled
        handler_without_md = QuestionHandler(self.role, markdown=False)
        assert handler_without_md.role == self.role
        assert handler_without_md.markdown == False

    @patch("sgpt.handlers.question_handler.rich_print")
    def test_print_question_response_formatting(self, mock_rich_print):
        """Test the _print_question_response method directly."""
        test_response = "This is a test response\nwith multiple lines\nfor testing"
        
        self.handler._print_question_response(test_response)
        
        # Should call rich_print twice: once for header, once for content
        assert mock_rich_print.call_count == 2
        
        # Check header call
        header_call = mock_rich_print.call_args_list[0][0][0]
        assert "💡 Answer:" in header_call
        assert "[dim]" in header_call
        
        # Check content call
        content_call = mock_rich_print.call_args_list[1][0][0]
        assert "[cyan]" in content_call
        assert "    This is a test response" in content_call  # Should be indented
        assert "    with multiple lines" in content_call      # Should be indented
        assert "    for testing" in content_call             # Should be indented

    @patch("sgpt.handlers.handler.Handler.get_completion")
    def test_question_handler_with_empty_response(self, mock_get_completion):
        """Test QuestionHandler handles empty responses gracefully."""
        mock_get_completion.return_value = mock_comp("")
        
        result = self.handler.handle(prompt="Empty response test??")
        
        assert result == ""

    @patch("sgpt.handlers.handler.Handler.get_completion")
    def test_question_handler_with_whitespace_in_prompt(self, mock_get_completion):
        """Test QuestionHandler handles prompts with whitespace correctly."""
        mock_get_completion.return_value = mock_comp("Clean response")
        
        # Test prompt with trailing whitespace and ??
        prompt_with_whitespace = "  What is this?  ??"
        result = self.handler.handle(prompt=prompt_with_whitespace)
        
        # Verify that whitespace was handled correctly
        args, kwargs = mock_get_completion.call_args
        messages = kwargs['messages']
        user_message = next(msg for msg in messages if msg['role'] == 'user')
        
        # Should strip trailing whitespace and only the ?? part
        assert user_message['content'] == "What is this?"
        assert result == "Clean response"
