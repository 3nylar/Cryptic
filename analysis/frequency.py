"""Frequency analysis: the statistical toolkit both attacks are built on.

The one idea behind this whole module
-------------------------------------
English is lumpy. If you take a page of ordinary English and count the letters,
E turns up about 12% of the time while Z turns up about 0.07% of the time. That
lumpiness is a fingerprint, and a Caesar or Vigenere cipher does not erase it —
it only slides it sideways. Find where the fingerprint went, and you have found
the key.

The tools below all measure "how English does this look?" in different ways:

* :func:`letter_frequencies` — the raw fingerprint.
* :func:`chi_squared` — how far a fingerprint is from English. Lower is better.
* :func:`index_of_coincidence` — how lumpy a text is at all, regardless of
  which letters are which. This is what reveals a Vigenere key's length.
* :func:`english_score` and :func:`confidence` — human-friendly verdicts.
"""

from __future__ import annotations

import logging
import math
from collections import Counter
from pathlib import Path

from utils.alphabet import ALPHABET, ALPHABET_SIZE, letters_only

__all__ = [
    "ENGLISH_FREQUENCIES",
    "ENGLISH_IOC",
    "RANDOM_IOC",
    "letter_counts",
    "letter_frequencies",
    "chi_squared",
    "index_of_coincidence",
    "english_score",
    "bigram_fitness",
    "fitness_confidence",
    "confidence",
    "histogram_rows",
]

# Letter frequencies of ordinary English prose, as proportions summing to 1.0.
# (Standard corpus figures; any modern source agrees to within ~0.2%.)
ENGLISH_FREQUENCIES: dict[str, float] = {
    "A": 0.08167, "B": 0.01492, "C": 0.02782, "D": 0.04253, "E": 0.12702,
    "F": 0.02228, "G": 0.02015, "H": 0.06094, "I": 0.06966, "J": 0.00153,
    "K": 0.00772, "L": 0.04025, "M": 0.02406, "N": 0.06749, "O": 0.07507,
    "P": 0.01929, "Q": 0.00095, "R": 0.05987, "S": 0.06327, "T": 0.09056,
    "U": 0.02758, "V": 0.00978, "W": 0.02360, "X": 0.00150, "Y": 0.01974,
    "Z": 0.00074,
}

ENGLISH_IOC = 0.0667
"""Index of coincidence expected from English text (see :func:`index_of_coincidence`)."""

RANDOM_IOC = 1 / ALPHABET_SIZE  # 0.03846
"""Index of coincidence expected from uniformly random letters."""

# The 60 most common English words. Used for a cheap sanity check that a
# candidate plaintext contains real words and not just English-ish letters.
COMMON_WORDS: frozenset[str] = frozenset(
    """the be to of and a in that have i it for not on with he as you do at this
    but his by from they we say her she or an will my one all would there their
    what so up out if about who get which go me when make can like time no just
    him know take people into year your good some could them""".split()
)


def letter_counts(text: str) -> Counter:
    """Count each letter A-Z in ``text``, ignoring case and non-letters.

    Every letter appears in the result, including ones that never occur, so
    callers can rely on all 26 keys being present.

    Examples:
        >>> letter_counts("Bee!")["E"]
        2
        >>> letter_counts("Bee!")["Z"]
        0
    """
    counts = Counter({letter: 0 for letter in ALPHABET})
    counts.update(letters_only(text))
    return counts


def letter_frequencies(text: str) -> dict[str, float]:
    """Return each letter's share of the text, as proportions summing to 1.0.

    An empty text yields all zeros rather than a ZeroDivisionError.
    """
    counts = letter_counts(text)
    total = sum(counts.values())
    if total == 0:
        return {letter: 0.0 for letter in ALPHABET}
    return {letter: counts[letter] / total for letter in ALPHABET}


def chi_squared(text: str) -> float:
    """Measure how far ``text``'s letter distribution is from English.

    The chi-squared statistic compares what we *observed* against what we would
    *expect* if the text were English::

        X^2 = sum over letters of  (observed - expected)^2 / expected

    Read it as a penalty score: a perfect match scores 0, and the more the
    observed counts deviate from English, the larger it grows. Because each
    difference is squared, one wildly wrong letter costs more than several
    slightly wrong ones. Dividing by ``expected`` keeps rare letters from being
    ignored: being 10 counts over on Z is far more suspicious than being 10
    counts over on E.

    **Lower is better.** For real English of a few hundred letters expect
    roughly 10-40; a wrong Caesar shift typically scores in the hundreds.

    Returns ``inf`` for text with no letters, since nothing can be judged.

    Examples:
        >>> round(chi_squared("ETAOIN SHRDLU")) < round(chi_squared("ZZZZZZ QQQQQQ"))
        True
    """
    counts = letter_counts(text)
    total = sum(counts.values())
    if total == 0:
        return float("inf")
    score = 0.0
    for letter in ALPHABET:
        expected = ENGLISH_FREQUENCIES[letter] * total
        difference = counts[letter] - expected
        score += (difference * difference) / expected
    return score


