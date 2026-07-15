#!/usr/bin/env python3
"""Entry point for the Cipher Breaker CLI.

Run with no arguments for the interactive menu, or pass a subcommand:

    python main.py --help
    python main.py caesar-break -t "Dwwdfn dw gdzq"

Keeping this file to a few lines is deliberate: the entry point should decide
nothing. All behaviour lives in :mod:`cli.args`, which is importable and
testable without launching a process.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `python main.py` from anywhere without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cli.args import run  # noqa: E402


def main() -> int:
    """Run the CLI and return an exit code."""
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
