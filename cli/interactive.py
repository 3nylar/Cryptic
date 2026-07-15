"""The interactive menu — the front door for people who have never used a CLI.

Usability decisions worth knowing about:

* Every prompt says what a valid answer looks like, and a bad answer re-asks
  instead of exiting. Losing your pasted paragraph to a typo'd key is the
  fastest way to make someone give up on a tool.
* Enter alone accepts the shown default wherever there is a sensible one.
* ``q`` or Ctrl-C leaves from anywhere, and Ctrl-D (EOF) is treated as quit
  rather than an unhandled exception.
* After every attack the tool offers to export, because "I got the answer and
  then lost the terminal" is a real student experience.
"""

from __future__ import annotations

from analysis import caesar_breaker, vigenere_breaker
from analysis.frequency import chi_squared, index_of_coincidence
from cipher import caesar, vigenere
from utils.config import Settings
from utils.export import ExportError, export_result
from utils.formatting import Formatter

HELP_TEXT = """\
What this tool is
  A teaching toolkit for two historical ciphers, plus the attacks that break
  them. Nothing here is safe for real secrets - that is the point of the demo.

The words you will meet
  plaintext   your readable message
  ciphertext  the scrambled version
  key         the secret that turns one into the other
  Caesar      shift every letter by a fixed number (key = a number, 0-25)
  Vigenere    shift every letter by a different amount, taken from a repeating
              keyword (key = a word, e.g. LEMON)

Menu options
  1/2  Caesar encrypt / decrypt   - you supply the shift
  3    Break Caesar               - no key needed; the tool finds it
  4/5  Vigenere encrypt / decrypt - you supply the keyword
  6    Break Vigenere             - no key needed; needs ~100+ letters to work well
  7    Compare Caesar, Vigenere and AES
  8    This help
  9    Exit  (or type 'q' at any prompt)

Tips
  * Breaking works on statistics, so longer ciphertext = better results.
  * Confidence below ~50% means "this is a guess" - feed it more text.
  * Command-line mode exists too: python main.py --help
"""


def _ask(prompt: str, default: str | None = None) -> str:
    """Prompt for a line of input, handling quit and EOF uniformly.

    Raises:
        KeyboardInterrupt: when the user asks to quit, so a single handler at
            the top of the loop can unwind cleanly from any depth.
    """
    suffix = f" [{default}]" if default else ""
    try:
        answer = input(f"{prompt}{suffix}: ").strip()
    except EOFError:
        raise KeyboardInterrupt from None
    if answer.lower() in {"q", "quit", "exit"}:
        raise KeyboardInterrupt
    return answer or (default or "")


def _ask_text(fmt: Formatter) -> str:
    """Ask for a message, allowing a file path instead of typing/pasting."""
    fmt.muted("  Enter your text, or type 'file:PATH' to read it from a file.")
    while True:
        raw = _ask("  Text")
        if not raw:
            fmt.warn("Please enter some text (or 'q' to go back).")
            continue
        if raw.lower().startswith("file:"):
            path = raw[5:].strip()
            try:
                with open(path, encoding="utf-8") as handle:
                    content = handle.read()
                fmt.success(f"Read {len(content)} characters from {path}")
                return content
            except OSError as exc:
                fmt.error(f"Could not read {path}: {exc}")
                continue
        return raw


def _ask_caesar_key(fmt: Formatter) -> int:
    """Ask for a Caesar shift until a valid one is given."""
    while True:
        try:
            return caesar.validate_shift(_ask("  Shift (a whole number, e.g. 3)"))
        except caesar.CaesarKeyError as exc:
            fmt.error(f"{exc}. Try again, e.g. 3 or -5 or 29.")


def _ask_vigenere_key(fmt: Formatter) -> str:
    """Ask for a Vigenere keyword until a valid one is given."""
    while True:
        try:
            return vigenere.validate_key(_ask("  Keyword (letters only, e.g. LEMON)"))
        except vigenere.VigenereKeyError as exc:
            fmt.error(f"{exc}. Try again, e.g. LEMON.")


def _offer_export(result, fmt: Formatter) -> None:
    answer = _ask("  Export this report? path or Enter to skip", "")
    if not answer:
        return
    try:
        fmt.success(f"Report written to {export_result(result, answer)}")
    except ExportError as exc:
        fmt.error(str(exc))


def run_interactive(settings: Settings | None = None) -> int:
    """Run the menu loop. Returns a process exit code."""
    settings = settings or Settings()
    fmt = Formatter(plain=settings.no_color)
    fmt.banner()
    fmt.muted("Type 'q' at any prompt to go back. Option 8 explains everything.")

    try:
        while True:
            fmt.menu()
            choice = _ask("Choose an option", "8")

            if choice == "1":
                fmt.title("Encrypt with Caesar")
                text, key = _ask_text(fmt), _ask_caesar_key(fmt)
                fmt.success(f"Ciphertext: {caesar.encrypt(text, key)}")
            elif choice == "2":
                fmt.title("Decrypt with Caesar")
                text, key = _ask_text(fmt), _ask_caesar_key(fmt)
                fmt.success(f"Plaintext: {caesar.decrypt(text, key)}")
            elif choice == "3":
                fmt.title("Break Caesar (no key needed)")
                text = _ask_text(fmt)
                with fmt.progress("  Trying all 26 keys"):
                    result = caesar_breaker.break_caesar(text)
                fmt.success(
                    f"Key = {result.key}   confidence "
                    f"{fmt.confidence_bar(result.confidence)}"
                )
                fmt.print(f"  Plaintext: {result.plaintext}")
                fmt.caesar_candidates(result, limit=settings.top_candidates)
                if settings.explain:
                    fmt.steps(result.steps)
                _offer_export(result, fmt)
            elif choice == "4":
                fmt.title("Encrypt with Vigenere")
                text, key = _ask_text(fmt), _ask_vigenere_key(fmt)
                fmt.success(f"Ciphertext: {vigenere.encrypt(text, key)}")
            elif choice == "5":
                fmt.title("Decrypt with Vigenere")
                text, key = _ask_text(fmt), _ask_vigenere_key(fmt)
                fmt.success(f"Plaintext: {vigenere.decrypt(text, key)}")
            elif choice == "6":
                fmt.title("Break Vigenere (no key needed)")
                text = _ask_text(fmt)
                with fmt.progress("  Estimating key length"):
                    result = vigenere_breaker.break_vigenere(
                        text, max_key_length=settings.max_key_length
                    )
                fmt.success(
                    f"Key = {result.key!r}   confidence "
                    f"{fmt.confidence_bar(result.confidence)}"
                )
                for warning in result.warnings:
                    fmt.warn(warning)
                fmt.print(f"  Plaintext: {result.plaintext}")
                fmt.key_length_table(result.key_length_guesses)
                if settings.explain:
                    fmt.steps(result.steps)
                _offer_export(result, fmt)
            elif choice == "7":
                from cli.args import _print_comparison

                _print_comparison(fmt)
            elif choice == "8":
                fmt.title("Help")
                fmt.print(HELP_TEXT)
            elif choice == "9":
                break
            elif choice.lower() == "s":  # hidden extra: statistics view
                text = _ask_text(fmt)
                fmt.frequency_histogram(text)
                fmt.print(f"  Index of coincidence : {index_of_coincidence(text):.4f}")
                fmt.print(f"  Chi-squared vs English: {chi_squared(text):.1f}")
            else:
                fmt.warn(f"'{choice}' is not on the menu. Choose 1-9.")
    except KeyboardInterrupt:
        fmt.print("")

    fmt.muted("Goodbye. Remember: never protect anything real with these ciphers.")
    return 0
