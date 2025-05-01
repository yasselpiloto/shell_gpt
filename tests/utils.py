from typer import Typer
from typer.testing import CliRunner

from sgpt.app import main
from sgpt.utils import run_command

# Typer app for testing
app = Typer()
app.command()(main)

# CLI runner for invoking commands
runner = CliRunner(mix_stderr=False)


# Helper to convert dict to CLI args
def cmd_args(**kwargs):
    args = []
    for k, v in kwargs.items():
        if k.startswith("--"):
            args.append(k)
            if v is not True:
                args.append(str(v))
        else:
            args.append(str(v))
    return args


# Stub for completion args (accepts extra kwargs)
def comp_args(
    role,
    prompt,
    messages=None,
    model="gpt-4o",
    temperature=0.0,
    top_p=1.0,
    stream=True,
    **kwargs,
):
    # Always use messages, as the actual call uses messages, not role/prompt directly
    if messages is None:
        # If messages not provided, construct a default messages list
        messages = [
            {"role": "system", "content": getattr(role, "role", str(role))},
            {"role": "user", "content": prompt},
        ]
    args = {
        "model": model,
        "temperature": temperature,
        "top_p": top_p,
        "messages": messages,
        "stream": stream,
    }
    args.update(kwargs)
    return args


# Stub for mocking completion return values
def mock_comp(output):
    """Create a mock completion generator that yields chunks with the expected structure.

    The handler expects each chunk to have:
    - choices[0].delta.content
    - choices[0].finish_reason
    """
    import sys

    print(f"mock_comp called with output: {output}", file=sys.stderr)

    # Create a generator function that yields strings
    def generator():
        yield output

    # Return the generator
    return generator()


def test_run_command_captures_output():
    """Test that run_command captures and returns command output."""
    # Use echo command as it's available on all platforms
    result = run_command("echo 'test output'")
    assert "Command: echo 'test output'" in result
    assert "test output" in result
    assert "Exit code:" in result


def test_run_command_handles_errors():
    """Test that run_command properly captures error output and codes."""
    # Use a command that will fail
    result = run_command("command_that_does_not_exist")
    assert "Command: command_that_does_not_exist" in result
    assert "Exit code:" in result
    # The exact error message differs by OS, so just check it has some content
    assert len(result) > 50
