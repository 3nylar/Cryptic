"""Unit tests for the frequency-analysis toolkit."""

import math

import pytest

from analysis import frequency
from cipher import caesar, vigenere

ENGLISH = (
    "it is a truth universally acknowledged that a single man in possession "
    "of a good fortune must be in want of a wife however little known the "
    "feelings or views of such a man may be on his first entering a "
    "neighbourhood this truth is so well fixed in the minds of the "
    "surrounding families that he is considered the rightful property of "
    "some one or other of their daughters"
)


def test_english_frequencies_sum_to_one():
    assert math.isclose(sum(frequency.ENGLISH_FREQUENCIES.values()), 1.0, abs_tol=0.01)


class TestCounts:
    def test_all_letters_present(self):
        assert len(frequency.letter_counts("abc")) == 26
        assert frequency.letter_counts("abc")["Z"] == 0

    def test_case_and_symbols_ignored(self):
        assert frequency.letter_counts("A a! 1 A")["A"] == 3

    def test_frequencies_sum_to_one(self):
        assert math.isclose(sum(frequency.letter_frequencies(ENGLISH).values()), 1.0)

    def test_empty_text_frequencies_are_zero(self):
        assert set(frequency.letter_frequencies("").values()) == {0.0}


class TestChiSquared:
    def test_english_scores_better_than_gibberish(self):
        assert frequency.chi_squared(ENGLISH) < frequency.chi_squared("zzzz qqqq xxxx jjjj")

    def test_shifted_english_scores_worse(self):
        assert frequency.chi_squared(ENGLISH) < frequency.chi_squared(caesar.encrypt(ENGLISH, 7))

    def test_no_letters_is_infinite(self):
        assert frequency.chi_squared("12345 !!!") == float("inf")


class TestIndexOfCoincidence:
    def test_english_near_expected(self):
        assert 0.055 < frequency.index_of_coincidence(ENGLISH) < 0.080

    def test_invariant_under_caesar_shift(self):
        # The key property that makes IC useful: shifting does not change it.
        plain = frequency.index_of_coincidence(ENGLISH)
        shifted = frequency.index_of_coincidence(caesar.encrypt(ENGLISH, 13))
        assert math.isclose(plain, shifted, abs_tol=1e-12)

    def test_vigenere_flattens_it(self):
        long_text = ENGLISH * 4
        assert frequency.index_of_coincidence(
            vigenere.encrypt(long_text, "CRYPTOGRAPHY")
        ) < frequency.index_of_coincidence(long_text)

    def test_short_text_returns_zero(self):
        assert frequency.index_of_coincidence("a") == 0.0


class TestScoring:
    def test_word_hit_rate(self):
        assert frequency.word_hit_rate("the and of xyzzy") == pytest.approx(0.75)
        assert frequency.word_hit_rate("!!!") == 0.0

    def test_english_score_prefers_real_words(self):
        assert frequency.english_score(ENGLISH) < frequency.chi_squared(ENGLISH)

    def test_confidence_bounds(self):
        assert frequency.confidence(float("inf")) == 0.0
        assert 0.0 <= frequency.confidence(20.0, 400.0) <= 1.0
        assert frequency.confidence(20.0, 400.0) > frequency.confidence(20.0, 21.0)


def test_histogram_rows_shape():
    rows = frequency.histogram_rows(ENGLISH)
    assert len(rows) == 26
    assert rows[0][0] == "A"


class TestBigramModel:
    def test_english_beats_random(self):
        assert frequency.bigram_fitness(ENGLISH) > frequency.bigram_fitness("qxzj vkwq ppfz")

    def test_calibration_constants_are_realistic(self):
        # Held-out English (not in the corpus) should land near ENGLISH_FITNESS.
        assert frequency.bigram_fitness(ENGLISH) > frequency.RANDOM_FITNESS + 0.5

    def test_ciphertext_looks_random(self):
        ct = vigenere.encrypt(ENGLISH * 3, "CRYPTOGRAPHY")
        assert frequency.bigram_fitness(ct) < frequency.ENGLISH_FITNESS

    def test_scale_is_length_independent(self):
        short, long = frequency.bigram_fitness(ENGLISH), frequency.bigram_fitness(ENGLISH * 10)
        assert abs(short - long) < 0.05

    def test_too_short_returns_no_evidence(self):
        assert frequency.bigram_fitness("a") == frequency.RANDOM_FITNESS

    def test_fitness_confidence_bounds(self):
        assert frequency.fitness_confidence(frequency.RANDOM_FITNESS - 1) == 0.0
        assert frequency.fitness_confidence(frequency.ENGLISH_FITNESS) == 1.0
        assert 0.0 <= frequency.fitness_confidence(-2.4, -3.2) <= 1.0

    def test_cannot_be_faked_by_letter_counts(self):
        # THE POINT: text with English-ish letter counts but scrambled order
        # must score worse than real English.
        import random
        letters = list(frequency.__dict__ and "".join(ENGLISH.split()))
        random.Random(0).shuffle(letters)
        assert frequency.bigram_fitness("".join(letters)) < frequency.bigram_fitness(ENGLISH)
