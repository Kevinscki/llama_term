# Final Year Project Report — Strict Format Draft

**Purpose of this file:** Working draft of the bound final report, structured exactly as required by:
- `rp.pdf` — Final Year Project Requirements (structure + submission rules)
- `APPENDIX A - PROJECT REPORT FORMAT AND GUIDE.pdf` — Preliminary pages, Chapters 1–3 (Informatics), References (Harvard), Appendices

**Submission rule (rp.pdf):** Submit the printed/bound report and a CD of the developed system **only after** a successful project presentation.

**Candor:** Content below describes the **actual** system in the repository. llama_term is an AI-assisted interactive shell implemented in Python; it is **not** a from-scratch compiled shell. Replace all `[PLACEHOLDERS]` before printing. Do **not** put API keys or secrets in the printed report or on the CD.

---

# (I) PRELIMINARY PAGES

## a) Cover page

*(Exact order required by Appendix A)*

1. Name of the Institute: `[NAME OF THE INSTITUTE]`
2. Name of department: `[NAME OF DEPARTMENT / Faculty of Informatics]`
3. Title of the project report: **llama_term: An AI-Assisted Interactive Linux Shell for Error Recovery and Domain Tools**
4. Name of the student: `[FULL NAME]`
5. Student’s registration number: `[REGISTRATION NUMBER]`
6. Programme: `[PROGRAMME NAME]`
7. Student’s year of study: `[YEAR OF STUDY]`
8. Project duration: `[e.g. Semester I–II, ACADEMIC YEAR]`

---

## b) Acknowledgement

I wish to acknowledge my project supervisor, `[SUPERVISOR NAME]`, for guidance, scheduled meetings, and approval to present. I also thank `[lecturers / peers / lab technicians as applicable]` for technical advice, and the open-source communities behind Ollama, prompt-toolkit, and Rich. Any remaining errors in design or documentation are my own.

---

## c) Summary / Abstract

**llama_term** is a Final Year Project that implements an AI-assisted interactive shell for UNIX-like systems. The user types commands in a prompt similar to a normal terminal. Commands are executed in a persistent `/bin/bash` subprocess. When a command fails (non-zero exit status), the application sends the failure context to a large language model (primarily via a local Ollama HTTP chat API, with optional Gemini support), streams the model’s response in the terminal, extracts proposed `bash` code blocks, and asks the user to confirm before execution (`y` / `n` / `a` for always).

The system adds a **tool** mechanism: specialised system prompts stored as markdown files can be listed, switched (`TOOL()`), or drafted with AI assistance (`ADD_TOOL()`). Optional structured embeds can inject constrained file, tree, or allowlisted command output into the model context. A display module renders streaming markdown, syntax-highlighted code, and **risk badges** when dangerous keywords appear in the suggestion.

**Major challenges** included keeping the bash session and working directory consistent; streaming and parsing nested markdown fences; reducing unsafe automatic execution; and limiting hallucinated or overly long model context. **Conclusions:** the project delivers a usable complete system that integrates programming, operating systems, and applied AI. **Recommendations:** strengthen automated tests, harden sandboxing of AI-generated scripts, and expand curated tools for teaching.

**Keywords:** interactive shell, large language models, Ollama, error recovery, human-in-the-loop, Python.

---

## d) Table of contents

*(Generate in Word/LibreOffice from headings; page numbers when finalising the bound copy.)*

| Item | Page |
|------|------|
| Cover page | |
| Acknowledgement | |
| Summary/Abstract | |
| Table of contents | |
| List of Figures | |
| List of Tables | |
| List of acronyms/abbreviations | |
| Chapter 1: Introduction | |
| &nbsp;&nbsp;&nbsp;1.1 Background Information | |
| &nbsp;&nbsp;&nbsp;1.2 Project Description | |
| &nbsp;&nbsp;&nbsp;1.3 Project Objectives | |
| Chapter 2: Main Body | |
| &nbsp;&nbsp;&nbsp;2.1 Requirements Specification | |
| &nbsp;&nbsp;&nbsp;2.2 Requirements Analysis | |
| &nbsp;&nbsp;&nbsp;2.3 System Design | |
| &nbsp;&nbsp;&nbsp;2.4 System Implementation | |
| &nbsp;&nbsp;&nbsp;2.5 System Testing | |
| Chapter 3: Conclusion and Recommendation | |
| References | |
| Appendices | |
| Log File | |