def index_of_coincidence(text: str) -> float:
    """Probability that two letters drawn at random from ``text`` match.

    Pick two letters out of the text blindly. How often are they the same
    letter? In random gibberish, once every 26 tries (about 0.038). In English,
    far more often — about 0.067 — because so much of the text is E, T, A and O.

    The formula counts every unordered pair of identical letters and divides by
    the total number of pairs::

        IC = sum over letters of  n_i(n_i - 1)  /  N(N - 1)

    Why this matters: the value **does not change when you shift the alphabet**.
    Caesar-encrypting English leaves the IC at 0.067, because the lumps just
    move. But a Vigenere cipher with a long key *mixes* several alphabets and
    flattens the lumps toward 0.038. That single number tells an attacker
    whether they are facing one alphabet or many — and, applied to slices of
    the text, how many.

    Texts shorter than two letters return 0.0.
    """
    counts = letter_counts(text)
    total = sum(counts.values())
    if total < 2:
        return 0.0
    numerator = sum(n * (n - 1) for n in counts.values())
    return numerator / (total * (total - 1))


def word_hit_rate(text: str) -> float:
    """Fraction of whitespace-separated tokens that are common English words.

    Returns 0.0 when the text has no word breaks at all (classic ciphertext is
    often written in unbroken blocks), so callers should treat this as a bonus
    signal, never as the sole verdict.
    """
    tokens = [
        "".join(c for c in token if c.isalpha()).lower()
        for token in text.split()
    ]
    tokens = [t for t in tokens if t]
    if not tokens:
        return 0.0
    hits = sum(1 for t in tokens if t in COMMON_WORDS)
    return hits / len(tokens)


def english_score(text: str) -> float:
    """Combined "how English is this?" penalty. Lower is better.

    Chi-squared does the heavy lifting; recognising real words shaves up to 30%
    off the penalty, which breaks ties between two shifts that look equally
    plausible letter-wise.
    """
    base = chi_squared(text)
    if base == float("inf"):
        return base
    return base * (1.0 - 0.3 * word_hit_rate(text))


def confidence(best: float, runner_up: float | None = None) -> float:
    """Turn raw scores into a 0-1 confidence figure for display.

    Two things make us confident: the winning candidate looks like English in
    absolute terms (low chi-squared), *and* it is clearly better than whatever
    came second. A candidate that scores 40 while the runner-up scores 45 is a
    coin toss; one that scores 40 while the runner-up scores 400 is a result.

    This is a presentation heuristic, not a probability. It is calibrated so
    that clean English of a few hundred letters lands above 0.8 and gibberish
    lands near 0.
    """
    if best == float("inf"):
        return 0.0
    # Absolute component: chi-squared of ~30 or less is very English-like.
    absolute = 1.0 / (1.0 + max(best, 0.0) / 60.0)
    if runner_up is None or runner_up == float("inf") or best <= 0:
        return round(min(absolute, 1.0), 3)
    # Relative component: how much better than second place?
    margin = (runner_up - best) / max(runner_up, 1e-9)
    relative = max(0.0, min(margin * 1.5, 1.0))
    return round(min(0.5 * absolute + 0.5 * relative, 1.0), 3)


# --------------------------------------------------------------------------
# Bigram model: a second opinion that single-letter statistics cannot fake.
# --------------------------------------------------------------------------
#
# Why bother, when chi-squared already works? Because chi-squared only looks at
# letters one at a time, and the Vigenere attack *chooses* its shifts to make
# those single-letter counts look English. Given enough columns to tune, it can
# make garbage score beautifully -- the same way a tailor with enough pins can
# make any coat hang straight until the wearer moves.
#
# Letter *pairs* run across the columns, so no per-column shift can arrange them.
# TH, HE, IN and ER only appear in quantity if the text really is English. This
# gives the breaker an independent check on its own work, which is what stops it
# preferring a 20-letter key over the true 5-letter one.

