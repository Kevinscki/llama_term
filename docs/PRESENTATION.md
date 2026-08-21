# Project Presentation — Slide Content (Strict Order)

**Source rules (Presentation Guidelines.pdf):**
- Bring a **completed, signed log form** (you + supervisor) to the panel.
- **15 minutes total:** ~4 minutes for slides, ~11 minutes for live project demonstration.
- PowerPoint **must not exceed 5 slides**.
- Slides must cover items (i)–(iv) below, then you demonstrate the system.
- Present only after **supervisor approval** (rp.pdf: at least two weeks before Semester II study week).

**Fill placeholders** (`[FULL NAME]`, `[REGISTRATION NUMBER]`, `[SUPERVISOR NAME]`, institute names) before exporting to PowerPoint.

**Candor for the panel:** llama_term is **not** a compiled shell binary. It is a Python AI-assisted interactive shell that drives a real `/bin/bash` subprocess, intervenes on failed commands, and optionally executes AI-proposed fixes after user confirmation.

---

## Slide 1 — Cover Page (Guideline i)

| Field | Content |
|--------|---------|
| Project title | **llama_term: An AI-Assisted Interactive Linux Shell** |
| Student full name | `[FULL NAME]` |
| Registration number | `[REGISTRATION NUMBER]` |
| Supervisor | `[SUPERVISOR NAME]` |
| Optional (keep small) | Faculty / Department · Final Year Project · `[ACADEMIC YEAR]` |

**Spoken (≈30–40 s):** State title, your name, registration number, and supervisor. One sentence: *“The system helps users recover from failed terminal commands using a local or remote LLM, with explicit human approval before running suggested fixes.”*

---

## Slide 2 — Introduction / Project Description (Guideline ii)

**Headline:** What the project is

**Bullets (keep sparse — 4 minutes for all slides):**

- **Problem:** Terminal users often fail commands (typos, missing tools, wrong flags) and must search elsewhere for fixes; context is lost.
- **Solution:** `llama_term` — a Python-driven interactive shell that:
  1. Runs user input through a persistent bash session.
  2. On non-zero exit, prompts an LLM with conversation history.
  3. Streams a suggested fix (markdown / `bash` blocks).
  4. Asks **y / n / a** before executing; risky lines force confirmation.
- **What it is not:** Not a replacement OS shell binary; it **emulates** a terminal workflow and wraps real bash.
- **Stack (one line):** Python 3 · prompt-toolkit · Rich · Ollama HTTP and/or Gemini · PTY for interactive AI scripts.

**Spoken (≈45–60 s):** Problem → approach → honesty about emulation vs compiled shell → one concrete example (*wrong hostname → AI suggests corrected `curl` → user confirms*).

---

## Slide 3 — Methodology (Guideline iii)

**Headline:** How the system was built and operates

**Bullets:**

- **Requirements → design → implementation → testing** (Informatics lifecycle).
- **Core loop:** `command → execute` → on failure → `AI suggest → user confirm → execute script`.
- **Modules:**
  - `llama_shell.py` — bash subprocess, error handler, tools, main REPL.
  - `configuration_variables.py` — model/API choice, paths, context length, risk keywords.
  - `ai_display.py` — streaming markdown, code panels, risk badges.
  - `markdowns/*.md` — swappable system prompts (“tools”).
- **Safety:** keyword scan (`rm`, `sudo`, `chmod`, pipes to shell, etc.); amber flags; no silent auto-run of risky suggestions.
- **Tools:** `TOOL()` / `ADD_TOOL()` swap or draft domain prompts; optional `embed_json` context injection under path allowlists.
- **Evaluation:** manual scenarios (list/find files, failed commands, tool switch, `BUMP()` / `LOAD()`).

**Spoken (≈60–75 s):** Walk the failure→AI→confirm path once. Name the three Python modules. Mention local Ollama as primary privacy-friendly backend.

---

## Slide 4 — Significance of the Project (Guideline iv)

**Headline:** Why it matters

**Bullets:**

- **Learning aid:** Explains and proposes shell fixes in context, useful for students and junior admins.
- **Productivity:** Reduces time spent debugging common CLI mistakes without leaving the terminal.
- **Privacy / control:** Prefer local Ollama; user always gates execution of AI-generated commands.
- **Extensibility:** Domain tools (Git, Docker, etc.) via markdown prompts — same shell, specialized behaviour.
- **Community value:** Open approach to safer AI-in-the-terminal (confirm-before-run + risk highlighting).
- **Honest limits:** LLM hallucinations possible; mitigated by `BUMP()`, short context (`MODEL_CONTEXT_LEN`), user review, and keyword gating — not a guarantee of correct or safe commands.

**Spoken (≈45–60 s):** Impact + limitations in the same breath. End with: *“Next I will demonstrate the live system.”*

---

## Slide 5 — Demonstration Roadmap (within 5-slide limit)

**Headline:** Live demo plan (11 minutes)

Use this slide only as a **checklist for you and the panel** — do not overcrowd it.

1. Start `python3 llama_shell.py` → banner / prompt.
2. Successful command (`ls` / `pwd`).
3. Deliberate failure → AI stream → show risk badge if any → **n** then **y**.
4. `TOOL() LIST` → `TOOL() GIT` (or similar) → one domain query.
5. `BUMP()` / `LOAD()` briefly; `HELP` if time.
6. Stop; invite questions.

**Spoken:** Almost none — switch to demo immediately.

---

## After the slides — Live project (≈11 minutes)

**Do:**
- Run from a clean venv; Ollama up (`OLLAMA_MODEL` matches what you pull).
- Show **user confirmation** clearly.
- If the model stalls, `BUMP()` and retry; have a pre-recorded fallback clip only if allowed by the panel.

**Do not:**
- Run destructive demos (`rm -rf`, uncontrolled `sudo`).
- Paste API keys or `.env` secrets on screen.
- Exceed the 5-slide / 4-minute slide budget by reading paragraphs.

**Bring:** Signed log form; working laptop; optional short backup video of a successful failure→fix cycle.
