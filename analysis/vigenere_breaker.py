"""Breaking the Vigenere cipher with classical cryptanalysis.

The attack in three moves
-------------------------
The Vigenere cipher hides the English fingerprint by using several alphabets in
rotation. But the rotation *repeats*, and that is fatal.

1. **How long is the key?** Two independent methods vote on it:

   * *Kasiski examination* (Friedrich Kasiski, 1863). If the same word lands on
     the same part of the key twice, it encrypts to the same ciphertext both
     times. So repeated chunks in the ciphertext are usually not coincidence:
     the distance between them is a multiple of the key length. Collect those
     distances, factor them, and the key length is the factor that keeps
     showing up.
   * *Index of coincidence*. Take every m-th letter of the ciphertext. If m is
     the true key length, all those letters were shifted by the *same* key
     letter, so that slice is pure Caesar-encrypted English and its IC jumps to
     ~0.067. If m is wrong, the slice is still a mix and its IC stays near
     0.038. Try every m and look for the jump.

2. **Split the problem.** Once m is known, the ciphertext splits into m columns,
   and each column is nothing but a Caesar cipher.

3. **Solve each column.** Run the ordinary chi-squared Caesar attack on each
   column independently. Each answer is one letter of the key.

The cost collapses from 26^m (hopeless) to 26 x m (instant). A 10-letter key
takes 260 tests instead of 141 trillion. This is why "the keyspace is huge" is
not a security argument.

What can go wrong
-----------------
The IC is a statistic, and statistics need data. Under roughly 20 letters per
column the signal is noise, so this module reports low confidence instead of
pretending. The CLI surfaces that number honestly.
"""

from __future__ import annotations

import logging
import time
from collections import Counter
from dataclasses import dataclass, field

from analysis.frequency import (
    ENGLISH_IOC,
    RANDOM_IOC,
    bigram_fitness,
    chi_squared,
    fitness_confidence,
    index_of_coincidence,
)
from cipher import vigenere
from utils.alphabet import ALPHABET_SIZE, index_to_char, letters_only

logger = logging.getLogger(__name__)

__all__ = [
    "KeyLengthGuess",
    "VigenereBreakResult",
    "kasiski_examination",
    "ioc_key_lengths",
    "estimate_key_length",
    "recover_key",
    "break_vigenere",
]

MIN_LETTERS_PER_COLUMN = 20
"""Below this, per-column statistics are unreliable and we say so."""


@dataclass(frozen=True)
class KeyLengthGuess:
    """One candidate key length with the evidence supporting it."""

    length: int
    average_ioc: float
    kasiski_votes: int
    combined_score: float


@dataclass
class VigenereBreakResult:
    """Everything the Vigenere attack learned, ready to display or export."""

    ciphertext: str
    key: str
    plaintext: str
    key_length_guesses: list[KeyLengthGuess]
    kasiski_factors: dict[int, int]
    confidence: float
    elapsed_seconds: float
    steps: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "cipher": "vigenere",
            "recovered_key": self.key,
            "key_length": len(self.key),
            "confidence": self.confidence,
            "elapsed_seconds": round(self.elapsed_seconds, 6),
            "plaintext": self.plaintext,
            "steps": self.steps,
            "warnings": self.warnings,
            "key_length_guesses": [
                {
                    "length": g.length,
                    "average_ioc": round(g.average_ioc, 4),
                    "kasiski_votes": g.kasiski_votes,
                    "combined_score": round(g.combined_score, 4),
                }
                for g in self.key_length_guesses
            ],
        }


