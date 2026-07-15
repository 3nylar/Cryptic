"""Unit tests for the Vigenere cipher."""

import pytest

from cipher import vigenere
from cipher.vigenere import VigenereKeyError


class TestEncrypt:
    def test_known_vector(self):
        # The textbook example: ATTACKATDAWN + LEMON -> LXFOPVEFRNHR
        assert vigenere.encrypt("ATTACKATDAWN", "LEMON") == "LXFOPVEFRNHR"

    def test_preserves_case_and_punctuation(self):
        assert vigenere.encrypt("Attack at dawn!", "LEMON") == "Lxfopv ef rnhr!"

    def test_punctuation_does_not_advance_key(self):
        # Same letters, different spacing -> same letters out.
        a = vigenere.encrypt("ATTACK", "KEY")
        b = vigenere.encrypt("A-T T,A C K", "KEY")
        assert "".join(c for c in b if c.isalpha()) == a

    def test_single_letter_key_is_caesar(self):
        from cipher import caesar
        assert vigenere.encrypt("hello world", "D") == caesar.encrypt("hello world", 3)

    def test_key_longer_than_text(self):
        assert vigenere.decrypt(vigenere.encrypt("hi", "ENORMOUSKEY"), "ENORMOUSKEY") == "hi"

    def test_empty_text(self):
        assert vigenere.encrypt("", "KEY") == ""

    def test_unicode_passthrough(self):
        assert vigenere.decrypt(vigenere.encrypt("caf\u00e9 \u4f60\u597d", "KEY"), "KEY") == "caf\u00e9 \u4f60\u597d"

    def test_very_long_text(self):
        text = "attack at dawn " * 5000
        assert vigenere.decrypt(vigenere.encrypt(text, "LEMON"), "LEMON") == text


class TestKeys:
    def test_case_insensitive(self):
        assert vigenere.encrypt("hello", "lemon") == vigenere.encrypt("hello", "LEMON")

    @pytest.mark.parametrize("bad", ["", "   ", "key1", "two words", "!", 5, None])
    def test_invalid_keys_rejected(self, bad):
        with pytest.raises(VigenereKeyError):
            vigenere.validate_key(bad)

    def test_key_schedule(self):
        assert vigenere.key_schedule("LEMON", 7) == [11, 4, 12, 14, 13, 11, 4]

    def test_effective_key_length(self):
        assert vigenere.effective_key_length("ENORMOUSKEY", "hi!") == 2


class TestRoundTrip:
    @pytest.mark.parametrize("key", ["A", "AB", "LEMON", "cryptography", "ZZZZ"])
    def test_round_trip(self, key):
        text = "Meet me by the old oak tree at midnight, bring 2 lanterns!"
        assert vigenere.decrypt(vigenere.encrypt(text, key), key) == text
