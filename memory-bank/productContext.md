# Product Context: ShellGPT

**Why this project exists:**  
- Developers frequently forget shell syntax, waste time searching for commands, and risk running unsafe commands.
- ShellGPT automates command/code generation, documentation, and explanations, reducing friction and context switching.

**Problems Solved:**  
- Eliminates need for external search for shell/code snippets.
- Reduces risk of running destructive commands.
- Provides conversational, context-aware CLI assistance.

**How it should work:**  
- Accepts prompts via CLI, stdin, or REPL.
- Generates shell commands, code, or documentation using LLMs.
- Supports chat and REPL sessions with persistent context.
- **Allows seamless question asking within shell workflows using `??` trigger.**
- Integrates with shell for completions and direct execution.
- Enforces safety via confirmation for sensitive commands.

**User Experience Goals:**  
- Fast, low-latency responses.
- Clear, actionable output (code, commands, explanations).
- Interactive, multi-turn sessions (chat/REPL).
- **Enhanced visual distinction between shell commands and general questions.**
- Extensible: user roles, functions, safety config.
- Safe by default, with user control over risk.
- **Comprehensive test coverage ensuring reliability and preventing regressions.**
