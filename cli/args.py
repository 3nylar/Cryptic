"""Non-interactive command-line interface (argparse).

Design rules followed here:

* **Plaintext to stdout, everything else to stderr.** ``cryptic
  caesar-encrypt -t hi -k 3 > out.txt`` must yield a file containing only the
  ciphertext, so banners, tables and logs go elsewhere.
* **Exit codes mean something.** 0 success, 1 user error, 2 argparse usage
  error, 130 interrupted. Scripts and CI can rely on that.
* **Input from ``--text`` or ``--file`` or a pipe.** All three are equally
  first-class; long texts should never have to fit on a command line.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from analysis import caesar_breaker, vigenere_breaker
from analysis.frequency import index_of_coincidence, chi_squared
from cipher import caesar, vigenere
from utils.config import Settings, setup_logging
from utils.export import ExportError, export_result
from utils.formatting import Formatter

EXIT_OK, EXIT_USER_ERROR, EXIT_INTERRUPT = 0, 1, 130
VERSION = "1.0.0"


def build_parser() -> argparse.ArgumentParser:
    """Construct the full argument parser."""
    parser = argparse.ArgumentParser(
        prog="cryptic",
        description=(
            "Encrypt, decrypt and break Caesar and Vigenere ciphers. "
            "Run with no arguments for the interactive menu."
        ),
        epilog=(
            "Examples:\n"
            "  cryptic caesar-encrypt -t 'Attack at dawn' -k 3\n"
            "  cryptic caesar-break -f secret.txt --export report.md\n"
            "  cat secret.txt | cryptic vigenere-break --max-key-length 12\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

    common = argparse.ArgumentParser(add_help=False)
    source = common.add_mutually_exclusive_group()
    source.add_argument("-t", "--text", help="text to process")
    source.add_argument("-f", "--file", help="read text from this file ('-' for stdin)")
    common.add_argument("--no-color", action="store_true", help="disable colour output")
    common.add_argument("--export", metavar="PATH", help="write results to .json/.md/.txt")
    common.add_argument("--config", metavar="PATH", help="load settings from a JSON file")
    common.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="verbosity of diagnostic logging (stderr)",
    )
    common.add_argument(
        "--no-explain",
        action="store_true",
        help="suppress the step-by-step attack explanation",
    )

    subs = parser.add_subparsers(dest="command")

    def add(name: str, help_text: str) -> argparse.ArgumentParser:
        return subs.add_parser(name, parents=[common], help=help_text, description=help_text)

    ce = add("caesar-encrypt", "Encrypt text with the Caesar cipher")
    ce.add_argument("-k", "--key", required=True, help="shift, any integer (wraps mod 26)")

    cd = add("caesar-decrypt", "Decrypt Caesar ciphertext with a known shift")
    cd.add_argument("-k", "--key", required=True, help="shift used to encrypt")

    cb = add("caesar-break", "Break Caesar ciphertext with frequency analysis")
    cb.add_argument("--top", type=int, help="how many candidates to show (default 5)")

    ve = add("vigenere-encrypt", "Encrypt text with the Vigenere cipher")
    ve.add_argument("-k", "--key", required=True, help="keyword, letters only")

    vd = add("vigenere-decrypt", "Decrypt Vigenere ciphertext with a known keyword")
    vd.add_argument("-k", "--key", required=True, help="keyword used to encrypt")

    vb = add("vigenere-break", "Break Vigenere ciphertext with classical cryptanalysis")
    vb.add_argument("--max-key-length", type=int, help="largest key length to try (default 20)")
    vb.add_argument("--key-length", type=int, help="skip estimation; use this length")

    add("stats", "Show frequency statistics for a text")
    add("compare", "Compare Caesar, Vigenere and AES side by side")
    add("interactive", "Launch the interactive menu")
    return parser


def read_input(args) -> str:
    """Resolve the text to operate on from --text, --file or stdin.

    Raises:
        ValueError: if no input was supplied or the file cannot be read.
    """
    if args.text is not None:
        return args.text
    if args.file:
        if args.file == "-":
            return sys.stdin.read()
        path = Path(args.file).expanduser()
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"could not read {path}: {exc}") from exc
    if not sys.stdin.isatty():
        piped = sys.stdin.read()
        if piped.strip():
            return piped
    raise ValueError("no input: use --text, --file, or pipe text on stdin")


def _settings_from(args) -> Settings:
    settings = Settings.load(Path(args.config) if getattr(args, "config", None) else None)
    if getattr(args, "no_color", False):
        settings.no_color = True
    if getattr(args, "log_level", None):
        settings.log_level = args.log_level
    if getattr(args, "no_explain", False):
        settings.explain = False
    if getattr(args, "top", None):
        settings.top_candidates = args.top
    if getattr(args, "max_key_length", None):
        settings.max_key_length = args.max_key_length
    setup_logging(settings.log_level, settings.log_file)
    return settings


def _maybe_export(result, args, fmt: Formatter) -> None:
    if not getattr(args, "export", None):
        return
    try:
        written = export_result(result, args.export)
        fmt.success(f"Report written to {written}")
    except ExportError as exc:
        fmt.error(str(exc))


def run(argv: list[str] | None = None) -> int:
    """Execute one CLI invocation and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command or args.command == "interactive":
        from cli.interactive import run_interactive

        settings = Settings.load()
        setup_logging(settings.log_level, settings.log_file)
        return run_interactive(settings)

    settings = _settings_from(args)
    fmt = Formatter(plain=settings.no_color)

    try:
        if args.command == "compare":
            _print_comparison(fmt)
            return EXIT_OK

        text = read_input(args)

        if args.command == "caesar-encrypt":
            print(caesar.encrypt(text, args.key))
        elif args.command == "caesar-decrypt":
            print(caesar.decrypt(text, args.key))
        elif args.command == "vigenere-encrypt":
            print(vigenere.encrypt(text, args.key))
        elif args.command == "vigenere-decrypt":
            print(vigenere.decrypt(text, args.key))
        elif args.command == "caesar-break":
            with fmt.progress("Trying all 26 keys"):
                result = caesar_breaker.break_caesar(text)
            print(result.plaintext)
            fmt.success(
                f"Key = {result.key}   confidence {fmt.confidence_bar(result.confidence)}"
            )
            fmt.caesar_candidates(result, limit=settings.top_candidates)
            if settings.explain:
                fmt.steps(result.steps)
            _maybe_export(result, args, fmt)
        elif args.command == "vigenere-break":
            with fmt.progress("Estimating key length and solving columns"):
                result = vigenere_breaker.break_vigenere(
                    text,
                    max_key_length=settings.max_key_length,
                    known_key_length=getattr(args, "key_length", None),
                )
            print(result.plaintext)
            fmt.success(
                f"Key = {result.key!r}   confidence {fmt.confidence_bar(result.confidence)}"
            )
            for warning in result.warnings:
                fmt.warn(warning)
            fmt.key_length_table(result.key_length_guesses)
            if settings.explain:
                fmt.steps(result.steps)
            _maybe_export(result, args, fmt)
        elif args.command == "stats":
            fmt.frequency_histogram(text)
            fmt.print("")
            fmt.print(f"  Index of coincidence : {index_of_coincidence(text):.4f}")
            fmt.print(f"  Chi-squared vs English: {chi_squared(text):.1f}")
            fmt.muted(
                "  IC near 0.067 suggests one alphabet (plain or Caesar); "
                "near 0.038 suggests many (Vigenere)."
            )
        return EXIT_OK

    except (ValueError, caesar.CaesarKeyError, vigenere.VigenereKeyError) as exc:
        fmt.error(str(exc))
        return EXIT_USER_ERROR
    except KeyboardInterrupt:  # pragma: no cover
        fmt.warn("Interrupted.")
        return EXIT_INTERRUPT


def _print_comparison(fmt: Formatter) -> None:
    """Print the algorithm comparison table used by menu option 7."""
    fmt.title("Algorithm comparison")
    rows = [
        ("Caesar", "26", "instant", "Ciphertext-only frequency analysis", "None"),
        ("Vigenere", "26^m", "milliseconds", "Kasiski + IC + per-column chi-sq", "None"),
        ("AES-256", "2^256", "infeasible", "No practical attack known", "Standard"),
    ]
    headers = ("Cipher", "Keyspace", "Time to break", "Best known attack", "Modern use")
    from utils.formatting import _ascii_table

    _ascii_table(headers, rows)
    fmt.muted(
        "  Keyspace size is not security: Vigenere's 26^m keys fall in milliseconds\n"
        "  because the key repeats, which lets the attacker divide and conquer."
    )
