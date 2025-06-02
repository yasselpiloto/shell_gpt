# System Patterns: ShellGPT

**Architecture:**  
- Modular, handler-based CLI using Typer.
- Core flow: CLI → app.py → Handler (Default/Chat/REPL) → LLM/Function/Cache/Safety.

**Key Patterns:**  
- **Handler Pattern:** Separate classes for chat, REPL, and default flows.
- **Decorator Pattern:** Used for request and chat caching.
- **Config/Factory Pattern:** Centralized config, dynamic role/function loading.
- **Safety Layer:** YAML-driven, user-customizable command safety.

**Component Relationships:**  
- CLI entry (sgpt) → app.py (Typer) → Handler (Default/Chat/REPL)
- Handlers interact with:  
  - LLM API (OpenAI/local)  
  - Function calls (user/system)  
  - Request cache (per prompt)  
  - ChatSession (per chat/repl)  
  - Command safety (global, YAML-configurable)  
  - Config (global, user-editable)

**Critical Implementation Paths:**  
- All user input flows through app.py main(), which dispatches to the correct handler.
- Handlers manage context, caching, and output formatting.
- Safety checks are enforced before command execution.

```mermaid
flowchart TD
    CLI["sgpt (Typer CLI)"]
    CLI --> App["app.py: main()"]
    App -->|mode: shell/code/chat/repl| Handler
    Handler -->|Default| DefaultHandler
    Handler -->|Chat| ChatHandler
    Handler -->|REPL| ReplHandler
    Handler --> LLM["OpenAI/LLM API"]
    Handler --> Function["Function Calls"]
    Handler --> Cache["Request Cache"]
    Handler --> ChatSession["ChatSession (per chat/repl)"]
    Handler --> Safety["Command Safety"]
    App --> Config["Config"]
    Config --> Safety
    Config --> Cache
    Config --> ChatSession
