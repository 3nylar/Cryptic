"""Low-level helpers for working with the 26-letter English alphabet.

Every cipher in this project is a *substitution* cipher: it swaps each letter of
the message for a different letter. To do that with arithmetic instead of a
lookup table, we first turn letters into numbers:

    A -> 0, B -> 1, C -> 2, ... Z -> 25

Once letters are numbers, "shift three places forward" is just "add 3", and
"wrap around from Z back to A" is just "take the remainder after dividing by
26" (written ``% 26`` in Python, and called *modular arithmetic*).

This module is deliberately tiny and dependency-free. Everything else in the
project builds on it.
"""

from __future__ import annotations

import unicodedata

ALPHABET_SIZE = 26
"""Number of letters in the English alphabet. Used as the modulus everywhere."""

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def is_letter(char: str) -> bool:
    """Return True if ``char`` is one of the 26 ASCII letters (either case)."""
    return "A" <= char <= "Z" or "a" <= char <= "z"


def char_to_index(char: str) -> int:
    """Convert a letter to its 0-based alphabet position (``'C' -> 2``).

    Raises:
        ValueError: if ``char`` is not an ASCII letter.
    """
    if not is_letter(char):
        raise ValueError(f"not an ASCII letter: {char!r}")
    return ord(char.upper()) - ord("A")


def index_to_char(index: int, uppercase: bool = True) -> str:
    """Convert a 0-based alphabet position back to a letter (``2 -> 'C'``).

    The index is reduced modulo 26 first, so 26 becomes 'A' and -1 becomes 'Z'.
    """
    base = ord("A") if uppercase else ord("a")
    return chr(base + (index % ALPHABET_SIZE))


def normalise_shift(shift: int) -> int:
    """Reduce any integer shift into the canonical range 0-25.

    A shift of 29 behaves exactly like a shift of 3, and a shift of -1 behaves
    exactly like a shift of 25. Python's ``%`` already returns a non-negative
    result for a positive modulus, which is why negative shifts "just work".
    """
    return shift % ALPHABET_SIZE


def letters_only(text: str) -> str:
    """Strip everything that is not a letter and uppercase what remains.

    Cryptanalysis only cares about letters: spaces, digits and punctuation
    carry no frequency information for these ciphers. ``"Hi, Bob!"`` becomes
    ``"HIBOB"``.
    """
    return "".join(c.upper() for c in text if is_letter(c))


def fold_unicode(text: str) -> str:
    """Best-effort conversion of accented Latin text into plain ASCII letters.

    ``"café"`` becomes ``"cafe"``. This uses Unicode NFKD decomposition, which
    splits 'é' into 'e' + a combining accent, then drops the accent. Characters
    with no ASCII equivalent (Greek, Cyrillic, emoji) are left untouched and
    will simply be treated as non-letters downstream.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def preserve_case(source_char: str, new_char: str) -> str:
    """Return ``new_char`` wearing the case of ``source_char``."""
    return new_char.upper() if source_char.isupper() else new_char.lower()