def minimal_period(key: str) -> str:
    """Reduce a key to its shortest repeating unit.

    ``"LEMONLEMON"`` decrypts exactly like ``"LEMON"``, and ``"DD"`` like
    ``"D"``. When the length estimator lands on a multiple of the true key
    length, the recovered key is the true key written out twice — so reporting
    the minimal period is both more honest and more useful.

    Examples:
        >>> minimal_period("LEMONLEMON")
        'LEMON'
        >>> minimal_period("ABCAB")
        'ABCAB'
    """
    n = len(key)
    for period in range(1, n):
        if n % period == 0 and key == key[:period] * (n // period):
            return key[:period]
    return key


def _factors(number: int, max_factor: int) -> list[int]:
    """All factors of ``number`` from 2 up to ``max_factor``."""
    return [f for f in range(2, min(number, max_factor) + 1) if number % f == 0]


def kasiski_examination(
    ciphertext: str, min_sequence: int = 3, max_key_length: int = 20
) -> dict[int, int]:
    """Find repeated sequences and vote on key length via their spacings.

    Args:
        ciphertext: Text to examine (non-letters ignored).
        min_sequence: Length of repeated chunk to hunt for. Three is the
            classic choice: shorter repeats happen by chance too often.
        max_key_length: Largest key length to consider.

    Returns:
        ``{key_length: votes}``, where a vote means "some repeat distance was
        divisible by this length". The true key length usually tops the poll —
        but so do its own factors, which is why this evidence is combined with
        the IC rather than trusted alone.

    Examples:
        >>> from cipher import vigenere
        >>> ct = vigenere.encrypt("the sun and the man in the moon " * 6, "KEY")
        >>> votes = kasiski_examination(ct)
        >>> max(votes, key=votes.get) in (3, 6, 9, 12, 15, 18)
        True
    """
    letters = letters_only(ciphertext)
    positions: dict[str, list[int]] = {}
    for i in range(len(letters) - min_sequence + 1):
        chunk = letters[i : i + min_sequence]
        positions.setdefault(chunk, []).append(i)

    votes: Counter = Counter()
    for chunk, occurrences in positions.items():
        if len(occurrences) < 2:
            continue
        for earlier, later in zip(occurrences, occurrences[1:]):
            distance = later - earlier
            for factor in _factors(distance, max_key_length):
                votes[factor] += 1
    return dict(votes)


def ioc_key_lengths(
    ciphertext: str, max_key_length: int = 20
) -> list[tuple[int, float]]:
    """Average index of coincidence of the columns for each candidate length.

    Returns ``[(length, average_ioc), ...]`` for lengths 1..max. Look for the
    first length whose average IC is close to English's 0.067 — that is the key
    length. Multiples of it score well too (they are made of the same columns
    sliced finer), so prefer the *shortest* length that scores high.
    """
    letters = letters_only(ciphertext)
    results = []
    for length in range(1, max_key_length + 1):
        if len(letters) < length * 2:
            break
        columns = [letters[i::length] for i in range(length)]
        iocs = [index_of_coincidence(col) for col in columns if len(col) > 1]
        results.append((length, sum(iocs) / len(iocs) if iocs else 0.0))
    return results


def estimate_key_length(
    ciphertext: str, max_key_length: int = 20
) -> list[KeyLengthGuess]:
    """Rank candidate key lengths using IC and Kasiski evidence together.

    The IC provides the main signal; Kasiski breaks ties. A small penalty is
    applied to longer candidates so that the key length is preferred over its
    own multiples (a length of 10 always scores at least as well as 5 when the
    real key is 5, but 5 is the answer).
    """
    ioc_table = ioc_key_lengths(ciphertext, max_key_length)
    kasiski = kasiski_examination(ciphertext, max_key_length=max_key_length)
    max_votes = max(kasiski.values(), default=0)

    guesses: list[KeyLengthGuess] = []
    for length, average_ioc in ioc_table:
        # How far along the road from random (0.038) to English (0.067) is this?
        closeness = (average_ioc - RANDOM_IOC) / (ENGLISH_IOC - RANDOM_IOC)
        closeness = max(0.0, min(closeness, 1.2))
        vote_share = (kasiski.get(length, 0) / max_votes) if max_votes else 0.0
        length_penalty = 0.012 * (length - 1)  # prefer the shortest good fit
        combined = closeness + 0.35 * vote_share - length_penalty
        guesses.append(
            KeyLengthGuess(
                length=length,
                average_ioc=average_ioc,
                kasiski_votes=kasiski.get(length, 0),
                combined_score=combined,
            )
        )
    guesses.sort(key=lambda g: g.combined_score, reverse=True)
    return guesses


def recover_key(ciphertext: str, key_length: int) -> str:
    """Recover the keyword, assuming ``key_length`` is correct.

    Each column is a Caesar cipher; the shift that makes a column look most
    like English is that position's key letter.

    Raises:
        ValueError: if ``key_length`` is less than 1.
    """
    if key_length < 1:
        raise ValueError("key_length must be at least 1")
    letters = letters_only(ciphertext)
    key_chars = []
    for i in range(key_length):
        column = letters[i::key_length]
        if not column:
            key_chars.append("A")
            continue
        best_shift, best_score = 0, float("inf")
        for shift in range(ALPHABET_SIZE):
            shifted = "".join(
                index_to_char(ord(c) - ord("A") - shift) for c in column
            )
            score = chi_squared(shifted)
            if score < best_score:
                best_shift, best_score = shift, score
        key_chars.append(index_to_char(best_shift))
    return "".join(key_chars)


def break_vigenere(
    ciphertext: str,
    max_key_length: int = 20,
    known_key_length: int | None = None,
    candidates_to_try: int = 3,
) -> VigenereBreakResult:
    """Recover the keyword and plaintext from Vigenere ciphertext alone.

    Args:
        ciphertext: The encrypted message.
        max_key_length: Largest key length to consider.
        known_key_length: Skip length estimation and use this instead. Useful
            when a Kasiski analysis was done by hand, or in teaching.
        candidates_to_try: How many top-ranked key lengths to fully solve
            before picking a winner. Trying the top 3 and scoring the resulting
            plaintexts is far more robust than trusting the IC's first choice.

    Returns:
        A :class:`VigenereBreakResult`, including a ``warnings`` list when the
        ciphertext is too short for the statistics to be trustworthy.

    Examples:
        >>> from cipher import vigenere
        >>> text = "we hold these truths to be self evident that all men are created equal " * 4
        >>> result = break_vigenere(vigenere.encrypt(text, "LEMON"))
        >>> result.key
        'LEMON'
    """
    started = time.perf_counter()
    letters = letters_only(ciphertext)
    steps: list[str] = [
        f"Read {len(letters)} letters of ciphertext.",
        f"Whole-text index of coincidence = {index_of_coincidence(letters):.4f} "
        f"(English ~ {ENGLISH_IOC}, random ~ {RANDOM_IOC:.4f}). "
        "A value near random says several alphabets are in use, i.e. Vigenere, not Caesar.",
    ]
    warnings: list[str] = []

    if len(letters) < 2:
        elapsed = time.perf_counter() - started
        return VigenereBreakResult(
            ciphertext=ciphertext,
            key="",
            plaintext=ciphertext,
            key_length_guesses=[],
            kasiski_factors={},
            confidence=0.0,
            elapsed_seconds=elapsed,
            steps=steps + ["Too few letters to analyse."],
            warnings=["Ciphertext contains fewer than 2 letters; nothing to attack."],
        )

    kasiski = kasiski_examination(ciphertext, max_key_length=max_key_length)
    if kasiski:
        top = sorted(kasiski.items(), key=lambda kv: -kv[1])[:5]
        steps.append(
            "Kasiski examination: distances between repeated 3-letter chunks "
            "favour key lengths "
            + ", ".join(f"{length} ({votes} votes)" for length, votes in top)
            + "."
        )
    else:
        steps.append(
            "Kasiski examination found no repeated 3-letter chunks "
            "(the text is short); relying on the index of coincidence alone."
        )

    if known_key_length is not None:
        guesses = [
            KeyLengthGuess(known_key_length, 0.0, kasiski.get(known_key_length, 0), 1.0)
        ]
        steps.append(f"Key length was supplied by the user: {known_key_length}.")
    else:
        guesses = estimate_key_length(ciphertext, max_key_length)
        if guesses:
            shortlist = ", ".join(
                f"{g.length} (IC {g.average_ioc:.3f})" for g in guesses[:4]
            )
            steps.append(
                f"Slicing the text every m letters and averaging each slice's IC "
                f"ranks the key lengths: {shortlist}."
            )

    if not guesses:
        guesses = [KeyLengthGuess(1, 0.0, 0, 0.0)]

    # Solve the top few candidate lengths properly and let the plaintext decide.
    attempts = []
    for guess in guesses[: max(1, candidates_to_try)]:
        key = minimal_period(recover_key(ciphertext, guess.length))
        plaintext = vigenere.decrypt(ciphertext, key) if key else ciphertext
        attempts.append((bigram_fitness(plaintext), guess, key, plaintext))
    attempts.sort(key=lambda a: -a[0])  # higher fitness is better

    # Occam's razor, and a warning worth internalising: a longer key has more
    # free parameters, so it can fit the *letter counts* at least as well as the
    # true key even when it is wrong. That is why the candidates are judged on
    # bigram fitness (which no per-column shift can fake) and why, among
    # near-equal candidates, the shortest key wins.
    best_fitness = attempts[0][0]
    tolerance = 0.05  # log10 units; ~12% probability per letter pair
    plausible = [a for a in attempts if a[0] >= best_fitness - tolerance]
    plausible.sort(key=lambda a: (len(a[2]), -a[0]))
    best_fitness, best_guess, best_key, best_plaintext = plausible[0]

    steps.append(
        f"For each candidate length, split the text into that many columns "
        f"(each column is a plain Caesar cipher) and solve every column with "
        f"chi-squared. Then judge each resulting plaintext on letter *pairs* "
        f"(TH, HE, IN...), which a per-column shift cannot fake."
    )
    steps.append(
        f"Shortest key that explains the text: {len(best_key)} letters. "
        f"Recovered key = {best_key!r}."
    )

    others = [a[0] for a in attempts if a[2] != best_key]
    conf = fitness_confidence(best_fitness, max(others) if others else None)

    letters_per_column = len(letters) / max(len(best_key), 1)
    if letters_per_column < MIN_LETTERS_PER_COLUMN:
        warnings.append(
            f"Only ~{letters_per_column:.0f} letters per key position "
            f"(want {MIN_LETTERS_PER_COLUMN}+). Frequency statistics are shaky here, "
            "so treat the key as a guess rather than a result."
        )
        conf = min(conf, 0.45)
    steps.append(
        f"Confidence {conf:.0%}, based on how English the plaintext looks and how "
        "far ahead it is of the next-best key length."
    )

    elapsed = time.perf_counter() - started
    logger.info(
        "vigenere break: %d letters, key=%s, confidence=%.2f, %.1f ms",
        len(letters),
        best_key,
        conf,
        elapsed * 1000,
    )
    return VigenereBreakResult(
        ciphertext=ciphertext,
        key=best_key,
        plaintext=best_plaintext,
        key_length_guesses=guesses[:8],
        kasiski_factors=kasiski,
        confidence=conf,
        elapsed_seconds=elapsed,
        steps=steps,
        warnings=warnings,
    )
