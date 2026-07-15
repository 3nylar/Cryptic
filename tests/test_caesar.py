"""Unit tests for the Caesar cipher."""

import pytest

from cipher import caesar
from cipher.caesar import CaesarKeyError


class TestEncrypt:
    def test_known_vector(self):
        assert caesar.encrypt("Attack at dawn!", 3) == "Dwwdfn dw gdzq!"

    def test_wraps_past_z(self):
        assert caesar.encrypt("xyz", 3) == "abc"

    def test_preserves_case(self):
        assert caesar.encrypt("AbC", 1) == "BcD"

    def test_non_letters_untouched(self):
        assert caesar.encrypt("a1! b", 1) == "b1! c"

    def test_zero_shift_is_identity(self):
        assert caesar.encrypt("Hello, World", 0) == "Hello, World"

    def test_empty_string(self):
        assert caesar.encrypt("", 5) == ""

    def test_whitespace_only(self):
        assert caesar.encrypt("  \t\n ", 5) == "  \t\n "

    def test_unicode_passthrough(self):
        # Non-ASCII letters are not in the 26-letter alphabet, so they survive.
        assert caesar.encrypt("café \u4f60\u597d \U0001f600", 1) == "dbgé \u4f60\u597d \U0001f600"

    def test_very_long_text(self):
        text = "the quick brown fox " * 5000
        assert caesar.decrypt(caesar.encrypt(text, 11), 11) == text


class TestKeys:
    @pytest.mark.parametrize("given,expected", [(3, 3), (29, 3), (-1, 25), (0, 0), (26, 0), (-27, 25)])
    def test_normalisation(self, given, expected):
        assert caesar.validate_shift(given) == expected

    def test_string_keys_accepted(self):
        assert caesar.validate_shift("  7 ") == 7

    @pytest.mark.parametrize("bad", ["abc", "3.5", "", None, 2.5, True])
    def test_invalid_keys_rejected(self, bad):
        with pytest.raises(CaesarKeyError):
            caesar.validate_shift(bad)

    def test_large_and_negative_shifts_agree(self):
        assert caesar.encrypt("hello", -1) == caesar.encrypt("hello", 25)


class TestRoundTrip:
    @pytest.mark.parametrize("shift", range(26))
    def test_all_shifts_round_trip(self, shift):
        text = "The Quick Brown Fox, 42 times!"
        assert caesar.decrypt(caesar.encrypt(text, shift), shift) == text


def test_brute_force_covers_keyspace():
    results = caesar.brute_force("Dwwdfn")
    assert len(results) == 26
    assert (3, "Attack") in results