---

## e) List of Figures

*(Caption figures at the bottom; number by chapter, e.g. Figure 2.1.)*

| Figure | Caption | Page |
|--------|---------|------|
| Figure 1.1 | Conceptual flow: command success vs failure→AI→confirm | |
| Figure 2.1 | High-level architecture of llama_term | |
| Figure 2.2 | Sequence: failed command to optional script execution | |
| Figure 2.3 | Screenshot of startup banner and prompt | |
| Figure 2.4 | Screenshot of streamed AI suggestion and confirm prompt | |

---

## f) List of Tables

| Table | Header | Page |
|-------|--------|------|
| Table 2.1 | Functional requirements | |
| Table 2.2 | Non-functional requirements | |
| Table 2.3 | Main modules and responsibilities | |
| Table 2.4 | Built-in AI/shell control commands | |
| Table 2.5 | Sample test cases and results | |

---

## g) List of acronyms / abbreviations

| Acronym | Full meaning |
|---------|----------------|
| AI | Artificial Intelligence |
| API | Application Programming Interface |
| CLI | Command-Line Interface |
| FYP | Final Year Project |
| GFM | GitHub Flavoured Markdown |
| HTTP | Hypertext Transfer Protocol |
| LLM | Large Language Model |
| OS | Operating System |
| PTY | Pseudo-Terminal |
| REPL | Read–Eval–Print Loop |
| UI | User Interface |

---

# (II) MAIN BODY

# Chapter 1: Introduction

## 1.1 Background Information

Command-line interfaces remain central to system administration, software development, and cybersecurity education. Learners and practitioners frequently encounter failed commands caused by typos, incorrect paths, missing packages, or misunderstood syntax. Traditional recovery requires reading man pages, searching the web, or asking peers—activities that interrupt the terminal workflow and discard useful local context (current directory, recent errors, active tools).

Recent advances in large language models make it feasible to generate candidate shell fixes from natural language and error context. However, unconstrained automatic execution of model output is unsafe: models hallucinate, invent flags, and may propose destructive operations. A practical system therefore needs a **human-in-the-loop** gate, transparent display of suggestions, and highlighting of high-risk patterns.

This project sits at the intersection of operating systems (process control, PTY, environment), software engineering (modular design, configuration), and applied AI (local inference via Ollama, streaming chat APIs).

## 1.2 Project Description

**llama_term** is a Python application that presents an interactive shell experience. It:

- Maintains a long-lived bash process and tracks the working directory and exit codes via sentinel markers.
- On failure, builds a chat history (system prompt + recent turns) and calls the configured AI backend.
- Streams the response through a Rich-based display layer, flags risky keywords, extracts `bash` fenced blocks into a temporary script, and prompts the user before running that script under a PTY when accepted.
- Supports specialised “tools” as markdown system prompts under `markdowns/`, including listing, switching, AI-assisted creation, and optional constrained context embeds.

The project deliberately does **not** claim to reimplement bash itself. It **orchestrates** bash and an LLM to assist the user.

## 1.3 Project Objectives

1. Design and implement a complete interactive system that executes user shell commands and recovers from failures with AI assistance under user confirmation.
2. Provide configurable AI backends (local Ollama HTTP chat; optional cloud Gemini) without changing the core shell loop.
3. Implement streaming terminal presentation of model output (prose, tables, code, risk indicators).
4. Implement a tool/prompt system for domain-specialised assistance (`TOOL()`, `ADD_TOOL()`).
5. Apply basic safety controls (risk keywords, forced confirmation on risky suggestions, path constraints for embeds).
6. Document, test through representative scenarios, and prepare the work for FYP presentation and submission.

---

# Chapter 2: Main Body

*(Appendix A — Informatics: methodology plus sections a–e below.)*

**Methodology overview:** The project followed an iterative software development approach: requirements gathering from observed CLI pain points; analysis and prioritisation; modular design; implementation in Python against a live bash subprocess; manual and scenario-based testing; refinement of prompts, context length, and safety keywords.

## 2.1 Requirements Specification

### Functional requirements (Table 2.1)

