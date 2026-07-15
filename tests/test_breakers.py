"""Unit and integration tests for the two cryptanalysis engines."""

import pytest

from analysis import caesar_breaker, vigenere_breaker
from cipher import caesar, vigenere

SHORT = "the quick brown fox jumps over the lazy dog"
MEDIUM = (
    "we hold these truths to be self evident that all men are created equal "
    "that they are endowed by their creator with certain unalienable rights "
    "that among these are life liberty and the pursuit of happiness"
)
LONG = MEDIUM * 3


class TestCaesarBreaker:
    @pytest.mark.parametrize("shift", range(26))
    def test_recovers_every_shift(self, shift):
        result = caesar_breaker.break_caesar(caesar.encrypt(MEDIUM, shift))
        assert result.key == caesar.validate_shift(shift)
        assert result.plaintext == MEDIUM

    def test_recovers_from_short_text(self):
        result = caesar_breaker.break_caesar(caesar.encrypt(SHORT, 7))
        assert result.key == 7

    def test_confidence_is_high_for_real_english(self):
        result = caesar_breaker.break_caesar(caesar.encrypt(LONG, 4))
        assert result.confidence > 0.5

    def test_returns_full_keyspace_ranked(self):
        result = caesar_breaker.break_caesar(caesar.encrypt(MEDIUM, 4))
        assert len(result.candidates) == 26
        scores = [c.score for c in result.candidates]
        assert scores == sorted(scores)

    def test_punctuation_and_case_preserved_in_output(self):
        original = "Attack at Dawn, bring 3 ladders!"
        result = caesar_breaker.break_caesar(caesar.encrypt(original, 9))
        assert result.plaintext == original

    def test_no_letters_gives_zero_confidence_not_crash(self):
        result = caesar_breaker.break_caesar("12345 !!!")
        assert result.confidence == 0.0

    def test_empty_string(self):
        assert caesar_breaker.break_caesar("").confidence == 0.0

    def test_steps_are_explained(self):
        result = caesar_breaker.break_caesar(caesar.encrypt(MEDIUM, 3))
        assert len(result.steps) >= 4
        assert any("chi-squared" in s.lower() for s in result.steps)

    def test_to_dict_is_serialisable(self):
        import json
        result = caesar_breaker.break_caesar(caesar.encrypt(MEDIUM, 3))
        assert json.loads(json.dumps(result.to_dict()))["recovered_key"] == 3


class TestKasiski:
    def test_finds_key_length_multiples(self):
        ct = vigenere.encrypt("the sun and the man in the moon " * 8, "KEY")
        votes = vigenere_breaker.kasiski_examination(ct)
        assert votes
        assert max(votes, key=votes.get) % 3 == 0

    def test_no_repeats_returns_empty(self):
        assert vigenere_breaker.kasiski_examination("abcdef") == {}


class TestIoCKeyLength:
    def test_true_length_scores_near_english(self):
        ct = vigenere.encrypt(LONG, "LEMON")
        table = dict(vigenere_breaker.ioc_key_lengths(ct, max_key_length=10))
        assert table[5] > table[3]
        assert table[5] > 0.055

    def test_estimation_ranks_true_length_first(self):
        guesses = vigenere_breaker.estimate_key_length(vigenere.encrypt(LONG, "LEMON"))
        assert guesses[0].length == 5


class TestVigenereBreaker:
    @pytest.mark.parametrize("key", ["LEMON", "KEY", "CRYPTO", "AB"])
    def test_recovers_key_from_long_text(self, key):
        result = vigenere_breaker.break_vigenere(vigenere.encrypt(LONG, key))
        assert result.key == key
        assert result.plaintext == LONG

    def test_recovers_plaintext_with_punctuation(self):
        original = "Meet me by the old oak tree at midnight; bring two lanterns! " * 6
        result = vigenere_breaker.break_vigenere(vigenere.encrypt(original, "LEMON"))
        assert result.plaintext == original

    def test_known_key_length_shortcut(self):
        ct = vigenere.encrypt(MEDIUM, "LEMON")
        result = vigenere_breaker.break_vigenere(ct, known_key_length=5)
        assert result.key == "LEMON"

    def test_recover_key_rejects_zero_length(self):
        with pytest.raises(ValueError):
            vigenere_breaker.recover_key("abc", 0)

    def test_short_text_warns_instead_of_lying(self):
        result = vigenere_breaker.break_vigenere(vigenere.encrypt("hello there", "LEMON"))
        assert result.warnings
        assert result.confidence <= 0.45

    def test_two_letter_text_does_not_crash(self):
        result = vigenere_breaker.break_vigenere("a")
        assert result.confidence == 0.0
        assert result.warnings

    def test_single_letter_key_is_found(self):
        result = vigenere_breaker.break_vigenere(vigenere.encrypt(LONG, "D"))
        assert result.plaintext == LONG

    def test_steps_and_dict(self):
        import json
        result = vigenere_breaker.break_vigenere(vigenere.encrypt(LONG, "LEMON"))
        assert any("coincidence" in s.lower() for s in result.steps)
        assert json.loads(json.dumps(result.to_dict()))["recovered_key"] == "LEMON"


class TestRegression:
    """Cases that previously broke, kept forever so they cannot break again."""

    def test_key_length_not_confused_by_multiples(self):
        # A 4-letter key must not be reported as 8 or 12.
        result = vigenere_breaker.break_vigenere(vigenere.encrypt(LONG, "MOON"))
        assert result.key == "MOON"

    def test_repeated_key_letters(self):
        result = vigenere_breaker.break_vigenere(vigenere.encrypt(LONG, "AAAB"))
        assert result.plaintext == LONG

    def test_caesar_break_survives_unicode(self):
        ct = caesar.encrypt("caf\u00e9 society meets at dawn " * 8, 5)
        assert caesar_breaker.break_caesar(ct).key == 5
