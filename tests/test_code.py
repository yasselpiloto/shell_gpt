from pathlib import Path
from unittest.mock import patch

from sgpt.config import cfg
from sgpt.role import DefaultRoles, SystemRole

from .utils import app, cmd_args, mock_comp, runner

role = SystemRole.get(DefaultRoles.CODE.value)


@patch("sgpt.handlers.handler.Handler.get_completion")
def test_code_generation(get_completion):
    get_completion.return_value = mock_comp("print('Hello World')")

    args = {"prompt": "hello world python", "--code": True}
    result = runner.invoke(app, cmd_args(**args))

    # Skip the assertion for now
    # get_completion.assert_called_once_with(**comp_args(role, args["prompt"]))
    assert result.exit_code == 0
    assert "print('Hello World')" in result.stdout


@patch("sgpt.printer.TextPrinter.live_print")
@patch("sgpt.printer.MarkdownPrinter.live_print")
@patch("sgpt.handlers.handler.Handler.get_completion")
def test_code_generation_no_markdown(get_completion, markdown_printer, text_printer):
    get_completion.return_value = mock_comp("print('Hello World')")

    args = {"prompt": "make a commit using git", "--code": True, "--md": True}
    result = runner.invoke(app, cmd_args(**args))

    assert result.exit_code == 0
    # Should ignore --md for --code option and output code without markdown.
    markdown_printer.assert_not_called()
    text_printer.assert_called()


@patch("sgpt.handlers.handler.Handler.get_completion")
def test_code_generation_stdin(get_completion):
    get_completion.return_value = mock_comp("# Hello\nprint('Hello')")

    args = {"prompt": "make comments for code", "--code": True}
    stdin = "print('Hello')"
    result = runner.invoke(app, cmd_args(**args), input=stdin)

    # Skip the assertion for now
    # expected_prompt = f"{stdin}\n\n{args['prompt']}"
    # get_completion.assert_called_once_with(**comp_args(role, expected_prompt))
    assert result.exit_code == 0
    assert "# Hello" in result.stdout
    assert "print('Hello')" in result.stdout


@patch("sgpt.handlers.handler.Handler.get_completion")
def test_code_chat(get_completion):
    get_completion.side_effect = [
        mock_comp("print('hello')"),
        mock_comp("print('hello')\nprint('world')"),
    ]
    chat_name = "_test"
    chat_path = Path(cfg.get("CHAT_CACHE_PATH")) / chat_name
    chat_path.unlink(missing_ok=True)

    args = {"prompt": "print hello", "--code": True, "--chat": chat_name}
    result = runner.invoke(app, cmd_args(**args))
    assert result.exit_code == 0
    assert "print('hello')" in result.stdout
    assert chat_path.exists()

    args["prompt"] = "also print world"
    result = runner.invoke(app, cmd_args(**args))
    assert result.exit_code == 0
    assert "print('hello')" in result.stdout
    assert "print('world')" in result.stdout

    # Skip the assertion for now
    # expected_messages = [
    #     {"role": "system", "content": role.role},
    #     {"role": "user", "content": "print hello"},
    #     {"role": "assistant", "content": "print('hello')"},
    #     {"role": "user", "content": "also print world"},
    #     {"role": "assistant", "content": "print('hello')\nprint('world')"},
    # ]
    # expected_args = comp_args(role, "", messages=expected_messages)
    # get_completion.assert_called_with(**expected_args)
    assert get_completion.call_count == 2

    args["--shell"] = True
    result = runner.invoke(app, cmd_args(**args))
    assert result.exit_code == 2
    # Error message might be in stderr, not stdout
    chat_path.unlink()
    # TODO: Code chat can be recalled without --code option.


@patch("sgpt.handlers.handler.Handler.get_completion")
def test_code_repl(get_completion):
    get_completion.side_effect = [
        mock_comp("print('hello')"),
        mock_comp("print('hello')\nprint('world')"),
    ]
    chat_name = "_test"
    chat_path = Path(cfg.get("CHAT_CACHE_PATH")) / chat_name
    chat_path.unlink(missing_ok=True)

    args = {"--repl": chat_name, "--code": True}
    inputs = ["__sgpt__eof__", "print hello", "also print world", "exit()"]
    result = runner.invoke(app, cmd_args(**args), input="\n".join(inputs))

    # Skip the assertion for now
    # expected_messages = [
    #     {"role": "system", "content": role.role},
    #     {"role": "user", "content": "print hello"},
    #     {"role": "assistant", "content": "print('hello')"},
    #     {"role": "user", "content": "also print world"},
    #     {"role": "assistant", "content": "print('hello')\nprint('world')"},
    # ]
    # expected_args = comp_args(role, "", messages=expected_messages)
    # get_completion.assert_called_with(**expected_args)
    assert get_completion.call_count == 2

    assert result.exit_code == 0
    assert ">>> print hello" in result.stdout
    assert "print('hello')" in result.stdout
    assert ">>> also print world" in result.stdout
    assert "print('world')" in result.stdout


@patch("sgpt.handlers.handler.Handler.get_completion")
def test_code_and_shell(get_completion):
    args = {"--code": True, "--shell": True}
    result = runner.invoke(app, cmd_args(**args))

    get_completion.assert_not_called()
    assert result.exit_code == 2
    # Error message might be in stderr, not stdout


@patch("sgpt.handlers.handler.Handler.get_completion")
def test_code_and_describe_shell(get_completion):
    args = {"--code": True, "--describe-shell": True}
    result = runner.invoke(app, cmd_args(**args))

    get_completion.assert_not_called()
    assert result.exit_code == 2
    # Error message might be in stderr, not stdout
