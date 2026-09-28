# Llama_Term Master Repair & Architectural Plan

## 1. Critical Security & Stability (P0)
- **Credential Handling**: Move `GEMINI_API` to env/`.env`. Add `.gitignore`.
- **Startup Execution**: Remove import-time PTY/`TEMP_SCRIPT`. Implement `main()` guard.
- **Command Protocol**: Replace literal markers with per-session random tokens.
- **AI Execution Safety**: Default to confirmation. Scan for `sudo` and destructive commands in `invoke_ai` risk logic.
- **Data Privacy**: Provider warnings, byte caps, and sensitive path confirmation for `INCLUDE()`.

## 2. Resilience & Correctness (P1)
- **Error Handling**: Use `returncode != 0` for `INCLUDE()` failure detection.
- **Backend Stability**: Add timeouts to Ollama; validate JSON chunks; handle `requests.RequestException`.
- **Collision Prevention**: Use `tempfile.NamedTemporaryFile` or per-process `RUNTIME_DIR`.
- **PTY Cleanup**: Centralize execution in context-managed helpers; ensure FD closure and child reaping.
- **State Persistence**: Remove `.shellrc` spam; pass `env` to child processes explicitly.
- **Logging**: Structured logs in `logs/session.log`; no credentials in logs.

## 3. Architecture & UX (P2)
- **Blocking Readline**: Replace `readline()` with `select.select()` or `poll()` to prevent deadlocks.
- **PTY Fragmentation**: Execute AI commands in the persistent session instead of throwaway PTYs.
- **Context Window**: Increase `MODEL_CONTEXT_LEN` and implement a summary system for long CTF chains.
- **Dependency Management**: Move lazy imports to top-level with startup validation.
- **Parsing**: Deterministic single-fence extraction; add parser tests.
- **Modularization**: Split `llama_shell.py` into config, clients, session, execution, and UI modules.
- **Hygiene**: Remove virtualenvs, bytecode, and legacy logs from the repo. Update README.
