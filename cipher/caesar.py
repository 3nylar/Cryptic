"""The Caesar cipher: shift every letter a fixed number of places.

Plain English first
-------------------
Imagine a decoder ring with two rings of letters, an inner one and an outer
one. Turn the inner ring three clicks and line it up: A now sits under D, B
under E, and so on. To encrypt, you look up each letter of your message on the
outer ring and write down the letter beneath it. To decrypt, you turn the ring
back the same three clicks.

That "number of clicks" is the **key**. For the Caesar cipher the key is a
single number from 0 to 25, which is why there are only 26 possible keys — and
why a computer can try all of them in microseconds.

The mathematics
---------------
With letters written as numbers (A=0 ... Z=25) and a key ``k``:

    encrypt:  E(x) = (x + k) mod 26
    decrypt:  D(y) = (y - k) mod 26

``mod 26`` ("modulo 26") means *take the remainder after dividing by 26*. It is
what makes the alphabet wrap around: Z + 1 lands back on A.

Complexity: encryption and decryption are O(n) in the length of the message,
and each character costs constant time and memory.
"""

from __future__ import annotations

from utils.alphabet import (
    ALPHABET_SIZE,
    char_to_index,
    index_to_char,
    is_letter,
    normalise_shift,
    preserve_case,
)

__all__ = ["encrypt", "decrypt", "validate_shift", "brute_force"]


class CaesarKeyError(ValueError):
    """Raised when a Caesar key is not usable as a shift."""


def validate_shift(shift: object) -> int:
    """Coerce and check a Caesar key, returning it normalised to 0-25.

    Accepts an ``int`` or a string of digits (optionally signed) so that CLI
    input can be passed straight through.

    Raises:
        CaesarKeyError: if the value is not an integer at all.

    Examples:
        >>> validate_shift(3)
        3
        >>> validate_shift("-1")   # negative shifts wrap around
        25
        >>> validate_shift(29)     # large shifts wrap around
        3
    """
    if isinstance(shift, bool):  # bool is a subclass of int; reject it explicitly
        raise CaesarKeyError("shift must be an integer, not a boolean")
    if isinstance(shift, int):
        return normalise_shift(shift)
    if isinstance(shift, str):
        text = shift.strip()
        try:
            return normalise_shift(int(text))
        except ValueError as exc:
            raise CaesarKeyError(
                f"shift must be a whole number (got {shift!r})"
            ) from exc
    raise CaesarKeyError(f"shift must be a whole number (got {shift!r})")


def encrypt(plaintext: str, shift: object) -> str:
    """Encrypt ``plaintext`` by shifting each letter forward by ``shift``.

    Non-letters (spaces, digits, punctuation, emoji) pass through unchanged,
    and the case of each letter is preserved.

    Examples:
        >>> encrypt("Attack at dawn!", 3)
        'Dwwdfn dw gdzq!'
        >>> encrypt("Hello", 0)      # a key of 0 is the identity
        'Hello'
    """
    k = validate_shift(shift)
    out = []
    for char in plaintext:
        if is_letter(char):
            shifted = index_to_char(char_to_index(char) + k)
            out.append(preserve_case(char, shifted))
        else:
            out.append(char)
    return "".join(out)


def decrypt(ciphertext: str, shift: object) -> str:
    """Decrypt ``ciphertext`` produced with ``shift``.

    Decryption is encryption with the opposite shift, which is the whole reason
    the Caesar cipher is called *symmetric*: the same secret does both jobs.

    Examples:
        >>> decrypt("Dwwdfn dw gdzq!", 3)
        'Attack at dawn!'
    """
    k = validate_shift(shift)
    return encrypt(ciphertext, -k)


def brute_force(ciphertext: str) -> list[tuple[int, str]]:
    """Return all 26 possible decryptions as ``(shift, plaintext)`` pairs.

    This is the entire keyspace of the cipher. A human can eyeball the list and
    spot the English one instantly — which is precisely the weakness that
    :mod:`analysis.caesar_breaker` automates.
    """
    return [(k, decrypt(ciphertext, k)) for k in range(ALPHABET_SIZE)]
