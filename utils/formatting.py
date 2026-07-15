"""All terminal output lives here, so the rest of the code never prints.

Two reasons for that discipline:

1. The cipher and analysis modules stay importable from a notebook, a web app
   or a test suite without dragging a terminal along.
2. Colour is a *presentation* choice, and presentation choices have to degrade.
   If :mod:`rich` is installed we use it; if not, we fall back to plain ASCII
   with no loss of information. The tool never crashes because a library is
   missing, and never emits escape codes into a pipe or a file.

Accessibility notes
-------------------
* Colour is never the only signal: every status also carries a word or symbol
  (``[OK]``, ``[!]``), so the output survives greyscale, colour-blindness and
  screen readers.
* ``--no-color`` and the ``NO_COLOR`` environment variable both disable styling.
* Output is auto-plain when stdout is not a TTY, so ``> results.txt`` produces a
  clean file.
* Tables are ASCII-first and stay under 80 columns where possible.
"""

from __future__ import annotations

import os
import sys
import time
from contextlib import contextmanager

try:  # pragma: no cover - exercised implicitly by both branches
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:  # pragma: no cover
    RICH_AVAILABLE = False

from analysis.frequency import histogram_rows

BANNER = r"""
====================================
        Cryptic
   Caesar & Vigenere Toolkit
====================================
""".strip("\n")

MENU = """\
====================================
 Cryptic
====================================
1. Encrypt Caesar
2. Decrypt Caesar
3. Break Caesar
4. Encrypt Vigenere
5. Decrypt Vigenere
6. Break Vigenere
7. Compare Algorithms
8. Help
9. Exit
===================================="""

_ANSI = {
    "title": "\033[1;36m",
    "ok": "\033[1;32m",
    "warn": "\033[1;33m",
    "error": "\033[1;31m",
    "muted": "\033[2m",
    "reset": "\033[0m",
}


def colour_enabled(force_plain: bool = False) -> bool:
    """Decide whether to emit styling at all.

    Honours ``--no-color`` (via ``force_plain``), the ``NO_COLOR`` convention,
    and whether stdout is an interactive terminal.
    """
    if force_plain or os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


