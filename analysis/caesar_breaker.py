"""Breaking the Caesar cipher automatically, and explaining how as it goes.

The attack in one paragraph
---------------------------
There are only 26 keys, so we simply try all of them. That gives 26 candidate
plaintexts, 25 of which are gibberish. The only question left is: which one is
English? We answer it with :func:`analysis.frequency.english_score` — the
candidate whose letter frequencies look most like English wins. No dictionary
of the message is needed, no guessing, no luck. On any modern laptop the whole
attack takes well under a millisecond.

This is the *ciphertext-only* attack: we need nothing but the encrypted message
itself. It is the weakest thing an attacker can be given, and it is still
enough. That is what "broken" means in cryptography.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from cipher import caesar
from analysis.frequency import chi_squared, confidence, english_score
from utils.alphabet import ALPHABET_SIZE, letters_only

logger = logging.getLogger(__name__)

__all__ = ["Candidate", "CaesarBreakResult", "break_caesar"]


@dataclass(frozen=True)
class Candidate:
    """One of the 26 possible decryptions, with its scores."""

    shift: int
    plaintext: str
    chi_squared: float
    score: float

    def preview(self, width: int = 60) -> str:
        """First ``width`` characters of the plaintext, for table display."""
        single_line = " ".join(self.plaintext.split())
        if len(single_line) <= width:
            return single_line
        return single_line[: width - 1] + "\u2026"


@dataclass
class CaesarBreakResult:
    """Everything the Caesar attack learned, ready to display or export."""

    ciphertext: str
    candidates: list[Candidate]  # sorted best-first
    confidence: float
    elapsed_seconds: float
    steps: list[str] = field(default_factory=list)

    @property
    def best(self) -> Candidate:
        """The winning candidate."""
        return self.candidates[0]

    @property
    def key(self) -> int:
        """The recovered shift."""
        return self.best.shift

    @property
    def plaintext(self) -> str:
        """The recovered plaintext."""
        return self.best.plaintext

    def to_dict(self) -> dict:
        """Plain-data view, used by the JSON/Markdown exporters."""
        return {
            "cipher": "caesar",
            "recovered_key": self.key,
            "confidence": self.confidence,
            "elapsed_seconds": round(self.elapsed_seconds, 6),
            "plaintext": self.plaintext,
            "steps": self.steps,
            "candidates": [
                {
                    "shift": c.shift,
                    "chi_squared": round(c.chi_squared, 2),
                    "score": round(c.score, 2),
                    "preview": c.preview(),
                }
                for c in self.candidates
            ],
        }


def break_caesar(ciphertext: str, top_n: int = 26) -> CaesarBreakResult:
    """Recover the shift and plaintext from Caesar ciphertext alone.

    Args:
        ciphertext: The encrypted message. Case, spacing and punctuation are
            all ignored by the scoring, and preserved in the output.
        top_n: How many ranked candidates to keep (1-26).

    Returns:
        A :class:`CaesarBreakResult`. Even for text with no letters a result is
        returned, with confidence 0.0 — the CLI prefers a clearly-labelled
        no-confidence answer over an exception here.

    Examples:
        >>> from cipher import caesar
        >>> ct = caesar.encrypt("the quick brown fox jumps over the lazy dog", 7)
        >>> result = break_caesar(ct)
        >>> result.key
        7
    """
    started = time.perf_counter()
    letters = letters_only(ciphertext)
    steps: list[str] = [
        f"Read {len(letters)} letters of ciphertext "
        f"({len(ciphertext)} characters including spaces and punctuation).",
        f"The Caesar keyspace is only {ALPHABET_SIZE} keys, so try every one of them.",
    ]

    candidates: list[Candidate] = []
    for shift in range(ALPHABET_SIZE):
        plaintext = caesar.decrypt(ciphertext, shift)
        candidates.append(
            Candidate(
                shift=shift,
                plaintext=plaintext,
                chi_squared=chi_squared(plaintext),
                score=english_score(plaintext),
            )
        )

    candidates.sort(key=lambda c: c.score)
    steps.append(
        "Score each of the 26 candidates with the chi-squared test against "
        "English letter frequencies (lower = more English-like)."
    )

    if len(letters) == 0:
        conf = 0.0
        steps.append("No letters found, so nothing can be scored. Confidence 0.")
    else:
        best, second = candidates[0], candidates[1]
        conf = confidence(best.score, second.score)
        steps.append(
            f"Best candidate: shift {best.shift} scores {best.score:.1f}; "
            f"runner-up shift {second.shift} scores {second.score:.1f}. "
            f"The winner is {second.score / max(best.score, 1e-9):.1f}x better, "
            f"which is why confidence is {conf:.0%}."
        )
        steps.append(
            f"Recovered key = {best.shift}. Decrypting with it gives readable English."
        )

    elapsed = time.perf_counter() - started
    logger.info(
        "caesar break: %d letters, key=%s, confidence=%.2f, %.4f ms",
        len(letters),
        candidates[0].shift,
        conf,
        elapsed * 1000,
    )
    return CaesarBreakResult(
        ciphertext=ciphertext,
        candidates=candidates[: max(1, min(top_n, ALPHABET_SIZE))],
        confidence=conf,
        elapsed_seconds=elapsed,
        steps=steps,
    )
