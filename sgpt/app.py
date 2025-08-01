import os
from typing import List

# To allow users to use arrow keys in the REPL.
import readline  # noqa: F401
import sys

import typer
from click import BadArgumentUsage
from click.types import Choice

from sgpt.command_safety import (
    add_to_approve_list,
    add_to_confirm_list,
    get_safety_config_display,
    remove_from_approve_list,
    remove_from_confirm_list,
)
from sgpt.config import cfg
from sgpt.function import get_openai_schemas
from sgpt.handlers.chat_handler import ChatHandler
from sgpt.handlers.default_handler import DefaultHandler
from sgpt.handlers.repl_handler import ReplHandler
from sgpt.llm_functions.init_functions import install_functions as inst_funcs
from sgpt.role import DefaultRoles, SystemRole
from sgpt.utils import (
    get_edited_prompt,
    get_sgpt_version,
    install_shell_integration,
    run_command,
)


app = typer.Typer()


@app.command()
def safety_config(
    add_to_approve: List[str] = typer.Option(
        [], "--add-approve", help="Add commands to always-approve list"
    ),
    add_to_confirm: List[str] = typer.Option(
        [], "--add-confirm", help="Add commands to always-confirm list"
    ),
    remove_from_approve: List[str] = typer.Option(
        [], "--remove-approve", help="Remove commands from always-approve list"
    ),
    remove_from_confirm: List[str] = typer.Option(
        [], "--remove-confirm", help="Remove commands from always-confirm list"
    ),
    show: bool = typer.Option(
        False, "--show", "-s", help="Show current safety configuration"
    ),
) -> None:
    """
    Manage command safety configuration for auto-approve feature.
    
    This command allows you to configure which commands should always require confirmation
    and which commands can be automatically approved when using --auto-approve.
    """
    # Process command additions/removals
    if add_to_approve:
        add_to_approve_list(add_to_approve)
        typer.echo(f"Added {', '.join(add_to_approve)} to always-approve list")
    
    if add_to_confirm:
        add_to_confirm_list(add_to_confirm)
        typer.echo(f"Added {', '.join(add_to_confirm)} to always-confirm list")
    
    if remove_from_approve:
        remove_from_approve_list(remove_from_approve)
        typer.echo(f"Removed {', '.join(remove_from_approve)} from always-approve list")
    
    if remove_from_confirm:
        remove_from_confirm_list(remove_from_confirm)
        typer.echo(f"Removed {', '.join(remove_from_confirm)} from always-confirm list")
    
    # Show configuration if requested or if no other action was performed
    if show or not any([add_to_approve, add_to_confirm, remove_from_approve, remove_from_confirm]):
        typer.echo(get_safety_config_display())