class Formatter:
    """Renders results. One instance per CLI run.

    Args:
        plain: Force ASCII, no colour. Set by ``--no-color`` or piped output.
    """

    def __init__(self, plain: bool = False) -> None:
        self.use_colour = colour_enabled(plain)
        self.console = (
            Console(no_color=not self.use_colour)
            if RICH_AVAILABLE and not plain
            else None
        )

    # ---------------------------------------------------------------- basics

    def _style(self, text: str, kind: str) -> str:
        if not self.use_colour:
            return text
        return f"{_ANSI.get(kind, '')}{text}{_ANSI['reset']}"

    def print(self, text: str = "") -> None:
        """Print a line of plain text."""
        print(text)

    def title(self, text: str) -> None:
        """Print a section heading."""
        if self.console:
            self.console.print(f"\n[bold cyan]{text}[/bold cyan]")
        else:
            print("\n" + self._style(text, "title"))

    def success(self, text: str) -> None:
        """Print a success line. Always prefixed ``[OK]``, colour or not."""
        if self.console:
            self.console.print(f"[bold green][OK][/bold green] {text}")
        else:
            print(self._style("[OK]", "ok") + " " + text)

    def warn(self, text: str) -> None:
        """Print a warning line. Always prefixed ``[!]``."""
        if self.console:
            self.console.print(f"[bold yellow][!][/bold yellow] {text}")
        else:
            print(self._style("[!]", "warn") + " " + text)

    def error(self, text: str) -> None:
        """Print an error line to stderr. Always prefixed ``[X]``."""
        message = "[X] " + text
        if self.console:
            self.console.print(f"[bold red][X][/bold red] {text}", style=None)
        else:
            print(self._style(message, "error"))

    def muted(self, text: str) -> None:
        """Print secondary information."""
        if self.console:
            self.console.print(f"[dim]{text}[/dim]")
        else:
            print(self._style(text, "muted"))

    def banner(self) -> None:
        """Print the application banner."""
        if self.console:
            self.console.print(Panel.fit(BANNER, border_style="cyan"))
        else:
            print(BANNER)

    def menu(self) -> None:
        """Print the interactive menu."""
        print("\n" + MENU)

    # -------------------------------------------------------------- progress

    @contextmanager
    def progress(self, label: str):
        """Show a progress indicator around a block of work.

        Uses a rich spinner when available; otherwise prints a one-line
        "working..." notice. Both are suppressed for non-interactive output so
        piped results stay clean.

        Example:
            >>> fmt = Formatter(plain=True)
            >>> with fmt.progress("Working"):  # doctest: +SKIP
            ...     do_the_thing()
        """
        quiet = not sys.stdout.isatty()
        if quiet:
            yield
            return
        if self.console:
            with self.console.status(f"[cyan]{label}...[/cyan]"):
                yield
        else:
            print(f"{label}... ", end="", flush=True)
            started = time.perf_counter()
            try:
                yield
            finally:
                print(f"done ({(time.perf_counter() - started) * 1000:.1f} ms)")

    # ---------------------------------------------------------------- tables

    def steps(self, steps: list[str]) -> None:
        """Print the numbered explanation of an attack."""
        self.title("How the attack worked")
        for i, step in enumerate(steps, 1):
            wrapped = _wrap(step, width=74, indent=" " * 4)
            print(f"  {i}. {wrapped.lstrip()}")

    def confidence_bar(self, value: float, width: int = 20) -> str:
        """Render confidence as ``[####------] 42%`` — readable without colour."""
        filled = round(width * max(0.0, min(value, 1.0)))
        return f"[{'#' * filled}{'-' * (width - filled)}] {value:.0%}"

    def caesar_candidates(self, result, limit: int = 5) -> None:
        """Print the ranked Caesar candidates table."""
        self.title(f"Top {limit} candidate plaintexts")
        rows = [
            (
                str(c.shift),
                f"{c.chi_squared:.1f}",
                f"{c.score:.1f}",
                c.preview(52),
            )
            for c in result.candidates[:limit]
        ]
        headers = ("Shift", "Chi-sq", "Score", "Plaintext preview")
        if self.console:
            table = Table(show_header=True, header_style="bold cyan")
            for h in headers:
                table.add_column(h)
            for i, row in enumerate(rows):
                style = "bold green" if i == 0 else None
                table.add_row(*row, style=style)
            self.console.print(table)
        else:
            _ascii_table(headers, rows)

    def key_length_table(self, guesses, limit: int = 6) -> None:
        """Print the Vigenere key-length evidence table."""
        self.title("Key length evidence")
        rows = [
            (
                str(g.length),
                f"{g.average_ioc:.4f}",
                str(g.kasiski_votes),
                f"{g.combined_score:.3f}",
            )
            for g in guesses[:limit]
        ]
        headers = ("Length", "Avg IC", "Kasiski votes", "Score")
        if self.console:
            table = Table(show_header=True, header_style="bold cyan")
            for h in headers:
                table.add_column(h)
            for i, row in enumerate(rows):
                table.add_row(*row, style="bold green" if i == 0 else None)
            self.console.print(table)
        else:
            _ascii_table(headers, rows)

    def frequency_histogram(self, text: str) -> None:
        """Print the observed-vs-English letter frequency histogram."""
        self.title("Letter frequency distribution")
        print("  letter   observed   English    chart")
        for letter, observed, expected, bar in histogram_rows(text, width=32):
            print(f"    {letter}      {observed:5.2f}%     {expected:5.2f}%   {bar}")
        self.muted("  'observed' is this text; 'English' is ordinary prose.")


def _wrap(text: str, width: int = 74, indent: str = "") -> str:
    """Word-wrap ``text``, indenting continuation lines."""
    words, lines, current = text.split(), [], ""
    for word in words:
        if len(current) + len(word) + 1 > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    lines.append(current)
    return ("\n" + indent).join(lines)


def _ascii_table(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> None:
    """Minimal ASCII table used when rich is unavailable."""
    widths = [
        max(len(headers[i]), max((len(r[i]) for r in rows), default=0))
        for i in range(len(headers))
    ]
    line = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    print(line)
    print("| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |")
    print(line)
    for row in rows:
        print("| " + " | ".join(c.ljust(widths[i]) for i, c in enumerate(row)) + " |")
    print(line)
