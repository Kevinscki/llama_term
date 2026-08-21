"""
ai_display.py — stdio-style streaming display for llama_term.

Renders the AI response inline in the terminal (no full-screen takeover):
  - Prose lines print as stable Rich Markdown, one line at a time
  - Contiguous Markdown table lines are buffered and flushed together so
    tables actually render as tables (Rich needs the whole table at once)
  - Code blocks render as Syntax-highlighted panels when the closing ``` arrives
  - ```mermaid (or other diagram) fences render as a distinct labeled panel
  - A "thinking…" indicator shows before the first token arrives
  - A single-line "typing" indicator updates in-place while a line is incomplete
  - Risk counter prints as a compact badge after each flagged line

Usage:
    from ai_display import stream_response

    full_response, flagged_lines, risk_counter = stream_response(
        token_generator,
        keywords=["rm", "sudo", "kill", ...],
    )
"""

from __future__ import annotations

import re
import sys
import time
from typing import Iterator

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
import rich.box as box

console = Console(highlight=False)

# Languages that we treat as "diagrams" rather than code — rendered in a
# distinctly labeled panel instead of a Syntax-highlighted code panel.
DIAGRAM_LANGS = {"mermaid", "sequence", "seq", "plantuml", "dot", "graphviz"}

_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$")


# ── helpers ─────────────────────────────────────────────────────────────────

def _risk_badge(count: int) -> Text:
    if count == 0:
        return Text(f" ✔  0 risky lines ", style="bold green")
    return Text(f" ⚠  {count} risky line{'s' if count != 1 else ''} ", style="bold red")


def _is_table_line(line: str) -> bool:
    """A line that looks like part of a Markdown table (row or separator)."""
    return bool(_TABLE_ROW_RE.match(line) or _TABLE_SEP_RE.match(line))


def _print_prose(line: str) -> None:
    """Print a single prose line as Markdown (handles bold, code, etc.)."""
    if line.strip():
        console.print(Markdown(line), end="")
    else:
        console.print()


def _print_table_block(lines: list[str]) -> None:
    """Print a buffered set of contiguous table lines as one Markdown block.

    Rich's Markdown renderer only recognizes a GFM table if it sees the
    header, separator, and body rows together — hence the buffering.
    """
    if not lines:
        return
    block = "\n".join(lines)
    console.print(Markdown(block))


def _print_code_block(lang: str, code_lines: list[str]) -> None:
    """Print a finished code block as a syntax-highlighted panel.

    Strips any stray fence-marker lines (``` or ```lang) so they never
    appear inside the rendered panel, regardless of nesting.
    """
    cleaned = [l for l in code_lines if not l.strip().startswith("```")]
    code = "\n".join(cleaned)
    syntax = Syntax(
        code,
        lang or "text",
        theme="monokai",
        word_wrap=True,
        background_color="default",
        padding=(0, 1),
    )
    console.print(
        Panel(syntax, box=box.ROUNDED, border_style="bright_black", padding=(0, 0)),
    )


def _print_diagram_block(lang: str, code_lines: list[str]) -> None:
    """Print a finished diagram fence (e.g. ```mermaid) as a labeled panel.

    Terminals can't render actual diagram graphics, so this shows the
    diagram source clearly marked as a diagram (not plain code), with a
    title so it's visually distinct from a Syntax code panel.
    """
    cleaned = [l for l in code_lines if not l.strip().startswith("```")]
    code = "\n".join(cleaned)
    syntax = Syntax(
        code,
        "text",
        theme="monokai",
        word_wrap=True,
        background_color="default",
        padding=(0, 1),
    )
    console.print(
        Panel(
            syntax,
            title=f"[bold cyan]◇ diagram · {lang}[/bold cyan]",
            title_align="left",
            box=box.ROUNDED,
            border_style="cyan",
            padding=(0, 0),
        ),
    )


def _overwrite_line(text: str) -> None:
    """
    Overwrite the current terminal line in-place (the 'typing' indicator).
    Uses a plain ANSI carriage-return trick — no curses, no Live.
    """
    width = console.width or 80
    truncated = text[: width - 4] + "…" if len(text) > width - 3 else text
    sys.stdout.write(f"\r\033[2m{truncated}\033[0m\033[K")
    sys.stdout.flush()


def _clear_line() -> None:
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()


