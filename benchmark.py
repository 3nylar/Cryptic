#!/usr/bin/env python3
"""Benchmark the ciphers and the attacks.

Run: ``python benchmark.py [--sizes 1000 10000 100000]``

The numbers this prints are the argument of the whole project. "These ciphers
are insecure" is an assertion; "your 8-letter Vigenere key fell in 40
milliseconds on a laptop" is a measurement.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analysis import caesar_breaker, vigenere_breaker  # noqa: E402
from cipher import caesar, vigenere  # noqa: E402

SAMPLE = (
    "it is a truth universally acknowledged that a single man in possession of "
    "a good fortune must be in want of a wife however little known the feelings "
    "or views of such a man may be on his first entering a neighbourhood this "
    "truth is so well fixed in the minds of the surrounding families that he is "
    "considered the rightful property of some one or other of their daughters "
)


def make_text(letters: int) -> str:
    """Return English text of roughly ``letters`` characters."""
    repeats = max(1, letters // len(SAMPLE) + 1)
    return (SAMPLE * repeats)[:letters]


def time_it(function, *args, repeats: int = 3) -> float:
    """Return the best of ``repeats` runs, in milliseconds.

    Best-of rather than mean: we want the machine's capability, not the noise
    from whatever else the OS decided to do during the run.
    """
    best = float("inf")
    for _ in range(repeats):
        started = time.perf_counter()
        function(*args)
        best = min(best, time.perf_counter() - started)
    return best * 1000


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=int, nargs="+", default=[1_000, 10_000, 100_000])
    parser.add_argument("--key", default="LEMONADE", help="Vigenere key to benchmark")
    args = parser.parse_args()

    print(f"Cryptic benchmark  (Python {sys.version.split()[0]})")
    print(f"Vigenere key: {args.key!r} ({len(args.key)} letters)\n")
    header = f"{'letters':>9} | {'C-enc':>8} | {'C-break':>8} | {'V-enc':>8} | {'V-break':>9} | {'V key':>10}"
    print(header)
    print("-" * len(header))

    for size in args.sizes:
        text = make_text(size)
        caesar_ct = caesar.encrypt(text, 7)
        vigenere_ct = vigenere.encrypt(text, args.key)

        c_enc = time_it(caesar.encrypt, text, 7)
        c_break = time_it(caesar_breaker.break_caesar, caesar_ct)
        v_enc = time_it(vigenere.encrypt, text, args.key)
        v_break = time_it(vigenere_breaker.break_vigenere, vigenere_ct, repeats=1)
        found = vigenere_breaker.break_vigenere(vigenere_ct).key

        print(
            f"{size:>9,} | {c_enc:>7.2f}m | {c_break:>7.2f}m | {v_enc:>7.2f}m "
            f"| {v_break:>8.1f}m | {found:>10}"
        )

    print("\nAll times in milliseconds (m), best of 3.")
    print("For scale: a brute-force search of AES-256's keyspace at one trillion")
    print("keys per second would still take about 10^57 years.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
