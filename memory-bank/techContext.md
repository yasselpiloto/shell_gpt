# Tech Context: ShellGPT

**Languages:**  
- Python 3.10+

**Core Libraries:**  
- openai (LLM API)
- typer, click (CLI)
- rich (output formatting)
- instructor (function calling)
- pyyaml (config/safety)
- distro (OS detection)

**Dev Tools:**  
- ruff, black, mypy, pytest, isort, codespell, poethepoet
- **pytest for comprehensive testing (unit, integration, edge cases)**

**Dependencies:**  
- Managed by Poetry (pyproject.toml)
- Optional: litellm for local LLMs
- **pytest for test framework and assertions**

**Development Setup:**  
- Install via pip or poetry.
- Config: ~/.config/shell_gpt/.sgptrc (runtime), YAML for safety, tempdir for cache.
- Roles/functions: ~/.config/shell_gpt/roles, ~/.config/shell_gpt/functions
- **Testing: `python -m pytest tests/ -p no:warnings` for full test suite**

**Technical Constraints:**  
- Python >=3.10
- LLM API key required (OpenAI or local backend)
- Cross-platform shell support
- **Test coverage requirements for all new features**

**Tool Usage Patterns:**  
- Typer for CLI parsing and command dispatch.
- Decorators for caching (request, chat).
- Handlers for chat, REPL, and default flows.
- YAML for user-editable safety config.
- Extensible via user roles, functions, and config.
- **Comprehensive test patterns: unit tests, integration tests, edge case testing**
- **Mock patching for external dependencies (LLM completions, file operations)**
