# OTHER — FYP Helpers Drawn from the PDFs (+ Project Reality)

Material here is **not** a substitute for the formal report or the five presentation slides. It consolidates rules from `rp.pdf`, `Presentation Guidelines.pdf`, and `APPENDIX A`, plus practical notes grounded in this repository.

---

## 1. Hard submission and eligibility rules (`rp.pdf`)

| Rule | What you must do |
|------|------------------|
| Presentation first | Only after a **successful presentation** may you submit the final report. |
| Bound report | Printed and bound copy of the final project report. |
| System media | A **CD** containing the developed system. |
| Supervisor | Meet regularly; complete the **log form every meeting**. |
| Approval to present | Supervisor approval **≥ 2 weeks** before Semester II study week. |
| Timetable | Present only on your assigned date/time; only with approval. |
| Expectations | Complete system; integrate programme knowledge; community value; keep documentation and progress updates. |

Faculty may still publish exact presentation dates, submission deadlines, and marking rubrics — track those announcements separately.

---

## 2. Presentation day checklist (`Presentation Guidelines.pdf`)

**Must bring**
- [ ] Completed **log form**, signed by you and your supervisor
- [ ] Laptop with working `llama_term` + Ollama (or documented Gemini fallback)
- [ ] PowerPoint **≤ 5 slides** covering cover → intro → methodology → significance (+ optional demo roadmap)
- [ ] Backup: short offline video of failure→AI→confirm if network/model fails (ask if allowed)

**Timing**
- Total **15 minutes**
- ≈ **4 minutes** slides
- ≈ **11 minutes** live project
- Leave time for panel questions within the slot if the chair allows

**What the 5 slides are allowed to carry**
1. Cover (title, full name, registration number, supervisor)
2. Introduction / description
3. Methodology
4. Significance
5. (Optional within limit) Demo roadmap — do not invent extra theory slides

**Then:** demonstrate the project (not more slides).

Full slide text: see `PRESENTATION.md`.

---

## 3. Report assembly checklist (`APPENDIX A` + `rp.pdf`)

### Preliminary pages (all required)
- [ ] Cover page fields in **exact order** (institute → department → title → name → reg no → programme → year → duration)
- [ ] Acknowledgement
- [ ] Summary/Abstract (practical work learned, major challenges, conclusions, recommendations)
- [ ] Table of contents with page numbers
- [ ] List of Figures (captions **below** figures; chapter-based numbering preferred)
- [ ] List of Tables (headers + numbers; chapter-based numbering preferred)
- [ ] List of acronyms/abbreviations

### Main body
- [ ] **Chapter 1:** Background · Project Description · Project Objectives
- [ ] **Chapter 2 (Informatics):** Requirements Specification · Requirements Analysis · System Design · System Implementation/Simulation · System Testing — plus clear methodology
- [ ] **Chapter 3:** Conclusion (strengths, weaknesses, benefits) · Recommendations (planning & operational logistics)
- [ ] **References:** Harvard style only
- [ ] **Appendices:** charts, photos, **source code** for software projects
- [ ] **Log File** copy as required by department

Draft body: see `REPORT.md`.

---

## 4. What to put on the CD (practical)

Suggested layout (confirm with supervisor if the department specifies otherwise):

```
CD/
  README.txt          # how to install and run
  REQUIREMENTS.txt    # pip packages
  src/                # project tree without secrets / venv / huge models
  docs/               # optional PDF of report (if allowed)
  screenshots/        # demo evidence
```

**Do not put on the CD**
- API keys (including any Gemini/cloud keys that may exist in local config)
- `.env` files with secrets
- Virtualenv (`env/`, `.env/` bytecode trees)
- Personal paths that expose unrelated host files
- Large model weights (document `ollama pull …` instead)

Before burning: set `configuration_variables.py` to Ollama-only defaults and remove secrets, or load keys from environment.

---

## 5. Honest one-paragraph project statement (use in viva)