def _show_thinking_placeholder(token_generator: Iterator[str]):
    """
    Show a lightweight 'thinking…' indicator until the first token arrives.

    Pulls the first token out of the generator (blocking on it, same as the
    caller would eventually do anyway) while animating a small spinner in
    place, then hands back a generator that replays that first token
    followed by the rest of the stream — so stream_response's main loop
    doesn't need to know this happened.
    """
    spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    it = iter(token_generator)

    result_holder: dict = {}

    def _pull_first():
        try:
            result_holder["token"] = next(it)
            result_holder["done"] = False
        except StopIteration:
            result_holder["done"] = True

    import threading
    t = threading.Thread(target=_pull_first, daemon=True)
    t.start()

    i = 0
    start = time.monotonic()
    while t.is_alive():
        frame = spinner_frames[i % len(spinner_frames)]
        elapsed = time.monotonic() - start
        _overwrite_line(f"\033[2m{frame} thinking… ({elapsed:0.1f}s)\033[0m")
        time.sleep(0.08)
        i += 1
    t.join()
    _clear_line()

    def _replay():
        if not result_holder.get("done"):
            yield result_holder["token"]
        for tok in it:
            yield tok

    return _replay()


# ── public API ───────────────────────────────────────────────────────────────

def stream_response(
    token_generator: Iterator[str],
    keywords: list[str] | None = None,
    show_thinking: bool = True,
) -> tuple[str, list[str], int]:
    """
    Consume *token_generator* and print the response inline as stdio.

    Returns (full_response, flagged_lines, risk_counter).
    Raises KeyboardInterrupt if interrupted.
    """
    if keywords is None:
        keywords = []

    compiled = [re.compile(rf"\b{re.escape(k)}\b") for k in keywords]

    full_response = ""
    flagged_lines: list[str] = []
    risk_counter = 0

    # Parser state
    buffer = ""
    fence_stack: list[str] = []   # stack of fence languages (depth = nesting)
    code_lang = "text"             # language of the OUTERMOST open fence
    code_buf: list[str] = []
    table_buf: list[str] = []      # buffered contiguous table lines (prose mode only)

    def _flush_table_buf():
        nonlocal table_buf
        if table_buf:
            _print_table_block(table_buf)
            table_buf = []

    if show_thinking:
        token_generator = _show_thinking_placeholder(token_generator)

    try:
        for token in token_generator:
            full_response += token
            buffer += token

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                _clear_line()

                stripped = line.strip()
                is_fence = stripped.startswith("```")

                if is_fence:
                    lang_word = stripped[3:].strip()

                    if not fence_stack:
                        # Any pending table lines end here — flush before code
                        _flush_table_buf()
                        # Opens the OUTER code block
                        fence_stack.append(lang_word or "text")
                        code_lang = fence_stack[0]
                        code_buf = []
                    elif lang_word:
                        # ``` followed by a word while already inside a
                        # code block -> nested opener, keep as literal
                        # content (it will be stripped on render anyway)
                        fence_stack.append(lang_word)
                        code_buf.append(line)
                    else:
                        # bare ``` -> closes innermost fence
                        fence_stack.pop()
                        if fence_stack:
                            code_buf.append(line)
                        else:
                            if code_lang.lower() in DIAGRAM_LANGS:
                                _print_diagram_block(code_lang, code_buf)
                            else:
                                _print_code_block(code_lang, code_buf)
                            code_buf = []
                else:
                    if not fence_stack:
                        if _is_table_line(line):
                            table_buf.append(line)
                        else:
                            _flush_table_buf()
                            _print_prose(line)
                            if any(p.search(line) for p in compiled):
                                flagged_lines.append(line)
                                risk_counter += 1
                                console.print(_risk_badge(risk_counter))
                    else:
                        code_buf.append(line)
                        if any(p.search(line) for p in compiled):
                            flagged_lines.append(line)
                            risk_counter += 1

            if buffer:
                if fence_stack:
                    indicator = f"  [{code_lang}] {buffer}"
                else:
                    indicator = "  " + buffer
                _overwrite_line(indicator)

    except KeyboardInterrupt:
        _clear_line()
        _flush_table_buf()
        console.print("\n[yellow]Interrupted.[/yellow]")
        raise

    # ── flush anything left after the stream ends ───────────────────────
    _clear_line()

    if fence_stack and code_buf:
        # Stream ended mid-code-block — render what we have
        if code_lang.lower() in DIAGRAM_LANGS:
            _print_diagram_block(code_lang, code_buf)
        else:
            _print_code_block(code_lang, code_buf)
    elif buffer.strip():
        if _is_table_line(buffer):
            table_buf.append(buffer)
        else:
            _flush_table_buf()
            _print_prose(buffer)

    _flush_table_buf()

    return full_response, flagged_lines, risk_counter