| ID | Requirement |
|----|-------------|
| FR1 | Accept interactive command input with path/command completion. |
| FR2 | Execute commands in a persistent bash session and display output. |
| FR3 | Detect non-zero exit status and invoke AI error handling. |
| FR4 | Stream AI responses to the terminal with readable formatting. |
| FR5 | Extract `bash` code blocks and optionally execute after user confirmation. |
| FR6 | Flag suggestions containing configured dangerous keywords. |
| FR7 | Support context reset (`BUMP()`), model warm-up (`LOAD()`), help, and banner. |
| FR8 | Support tool list/switch and AI-assisted tool drafting. |
| FR9 | Allow attaching a file as reference context (`INCLUDE()`). |
| FR10 | Persist configuration for model name, paths, and context length. |

### Non-functional requirements (Table 2.2)

| ID | Requirement |
|----|-------------|
| NFR1 | Prefer local inference for privacy when Ollama is used. |
| NFR2 | User must remain in control of executing AI-generated commands. |
| NFR3 | Usable on UNIX-like systems; Windows not a primary target. |
| NFR4 | Dependencies limited and installable via a Python virtual environment. |
| NFR5 | Failures of the AI backend must not crash the shell silently; report errors. |

## 2.2 Requirements Analysis

Stakeholders are students, junior system administrators, and security/CTF learners who already use a terminal. Priority was given to a reliable execute-and-recover loop over a full GUI. Safety analysis showed that “always execute” must be disabled when risky lines are detected. Context length must stay small (`MODEL_CONTEXT_LEN`) because longer histories increase hallucination and cost. Tool prompts are treated as data files so behaviour can change without rewriting the Python engine.

**Out of scope:** replacing bash; multi-user remote shell hosting; guaranteed correctness of LLM output; unsupervised destructive automation.

## 2.3 System Design

### Architecture

```
User (prompt-toolkit)
        │
        ▼
 llama_shell.py  ──►  /bin/bash (persistent) ──► stdout
        │
        │  exit ≠ 0
        ▼
 handle_error() ──► ai_response() ──► Ollama HTTP / Gemini
        │
        ▼
 ai_display.stream_response() ──► risk scan + render
        │
        ▼
 extract bash blocks → temp_script.sh → user y/n/a → PTY bash
```

### Module responsibilities (Table 2.3)

| Module | Responsibility |
|--------|----------------|
| `llama_shell.py` | REPL, bash I/O, error handler, tools, PTY execution |
| `configuration_variables.py` | API type, model IDs, paths, keywords, tool defaults |
| `ai_display.py` | Token streaming UI, markdown/code/diagram panels, risk badges |
| `markdowns/*.md` | System prompts / tools |
| Temporary files | `temp_script.sh`, error log temps under project base |

### Control commands (Table 2.4)

| Command | Purpose |
|---------|---------|
| `BUMP()` | Clear chat history to system prompt (reduce hallucinations) |
| `LOAD()` | Warm up the model with a trivial exchange |
| `TOOL()` / `TOOL() NAME` | List or switch active tool markdown |
| `ADD_TOOL() NAME …` | Draft and save a new tool via editor |
| `INCLUDE() file` | Attach file content for subsequent AI context |
| `BANNER()` / `HELP` / `RESET()` | UI help and bash session restart |

## 2.4 System Implementation / Simulation

Implementation language: **Python 3**. Key libraries: `prompt-toolkit` (prompt and completion), `rich` (display), `requests` (Ollama HTTP streaming), optional `google.generativeai` for Gemini.

**Command execution:** User lines are written to the bash stdin with sentinel lines that report exit code and `$PWD`. The Python side updates `current_dir` accordingly.

**AI path:** Messages follow a chat schema (`system` / `user` / `assistant`). Ollama uses streaming JSON lines; Gemini history is converted to alternating user/model parts. Default generation options favour lower temperature for more deterministic shell suggestions.

**Display:** `stream_response` consumes tokens, prints prose line-by-line, buffers GFM tables, renders closed fences as Syntax panels, and increments a risk counter when keyword regexes match.

**Tools:** Loading a tool replaces the system message from `markdowns/NAME.md`. An optional `embed_json` fence can inject string/time/file/tree/bash embeds subject to directory and command allowlists.

**Configuration:** `API_TYPE`, `OLLAMA_MODEL`, `OLLAMA_URL`, `HISTORY_DIR`, `MODEL_CONTEXT_LEN`, and `keywords` live in `configuration_variables.py`. Secrets (e.g. cloud API keys) must be kept out of version control and out of the printed report; use environment variables for submission media where possible.

## 2.5 System Testing

