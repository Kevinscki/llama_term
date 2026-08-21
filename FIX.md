# llama_term repair plan

This is a repair backlog from the 2026-08-18 "is this dumb?" audit. The
project idea is sound; these items make the current prototype safer,
predictable, and easier to maintain.

## Implementation status (2026-08-20)

| Priority | Area | Status |
| --- | --- | --- |
| P0 | Credential handling | **Done** — `GEMINI_API` from env/`.env`; `.env.example`; `.gitignore`; key removed from source |
| P0 | Startup execution | **Done** — import-time PTY/`TEMP_SCRIPT` removed; `main()` + `if __name__` |
| P0 | Command protocol | **Done** — per-session random markers; exact trailer parse only |
| P0 | AI execution safety | **Done** — confirm by default; `a` = session non-risky only; risky always prompts |
| P0 | Included data privacy | **Done** — provider warning, 200k default cap, sensitive-path confirm |
| P1 | INCLUDE returncode | **Done** — AI on `returncode != 0`, not stderr alone |
| P1 | Backend resilience | **Done** — Ollama timeouts + raise_for_status; clean AI errors |
| P1 | Temp-file collisions | **Done** — per-process `RUNTIME_DIR` |
| P1 | PTY cleanup | **Done** — `run_ai_script_pty()` with `isatty` + FD/reap cleanup |
| P1 | Shell-state persistence | **Done** — removed per-line `set > .shellrc` spam |
| P1 | Logging | **Partial** — logs to `logs/session.log` (not BASH_LEGACY); still minimal |
| P2 | Parsing / architecture / CI | **Open** — see below |

## Scope and priority

All items are repairable in one focused implementation pass. Do the P0 items
before relying on the program with a cloud model or on a machine with valuable
data.

| Priority | Area | Problem | Required outcome |
| --- | --- | --- | --- |
| P0 | Credential handling | `GEMINI_API` is present in `configuration_variables.py`. It may be intentionally device-local, but source files are easy to stage, copy, or publish. | Read `GEMINI_API` from the environment first; retain an explicit local-only fallback only if wanted. Add `.env`/local config to `.gitignore` and document the setup. Rotate the current key before any remote push or sharing. |
| P0 | Startup execution | Importing `llama_shell.py` creates a PTY then executes `bash TEMP_SCRIPT` before any response generates that file. | Remove the global PTY/process creation at lines 336-353. Create the PTY only immediately before executing an approved AI script, and always close/reap it. |
| P0 | Command protocol | The persistent Bash parser treats normal stdout as control data: `---CMD_END--`, `PY_EXIT__CODE:`, and `PY_DIRECTORY__:` can be printed by any command. | Replace literal markers with a per-session random token and parse only exact, dedicated trailer records. Keep a byte buffer across reads. Do not treat arbitrary program output as a directory/status update. |
| P0 | AI execution safety | `a` enables sticky automatic execution; safety relies on a small keyword list that misses many destructive forms. | Make every model-generated script require confirmation by default. If an auto-run mode remains, scope it to one response/session, visibly show it is active, and use it only as convenience—not as a security guarantee. Add a clear high-risk confirmation for destructive/network-changing commands. |
| P0 | Included data privacy | `INCLUDE()` accepts arbitrary readable absolute paths and has no default size limit. Included text may be sent to Gemini when that backend is active. | Show the active provider and a cloud-data warning before sending included content. Apply a conservative byte cap, reject/confirm sensitive paths, and display the exact files and truncated sizes being shared. |
| P1 | Error correctness | `include_file()` invokes AI when stderr is non-empty, not when the command fails. A failed silent command is ignored; a successful warning is treated as failure. | Check `result.returncode != 0`, capture/display output consistently, and pass the actual exit code to `handle_error`. |
| P1 | Backend resilience | Ollama calls have no timeout; after `raise_for_status()` fails, the code continues attempting to parse streamed JSON. `invoke_ai()` does not handle normal request/JSON failures. | Set connect/read timeouts, call `raise_for_status()` outside a swallowed exception, validate JSON chunks, and catch `requests.RequestException`/decode errors at the UI boundary. Return a clean error without killing the REPL. |
| P1 | Temp-file collisions | `temp_script.sh`, `_paste_cmd.sh`, and error temp files have fixed names. Two sessions can overwrite or delete each other's files. | Use `tempfile.NamedTemporaryFile`/`mkstemp` or a per-process runtime directory. Clean up in `finally` blocks. |
| P1 | Terminal/process cleanup | PTY file descriptors and child processes are only partly cleaned up; raw-mode restoration assumes an interactive TTY. | Centralize PTY execution in a context-managed helper, close both FDs on every path, wait/reap children, and guard TTY manipulation with `isatty()`. |
| P1 | Shell-state persistence | `set > markdowns/.shellrc` is written after output lines, but the constructed `env` is never passed to any subprocess. This is wasted I/O and misleading state handling. | Remove the unused dotenv/state-file path, or intentionally load it and pass `env` to child processes. Do not keep shell state by repeatedly overwriting a tracked Markdown-adjacent file. |
| P1 | Logging | Help says failed commands and AI responses are logged, but approved AI execution appends only the generated Bash script. Logs are mixed into `BASH_LEGACY.md`. | Define a structured log format/location outside tool prompts; log the request, response, approval decision, exit status, and timestamps only when opted in. Never log credentials or included sensitive content. |
| P2 | Parsing | Bash-fence parsing and display parsing have custom nested-fence behavior that is hard to reason about and not tested. | Restrict the response contract to one top-level `bash` fence, make extraction deterministic, and add parser tests for no fence, malformed fence, multiple fences, and prose containing fences. |
| P2 | Architecture | `llama_shell.py` is a 1,394-line script with import-time side effects, wildcard configuration imports, globals, UI, transport, execution, and tool management intertwined. | Split into configuration, AI clients, shell session/protocol, execution/approval, embeds, and UI modules. Add a `main()` guarded by `if __name__ == "__main__"`. Replace wildcard imports with explicit dependencies. |
| P2 | UX/documentation | The README is stale and understates cloud-provider/privacy behavior, confirmation semantics, setup dependencies, and tool usage. | Update README with supported OS, Python version, installation, Ollama/Gemini configuration, privacy model, security boundaries, `ASK()`/`INCLUDE()`/`TOOL()` behavior, and known limitations. |
| P2 | Repository hygiene | The staged tree contains a virtual environment, caches, backup copies, reports, swap files, generated binaries, and a 2.5 MB legacy log. `install.sh` is a 1,181-line Homebrew installer rather than this project's installer. | Add `.gitignore`; unstage/remove generated and local artifacts from version control without deleting wanted local files; move sample reports to fixtures if needed; replace/remove misleading `install.sh`; keep a minimal source-only repository. |