@app.command()
def main(
    prompt: str = typer.Argument(
        "",
        show_default=False,
        help="The prompt to generate completions for.",
    ),
    model: str = typer.Option(
        cfg.get("DEFAULT_MODEL"),
        help="Large language model to use.",
    ),
    temperature: float = typer.Option(
        0.0,
        min=0.0,
        max=2.0,
        help="Randomness of generated output.",
    ),
    top_p: float = typer.Option(
        1.0,
        min=0.0,
        max=1.0,
        help="Limits highest probable tokens (words).",
    ),
    md: bool = typer.Option(
        cfg.get("PRETTIFY_MARKDOWN") == "true",
        help="Prettify markdown output.",
    ),
    shell: bool = typer.Option(
        False,
        "--shell",
        "-s",
        help="Generate and execute shell commands.",
        rich_help_panel="Assistance Options",
    ),
    interaction: bool = typer.Option(
        cfg.get("SHELL_INTERACTION") == "true",
        help="Interactive mode for --shell option.",
        rich_help_panel="Assistance Options",
    ),
    auto_approve: bool = typer.Option(
        False,
        "--auto-approve",
        help="Auto-approve and execute commands in REPL mode without prompting.",
        rich_help_panel="Assistance Options",
    ),
    describe_shell: bool = typer.Option(
        False,
        "--describe-shell",
        "-d",
        help="Describe a shell command.",
        rich_help_panel="Assistance Options",
    ),
    code: bool = typer.Option(
        False,
        "--code",
        "-c",
        help="Generate only code.",
        rich_help_panel="Assistance Options",
    ),
    functions: bool = typer.Option(
        cfg.get("OPENAI_USE_FUNCTIONS") == "true",
        help="Allow function calls.",
        rich_help_panel="Assistance Options",
    ),
    editor: bool = typer.Option(
        False,
        help="Open $EDITOR to provide a prompt.",
    ),
    cache: bool = typer.Option(
        True,
        help="Cache completion results.",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        help="Show version.",
        callback=get_sgpt_version,
    ),
    chat: str = typer.Option(
        None,
        help="Follow conversation with id, " 'use "temp" for quick session.',
        rich_help_panel="Chat Options",
    ),
    repl: str = typer.Option(
        None,
        help="Start a REPL (Read–eval–print loop) session.",
        rich_help_panel="Chat Options",
    ),
    show_chat: str = typer.Option(
        None,
        help="Show all messages from provided chat id.",
        rich_help_panel="Chat Options",
    ),
    list_chats: bool = typer.Option(
        False,
        "--list-chats",
        "-lc",
        help="List all existing chat ids.",
        callback=ChatHandler.list_ids,
        rich_help_panel="Chat Options",
    ),
    role: str = typer.Option(
        None,
        help="System role for GPT model.",
        rich_help_panel="Role Options",
    ),
    create_role: str = typer.Option(
        None,
        help="Create role.",
        callback=SystemRole.create,
        rich_help_panel="Role Options",
    ),
    show_role: str = typer.Option(
        None,
        help="Show role.",
        callback=SystemRole.show,
        rich_help_panel="Role Options",
    ),
    list_roles: bool = typer.Option(
        False,
        "--list-roles",
        "-lr",
        help="List roles.",
        callback=SystemRole.list,
        rich_help_panel="Role Options",
    ),
    install_integration: bool = typer.Option(
        False,
        help="Install shell integration (ZSH and Bash only)",
        callback=install_shell_integration,
        hidden=True,  # Hiding since should be used only once.
    ),
    install_functions: bool = typer.Option(
        False,
        help="Install default functions.",
        callback=inst_funcs,
        hidden=True,  # Hiding since should be used only once.
    ),
) -> None:
    stdin_passed = not sys.stdin.isatty()

    if stdin_passed:
        stdin = ""
        # TODO: This is very hacky.
        # In some cases, we need to pass stdin along with inputs.
        # When we want part of stdin to be used as a init prompt,
        # but rest of the stdin to be used as a inputs. For example:
        # echo "hello\n__sgpt__eof__\nThis is input" | sgpt --repl temp
        # In this case, "hello" will be used as a init prompt, and
        # "This is input" will be used as "interactive" input to the REPL.
        # This is useful to test REPL with some initial context.
        for line in sys.stdin:
            if "__sgpt__eof__" in line:
                break
            stdin += line
        prompt = f"{stdin}\n\n{prompt}" if prompt else stdin
        try:
            # Switch to stdin for interactive input.
            if os.name == "posix":
                sys.stdin = open("/dev/tty", "r")
            elif os.name == "nt":
                sys.stdin = open("CON", "r")
        except OSError:
            # Non-interactive shell.
            pass

    if show_chat:
        ChatHandler.show_messages(show_chat, md)

    if sum((shell, describe_shell, code)) > 1:
        raise BadArgumentUsage(
            "Only one of --shell, --describe-shell, and --code options can be used at a time."
        )

    if chat and repl:
        raise BadArgumentUsage("--chat and --repl options cannot be used together.")

    if editor and stdin_passed:
        raise BadArgumentUsage("--editor option cannot be used with stdin input.")

    if editor:
        prompt = get_edited_prompt()

    role_class = (
        DefaultRoles.check_get(shell, describe_shell, code)
        if not role
        else SystemRole.get(role)
    )

    function_schemas = (get_openai_schemas() or None) if functions else None

    if repl:
        # Will be in infinite loop here until user exits with Ctrl+C.
        ReplHandler(repl, role_class, md, auto_approve).handle(
            init_prompt=prompt,
            model=model,
            temperature=temperature,
            top_p=top_p,
            caching=cache,
            functions=function_schemas,
        )

    if chat:
        full_completion = ChatHandler(chat, role_class, md).handle(
            prompt=prompt,
            model=model,
            temperature=temperature,
            top_p=top_p,
            caching=cache,
            functions=function_schemas,
        )
    else:
        full_completion = DefaultHandler(role_class, md).handle(
            prompt=prompt,
            model=model,
            temperature=temperature,
            top_p=top_p,
            caching=cache,
            functions=function_schemas,
        )

    while shell and interaction:
        option = typer.prompt(
            text="[E]xecute, [D]escribe, [A]bort",
            type=Choice(("e", "d", "a", "y"), case_sensitive=False),
            default="e" if cfg.get("DEFAULT_EXECUTE_SHELL_CMD") == "true" else "a",
            show_choices=False,
            show_default=False,
        )
        if option in ("e", "y"):
            # "y" option is for keeping compatibility with old version.
            run_command(full_completion)
        elif option == "d":
            DefaultHandler(DefaultRoles.DESCRIBE_SHELL.get_role(), md).handle(
                full_completion,
                model=model,
                temperature=temperature,
                top_p=top_p,
                caching=cache,
                functions=function_schemas,
            )
            continue
        break


def entry_point() -> None:
    # Run the main command directly, so all options are available at the root level.
    from typer import run
    run(main)


if __name__ == "__main__":
    entry_point()