Testing was primarily **manual scenario testing** in a Linux environment with Ollama installed and a pulled model matching configuration.

### Sample test cases (Table 2.5)

| ID | Scenario | Expected result | Observed (fill in) |
|----|----------|-----------------|--------------------|
| T1 | Valid `ls` / `pwd` | Output only; no AI | |
| T2 | Intentional typo / missing command | AI suggestion; confirm prompt | |
| T3 | User answers `n` | Suggestion not run | |
| T4 | User answers `y` | Script runs; output shown | |
| T5 | Suggestion containing risk keyword | Amber/risk badge; confirmation forced | |
| T6 | `TOOL() LIST` / switch tool | Active tool changes | |
| T7 | `BUMP()` then new failure | Fresh context | |
| T8 | `LOAD()` | Model warms; “Model ready” | |
| T9 | AI backend down | Error message; shell remains usable | |

**Limitations of testing:** No full automated regression suite in the repository; results depend on model quality and network/local GPU resources.

---

# Chapter 3: Conclusion and Recommendation

## 3.1 Conclusion

The project achieved a **complete working system**: an AI-assisted interactive shell that integrates shell process control with LLM assistance under explicit user control.

**Major strengths**
- End-to-end failure→suggestion→confirm→execute workflow.
- Streaming, readable presentation of model output.
- Extensible tools via markdown prompts.
- Basic risk highlighting and confirmation discipline.

**Major weaknesses**
- Dependence on LLM quality; hallucinations remain possible.
- Safety is keyword-based, not a full security sandbox.
- Limited automated testing and formal metrics.
- Cloud API configuration, if used, increases privacy and key-management risk.

**Benefits derived:** Practical experience integrating OS-level process I/O with AI APIs; a usable teaching/demo artefact for safer AI-assisted CLI work; documentation suitable for FYP assessment.

## 3.2 Recommendations

1. Add automated tests for parsers (`extract_bash_blocks`), risk matching, and tool path validation.
2. Move all secrets to environment variables; never ship keys on the submission CD or in appendices.
3. Consider stronger isolation (containers, restricted shells) for executing AI-generated scripts.
4. Curate a small set of high-quality educational tools (Git, Docker, basics) with reviewed prompts.
5. Improve planning logistics: weekly supervisor log entries, freeze a demo script early, and keep a short backup recording of a successful recovery cycle.

---

# REFERENCES

*(Harvard style — verify against your institution’s exact Harvard guide. Examples to expand with real access dates and editions.)*

Ollama (n.d.) *Ollama documentation*. Available at: https://ollama.ai/ (Accessed: `[DATE]`).

Prompt Toolkit (n.d.) *Python Prompt Toolkit*. Available at: https://python-prompt-toolkit.readthedocs.io/ (Accessed: `[DATE]`).

Rich (n.d.) *Rich library documentation*. Available at: https://rich.readthedocs.io/ (Accessed: `[DATE]`).

`[Author]` (`[Year]`) `[Title of textbook on OS / SE / AI]`. `[Edition]`. `[Place]`: `[Publisher]`.

Personal communication: `[Supervisor Name]` (`[Year]`) Discussion during project supervision meetings. `[Institute]`.

---

# BACK PAGES

## APPENDICES

*(Appendix A: include drawings, design charts, photographs; for software, include source codes here.)*

### Appendix A — Installation and run instructions

```bash
git clone https://github.com/Kevinscki/llama_term.git
cd llama_term
python3 -m venv .env
source ./.env/bin/activate
pip3 install prompt-toolkit rich requests python-dotenv
# Install Ollama; pull a model matching OLLAMA_MODEL
python3 llama_shell.py
```

### Appendix B — Selected source listings

Include (or attach on CD) the full sources of at least:
- `llama_shell.py`
- `configuration_variables.py` (**redact secrets**)
- `ai_display.py`
- Representative `markdowns/BASH.md`

### Appendix C — Screenshots

Insert Figure 2.3, Figure 2.4, and additional demo screenshots.

### Appendix D — Sample tool prompt excerpt

Short excerpt from an active tool markdown (without sensitive host data).

---

## LOG FILE

*(rp.pdf requires the project log. Bring the completed signed log form to the presentation panel; bind a copy with the report.)*

Maintain entries for **every supervisor meeting**: date, topics discussed, decisions, next actions, student signature, supervisor signature. Obtain **supervisor approval to present** at least two weeks before Semester II study week.