## One-run implementation order

1. Create `.gitignore`, stop tracking local/generated artifacts, and move config
   secrets to environment-driven settings.
2. Introduce `main()` and remove import-time PTY execution.
3. Implement one shell-session helper with a randomized trailer protocol and
   guaranteed process/FD cleanup.
4. Implement a temporary-script helper with per-run files and explicit cleanup.
5. Tighten AI approval, include-data disclosure/limits, and backend error
   handling.
6. Correct `INCLUDE()` return-code handling and remove or repair the unused
   `.shellrc` persistence path.
7. Add tests, then update documentation and logs.

## Acceptance checks

- Starting and importing the module never runs a stale/generated script.
- Two simultaneous sessions do not share temporary files or corrupt one
  another's current directory/status.
- `echo '---CMD_END--'` and output resembling internal markers cannot end or
  corrupt a command transaction.
- An Ollama outage, invalid streamed JSON, and a Gemini error leave the REPL
  usable and show a concise error.
- `false` in `INCLUDE()` invokes failure handling; a successful command writing
  a warning to stderr does not.
- Every generated script prompts before execution under default settings.
- A cloud provider is visibly identified before any included file is sent, and
  oversized/sensitive paths require an explicit decision.
- The repository contains no virtualenv, bytecode, reports, swap files, secret
  values, or generated runtime logs.
- Unit tests cover response fence extraction, marker parsing, include argument
  parsing, risky-command classification, and tool/embed validation.

## Non-blocking cleanup

- Remove unused imports and dead settings (`shutil`, `readline`, `env`,
  `USER_ERROR_TEMP`, `DIR_FILE`, `EXIT_CODE_FILE`, and redundant color values
  if they remain unused after the refactor).
- Make path completion shell-aware or clearly describe its simple behavior.
- Put configuration defaults in a documented example file rather than mutable
  Python globals.
- Add formatting/linting and a small test suite to CI.
