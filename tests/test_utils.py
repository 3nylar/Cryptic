"""Tests for alphabet maths, config loading, export and formatting."""

import json

import pytest

from utils import alphabet
from utils.config import Settings
from utils.export import ExportError, export_result
from utils.formatting import Formatter, _wrap


class TestAlphabet:
    @pytest.mark.parametrize("char,index", [("A", 0), ("a", 0), ("Z", 25), ("m", 12)])
    def test_char_to_index(self, char, index):
        assert alphabet.char_to_index(char) == index

    def test_char_to_index_rejects_non_letters(self):
        with pytest.raises(ValueError):
            alphabet.char_to_index("!")

    @pytest.mark.parametrize("index,char", [(0, "A"), (26, "A"), (-1, "Z"), (27, "B")])
    def test_index_to_char_wraps(self, index, char):
        assert alphabet.index_to_char(index) == char

    def test_letters_only(self):
        assert alphabet.letters_only("Hi, Bob! 42") == "HIBOB"

    def test_fold_unicode(self):
        assert alphabet.fold_unicode("caf\u00e9 na\u00efve") == "cafe naive"

    def test_preserve_case(self):
        assert alphabet.preserve_case("A", "b") == "B"
        assert alphabet.preserve_case("a", "B") == "b"


class TestSettings:
    def test_defaults(self):
        assert Settings().max_key_length == 20

    def test_load_from_file(self, tmp_path):
        path = tmp_path / "c.json"
        path.write_text(json.dumps({"max_key_length": 7, "top_candidates": 2}))
        settings = Settings.load(path)
        assert settings.max_key_length == 7 and settings.top_candidates == 2

    def test_missing_file_falls_back_to_defaults(self, tmp_path):
        assert Settings.load(tmp_path / "nope.json").max_key_length == 20

    def test_malformed_file_does_not_crash(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{not json")
        assert Settings.load(path).max_key_length == 20

    def test_unknown_keys_ignored(self, tmp_path):
        path = tmp_path / "c.json"
        path.write_text(json.dumps({"future_option": True}))
        assert Settings.load(path).max_key_length == 20


class TestExport:
    def test_rejects_unknown_extension(self, tmp_path):
        from analysis.caesar_breaker import break_caesar
        with pytest.raises(ExportError):
            export_result(break_caesar("abc"), tmp_path / "r.docx")

    def test_creates_missing_directories(self, tmp_path):
        from analysis.caesar_breaker import break_caesar
        target = tmp_path / "nested" / "deep" / "r.json"
        assert export_result(break_caesar("abc"), target).exists()


class TestFormatting:
    def test_confidence_bar_is_readable_without_colour(self):
        bar = Formatter(plain=True).confidence_bar(0.5, width=10)
        assert bar == "[#####-----] 50%"

    def test_plain_mode_emits_no_escape_codes(self, capsys):
        fmt = Formatter(plain=True)
        fmt.success("hello")
        assert "\033[" not in capsys.readouterr().out

    def test_wrap_respects_width(self):
        wrapped = _wrap("word " * 40, width=30)
        assert all(len(line) <= 31 for line in wrapped.split("\n"))