> llama_term is a Python AI-assisted interactive shell. It runs a real bash subprocess for normal commands. When a command fails, it asks an LLM for a fix, streams the answer in the terminal, highlights risky keywords, and only runs extracted bash blocks if the user confirms. It is not a compiled shell rewrite; its value is human-in-the-loop error recovery and swappable domain tools.

Avoid overselling: do not claim zero hallucinations, full OS replacement, or unsupervised safe automation.

---

## 6. Live demo script (≈11 minutes)

| Min | Action | Show |
|-----|--------|------|
| 0–1 | `python3 llama_shell.py` | Banner, prompt, identity |
| 1–2 | `pwd` / `ls` | Normal success path |
| 2–5 | Deliberate bad command | Failure → thinking → stream → confirm UI |
| 5–6 | Answer `n`, then repeat with `y` | Control and execution |
| 6–8 | `TOOL() LIST` → `TOOL() <NAME>` | Extensibility |
| 8–9 | `BUMP()` (and `LOAD()` if time) | Context hygiene |
| 9–11 | Summarise safety + limits; questions | Candor |

**Safe failure ideas:** misspelled URL host, `cat` of missing file, unknown command name.  
**Avoid live:** `rm -rf`, blind `sudo`, network attacks, or anything that can damage the demo machine.

---

## 7. Map: PDF chapters ↔ repository artefacts

| Report / slide topic | Evidence in code / repo |
|----------------------|-------------------------|
| Persistent shell | `llama_shell.py` — bash `Popen`, sentinels, `lord_bash` |
| AI on failure | `handle_error`, `ai_response`, `extract_bash_blocks` |
| Streaming UI / risk | `ai_display.py` — `stream_response`, keyword badges |
| Configuration | `configuration_variables.py` — `API_TYPE`, model, `keywords`, paths |
| Tools | `TOOL()` / `ADD_TOOL()`, `markdowns/*.md`, embeds |
| User docs | `README.md`, `AI_README.md` |
| Screenshot for figures | `screenshotpic.png` (plus new captures) |

---

## 8. Figures and tables you still need to produce

From Appendix A you must **actually caption and list** figures/tables in the bound report. Minimum set:

1. Architecture diagram (Chapter 2)
2. Sequence diagram: fail → AI → confirm → PTY
3. Two screenshots (banner; AI suggestion + `Run it?`)
4. Requirements tables and test table (already drafted in `REPORT.md` — fill “Observed”)

Number as Figure 2.1, Table 2.1, etc.

---

## 9. Supervisor log — what “good” entries look like

Each meeting row should allow a stranger to reconstruct progress:

- Date and duration
- Work shown (feature, bug, chapter draft)
- Feedback received
- Agreed next steps and deadline
- Signatures (student + supervisor)

Keep the original for the panel; bind a copy with the report if required.

---

## 10. Common panel questions (prepare short answers)

1. **Why not just use ChatGPT in a browser?** — Local context, terminal I/O, confirm-before-run, optional local Ollama, tool prompts.
2. **Is this a shell?** — Emulated workflow wrapping bash; not a POSIX shell implementation.
3. **How do you stop dangerous commands?** — Keyword scan, forced confirm, user gate; not a full sandbox — state the limit.
4. **How did you test?** — Scenario table; depend on model; acknowledge need for automation.
5. **What modules from your programme did you integrate?** — OS processes/PTY, SE modular design, networking/APIs, AI applications.
6. **Community impact?** — Learning aid and safer AI-CLI pattern for students/admins.

---

## 11. Formatting reminders (Appendix A)

- Figures: caption **at the bottom**, with number.
- Tables: header with table number.
- Prefer numbering **by chapter**.
- References: **Harvard** only.
- Software: **all codes** in appendices (and/or CD) — redact secrets.

---

## 12. File guide for this `docs/` folder

| File | Role |
|------|------|
| `PRESENTATION.md` | Exact slide order and spoken cues (≤5 slides + demo) |
| `REPORT.md` | Strict report skeleton and filled draft for Chapters 1–3 |
| `OTHER.md` | Checklists, CD tips, demo timing, viva prep (this file) |

After placeholders are filled, export `PRESENTATION.md` → PowerPoint and `REPORT.md` → formatted Word/PDF for binding.
