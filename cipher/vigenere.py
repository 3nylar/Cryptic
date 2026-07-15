"""The Vigenere cipher: a Caesar cipher whose shift changes every letter.

Plain English first
-------------------
The Caesar cipher's flaw is that it is boringly consistent: every E in the
message becomes the same letter. The Vigenere cipher fixes that by using a
*keyword* instead of a single number. Write the keyword under the message,
repeating it as often as needed:

    message:  A T T A C K A T D A W N
    keyword:  L E M O N L E M O N L E
    shift:    11 4 12 14 13 11 4 12 14 13 11 4

Each letter now gets its own shift, taken from the keyword letter above it. The
first A is shifted 11 places, the second A is shifted 14 places, so the two A's
encrypt to *different* letters. For 300 years this was considered unbreakable
and nicknamed *le chiffre indechiffrable* — "the indecipherable cipher".

Key generation
--------------
The keyword is repeated cyclically, but only over *letters*: spaces and
punctuation do not consume a key letter. This matters, because if punctuation
advanced the key, an attacker who knew the punctuation would learn about the
key stream for free.

The mathematics
---------------
With key letters k_0 ... k_(m-1) and message letter x at letter-position i:

    encrypt:  E(x_i) = (x_i + k_(i mod m)) mod 26
    decrypt:  D(y_i) = (y_i - k_(i mod m)) mod 26

Strengths: it is *polyalphabetic*, so a single-alphabet frequency count on the
whole ciphertext is flat and useless. The keyspace is 26^m for a key of length
m — a 12-letter key gives roughly 10^17 keys, far beyond brute force.

Weakness: the key repeats. Once an attacker guesses the key length m, the
ciphertext splits into m independent Caesar ciphers, and each falls in
microseconds. Keyspace size is not security. See :mod:`analysis.vigenere_breaker`.

Complexity: O(n) time, O(m) extra memory for the key.
"""

from __future__ import annotations

from utils.alphabet import (
    char_to_index,
    index_to_char,
    is_letter,
    letters_only,
    preserve_case,
)

__all__ = ["encrypt", "decrypt", "validate_key", "key_schedule"]


class VigenereKeyError(ValueError):
    """Raised when a Vigenere keyword is empty or contains non-letters."""


def validate_key(key: object) -> str:
    """Check a Vigenere keyword and return it uppercased.

    A valid key is a non-empty string of ASCII letters. Digits, spaces and
    punctuation are rejected loudly rather than silently stripped: silently
    turning ``"lemon 5"`` into ``"LEMON"`` would mean the user's encryption and
    the user's decryption could disagree about the key.

    Raises:
        VigenereKeyError: if the key is empty or contains non-letters.

    Examples:
        >>> validate_key("Lemon")
        'LEMON'
    """
    if not isinstance(key, str):
        raise VigenereKeyError(f"key must be text (got {type(key).__name__})")
    stripped = key.strip()
    if not stripped:
        raise VigenereKeyError("key must not be empty")
    if not all(is_letter(c) for c in stripped):
        raise VigenereKeyError(
            f"key must contain only letters A-Z (got {key!r})"
        )
    return stripped.upper()


def key_schedule(key: str, length: int) -> list[int]:
    """Return the first ``length`` shifts produced by repeating ``key``.

    Examples:
        >>> key_schedule("LEMON", 7)
        [11, 4, 12, 14, 13, 11, 4]
    """
    validated = validate_key(key)
    shifts = [char_to_index(c) for c in validated]
    return [shifts[i % len(shifts)] for i in range(length)]


def _apply(text: str, key: str, sign: int) -> str:
    """Shared engine for encrypt (sign=+1) and decrypt (sign=-1)."""
    validated = validate_key(key)
    shifts = [char_to_index(c) for c in validated]
    out = []
    position = 0  # counts letters only, so punctuation never advances the key
    for char in text:
        if is_letter(char):
            k = shifts[position % len(shifts)]
            new = index_to_char(char_to_index(char) + sign * k)
            out.append(preserve_case(char, new))
            position += 1
        else:
            out.append(char)
    return "".join(out)


def encrypt(plaintext: str, key: str) -> str:
    """Encrypt ``plaintext`` with the repeating keyword ``key``.

    Examples:
        >>> encrypt("Attack at dawn!", "LEMON")
        'Lxfopv ef rnhr!'
    """
    return _apply(plaintext, key, +1)


def decrypt(ciphertext: str, key: str) -> str:
    """Decrypt ``ciphertext`` with the repeating keyword ``key``.

    Examples:
        >>> decrypt("Lxfopv ef rnhr!", "LEMON")
        'Attack at dawn!'
    """
    return _apply(ciphertext, key, -1)


def effective_key_length(key: str, text: str) -> int:
    """How many distinct key letters actually touch ``text``.

    Useful for warnings: a 20-letter key on an 8-letter message uses only 8 of
    its letters, so the extra key material adds nothing.
    """
    return min(len(validate_key(key)), len(letters_only(text)))
