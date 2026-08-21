# llama_term

AI-assisted interactive shell for UNIX-like systems. Commands run in a persistent
bash session; on failure (or via `ASK()`), a local Ollama model — or optional
Gemini — proposes a fix. You confirm before any model-generated script runs.

## Requirements

- Python 3.10+
- Linux / UNIX-like terminal (Parrot, Debian, Ubuntu, …)
- [Ollama](https://ollama.ai/) for local inference (default)

```bash
git clone https://github.com/Kevinscki/llama_term.git
cd llama_term
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional; required for Gemini
python3 llama_shell.py
```

## Configuration

| Variable | Meaning |
|----------|---------|
| `API_TYPE` | `ollama_http` (default) or `gemini` |
| `OLLAMA_MODEL` / `OLLAMA_URL` | Local chat endpoint |
| `GEMINI_API` / `GEMINI_MODEL` | Cloud Gemini (set in `.env`, never commit) |
| `MAX_INCLUDE_BYTES` | Cap for `INCLUDE()` (default 200000) |

Secrets come from the environment or `.env` (see `.env.example`). Rotate any key
that was previously stored in source.

## Privacy

- Default backend is **local Ollama**.
- If `API_TYPE=gemini`, included files and failure context are sent to Google.
  `INCLUDE()` warns and asks before cloud sends.
- Keyword risk scanning is a convenience aid, **not** a security boundary.

## Core commands

| Command | Purpose |
|---------|---------|
| `ASK() …` | Ask the model; it generates bash from live context |
| `FLAGS()` | Toggle `repeat` / `embed` / `exitcode` context markers |
| `INCLUDE() file` | Attach file(s) for AI context (size + sensitive-path gates) |
| `TOOL() NAME` | Switch domain prompt (`DOCKER`, `PENTEST`, …) |
| `BUMP()` | Clear chat turns; keep tool + live embeds |
| `LOAD()` | Warm the model |
| `y` / `n` / `a` | Confirm AI script — `a` = session auto-run for **non-risky** only |
| `c` / `v` / `t` | Copy script to clipboard · view it · run captured and attach STDOUT/STDERR to context |
| `1-9` | Multiple blocks: run just that block |

## Real TTY mode

The persistent shell is pipe-based so state survives every command, but
TTY-hungry programs (vim, less, htop, ssh, python REPL, …) are wrapped in
`script(1)` at run time — each gets a fresh PTY *inside* the persistent bash,
so colors and full-screen UIs work while `cd`, env vars and functions still
persist. Set `LLAMA_REALTTY=auto|always|off` (default `auto`).

## Safety model

- Every model script prompts before run by default.
- Risky keyword hits always require an explicit `y` (session auto-run cannot bypass).
- Shell control trailers use a per-session random token (normal output cannot spoof them).
- Runtime files live under a per-process temp directory.

## Known limitations

- TTY wrapping is per-command (`script(1)`); a wrapped command's output is
  relayed line-by-line, so exotic full-screen redraws can look slightly off.
- AI suggestions can be wrong — always review before `y`.
- See `FIX.md` for the repair backlog and remaining P2 work.