_CORPUS_PATH = Path(__file__).resolve().parent.parent / "data" / "english_corpus.txt"
_BIGRAM_LOG_PROBS: dict[str, float] | None = None
_FLOOR_LOG_PROB: float = -6.0

ENGLISH_FITNESS = -2.30
"""Typical :func:`bigram_fitness` of real English.

Calibrated on prose held out of the corpus, not on the corpus itself -- scoring
the training text would flatter the model and inflate every confidence figure
the tool reports.
""" 

RANDOM_FITNESS = -3.25
"""Typical :func:`bigram_fitness` of uniformly random letters (measured)."""


def _load_bigram_model() -> dict[str, float]:
    """Build the log-probability table from the bundled corpus, once.

    Counts every adjacent letter pair in ``data/english_corpus.txt`` and applies
    Laplace (add-one) smoothing, so a pair that never occurred in the sample
    gets a small probability rather than zero -- without it, a single unusual
    pair like 'ZQ' would send the whole score to negative infinity.

    If the corpus file is missing the model degrades to a uniform table, which
    makes :func:`bigram_fitness` uninformative but keeps the tool running.
    """
    global _BIGRAM_LOG_PROBS, _FLOOR_LOG_PROB
    if _BIGRAM_LOG_PROBS is not None:
        return _BIGRAM_LOG_PROBS

    counts: Counter = Counter()
    try:
        raw = _CORPUS_PATH.read_text(encoding="utf-8")
        # Skip the provenance header; comment lines are not English prose.
        prose = "\n".join(
            line for line in raw.splitlines() if not line.startswith("#")
        )
        corpus = letters_only(prose)
    except OSError:
        logging.getLogger(__name__).warning(
            "English corpus not found at %s; bigram scoring disabled.", _CORPUS_PATH
        )
        corpus = ""
    for a, b in zip(corpus, corpus[1:]):
        counts[a + b] += 1

    total = sum(counts.values()) + ALPHABET_SIZE * ALPHABET_SIZE  # add-one smoothing
    model = {}
    for first in ALPHABET:
        for second in ALPHABET:
            pair = first + second
            model[pair] = math.log10((counts[pair] + 1) / total)
    _FLOOR_LOG_PROB = math.log10(1 / total)
    _BIGRAM_LOG_PROBS = model
    return model


def bigram_fitness(text: str) -> float:
    """Average log10 probability of ``text``'s letter pairs under English.

    **Higher is better**, and the value is always negative (probabilities are
    below 1, so their logarithms are below 0). Real English scores around
    ``-2.3``; random letters and Vigenere ciphertext score around ``-3.25``.

    Averaging per pair rather than summing keeps long and short texts on the
    same scale, so the number means the same thing everywhere.

    Texts with fewer than two letters return :data:`RANDOM_FITNESS`, i.e. "no
    evidence either way".

    Examples:
        >>> bigram_fitness("the theory of the thing") > bigram_fitness("qxzj vkwq")
        True
    """
    model = _load_bigram_model()
    letters = letters_only(text)
    if len(letters) < 2:
        return RANDOM_FITNESS
    total = sum(
        model.get(a + b, _FLOOR_LOG_PROB) for a, b in zip(letters, letters[1:])
    )
    return total / (len(letters) - 1)


def fitness_confidence(best: float, runner_up: float | None = None) -> float:
    """Turn bigram fitness scores into a 0-1 confidence figure.

    Same two ingredients as :func:`confidence`: how English the winner looks in
    absolute terms, and how far clear of the runner-up it is.
    """
    span = ENGLISH_FITNESS - RANDOM_FITNESS
    absolute = max(0.0, min((best - RANDOM_FITNESS) / span, 1.0))
    if runner_up is None:
        return round(absolute, 3)
    margin = max(0.0, min((best - runner_up) / (0.5 * span), 1.0))
    return round(min(0.6 * absolute + 0.4 * margin, 1.0), 3)


def histogram_rows(text: str, width: int = 40) -> list[tuple[str, float, float, str]]:
    """Build rows for a text histogram: (letter, observed %, English %, bar).

    Used by the CLI's statistics view. Kept here so the maths and the display
    data stay in one place, while the *rendering* stays in :mod:`utils.formatting`.
    """
    freqs = letter_frequencies(text)
    peak = max(max(freqs.values()), max(ENGLISH_FREQUENCIES.values()))
    rows = []
    for letter in ALPHABET:
        observed = freqs[letter]
        expected = ENGLISH_FREQUENCIES[letter]
        filled = 0 if peak == 0 else round(width * observed / peak)
        rows.append((letter, observed * 100, expected * 100, "#" * filled))
    return rows
