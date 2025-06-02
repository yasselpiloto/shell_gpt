from typing import Dict, List
from rich import print as rich_print

from ..role import SystemRole
from .default_handler import DefaultHandler


class QuestionHandler(DefaultHandler):
    """Handler for general questions triggered by ?? suffix in REPL mode."""
    
    def __init__(self, role: SystemRole, markdown: bool) -> None:
        super().__init__(role, markdown)
        self.role = role

    def handle(self, prompt: str, **kwargs) -> str:
        """Handle question with enhanced visual formatting."""
        # Remove the ?? trigger from the prompt for cleaner LLM processing
        clean_prompt = prompt.rstrip('?').rstrip() if prompt.endswith('??') else prompt
        
        # Get the completion without printing by directly calling get_completion
        messages = self.make_messages(clean_prompt.strip())
        generator = self.get_completion(
            messages=messages,
            **kwargs
        )
        
        # Collect the full response without streaming it to console
        full_completion = ""
        for chunk in generator:
            full_completion += chunk
        
        # Enhanced visual formatting for question responses
        self._print_question_response(full_completion)
        
        return full_completion
    
    def _print_question_response(self, response: str) -> None:
        """Print response with special formatting for questions."""
        # Add visual distinction with indentation and color
        rich_print("\n[dim]💡 Answer:[/dim]")
        
        # Indent the response for visual distinction
        indented_response = "\n".join(f"    {line}" for line in response.split('\n'))
        rich_print(f"[cyan]{indented_response}[/cyan]")
