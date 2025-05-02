from typing import Any

import typer
from click.types import Choice
from rich import print as rich_print
from rich.rule import Rule

from ..command_safety import is_safe_to_auto_execute
from ..role import DefaultRoles, SystemRole
from ..utils import run_command
from .chat_handler import ChatHandler
from .default_handler import DefaultHandler


class ReplHandler(ChatHandler):
    def __init__(
        self, chat_id: str, role: SystemRole, markdown: bool, auto_approve: bool = False
    ) -> None:
        super().__init__(chat_id, role, markdown)
        self.auto_approve = auto_approve

    @classmethod
    def _get_multiline_input(cls) -> str:
        multiline_input = ""
        while (user_input := typer.prompt("...", prompt_suffix="")) != '"""':
            multiline_input += user_input + "\n"
        return multiline_input

    def handle(self, init_prompt: str, **kwargs: Any) -> None:  # type: ignore
        if self.initiated:
            rich_print(Rule(title="Chat History", style="bold magenta"))
            self.show_messages(self.chat_id, self.markdown)
            rich_print(Rule(style="bold magenta"))

        info_message = (
            "Entering REPL mode, press Ctrl+C to exit."
            if not self.role.name == DefaultRoles.SHELL.value
            else (
                "Entering shell REPL mode with auto-approve enabled, commands will execute automatically. Press Ctrl+C to exit."
                if self.auto_approve
                else "Entering shell REPL mode, type [e] to execute commands "
                "or [d] to describe the commands, press Ctrl+C to exit."
            )
        )
        typer.secho(info_message, fg="yellow")

        if init_prompt:
            rich_print(Rule(title="Input", style="bold purple"))
            typer.echo(init_prompt)
            rich_print(Rule(style="bold purple"))

        full_completion = ""
        while True:
            # Infinite loop until user exits with Ctrl+C.
            prompt = typer.prompt(">>>", prompt_suffix=" ")
            if prompt == '"""':
                prompt = self._get_multiline_input()
            if prompt == "exit()":
                raise typer.Exit()
            if init_prompt:
                prompt = f"{init_prompt}\n\n\n{prompt}"
                init_prompt = ""
            if self.role.name == DefaultRoles.SHELL.value and prompt == "e":
                typer.echo()
                command_output = run_command(full_completion)
                # Add command output to chat context
                self.add_system_message(
                    f"Shell command executed:\n```\n{command_output}\n```"
                )
                typer.echo()
                rich_print(Rule(style="bold magenta"))
            elif self.role.name == DefaultRoles.SHELL.value and prompt == "d":
                DefaultHandler(
                    DefaultRoles.DESCRIBE_SHELL.get_role(), self.markdown
                ).handle(prompt=full_completion, **kwargs)
            else:
                full_completion = super().handle(prompt=prompt, **kwargs)

                # Auto-execute if auto_approve is enabled and in shell mode
                if self.auto_approve and self.role.name == DefaultRoles.SHELL.value:
                    # Check if the command is safe to auto-execute
                    if is_safe_to_auto_execute(full_completion, self.auto_approve):
                        typer.echo()
                        command_output = run_command(full_completion)
                        # Add command output to chat context
                        self.add_system_message(
                            f"Shell command executed:\n```\n{command_output}\n```"
                        )
                    else:
                        # Unsafe command detected - ask for confirmation
                        typer.secho("Potentially unsafe command detected:", fg="yellow")
                        typer.echo(full_completion)
                        option = typer.prompt(
                            text="[E]xecute, [A]bort",
                            type=Choice(("e", "a"), case_sensitive=False),
                            default="a",
                            show_choices=False,
                            show_default=False,
                        )
                        if option.lower() == "e":
                            typer.echo()
                            command_output = run_command(full_completion)
                            # Add command output to chat context
                            self.add_system_message(
                                f"Shell command executed:\n```\n{command_output}\n```"
                            )
                        else:
                            typer.secho("Command aborted.", fg="red")
                    typer.echo()
                    rich_print(Rule(style="bold magenta"))
