"""Tests for the interactive menu, driven by scripted keyboard input.

The menu is the part of the tool a first-time user actually meets, so it gets
the same test treatment as the maths: every path a confused user can take
(bad key, bad menu choice, Ctrl-D, quitting mid-prompt) must land somewhere
sensible rather than in a traceback.
"""

import pytest

from cli.interactive import run_interactive
from cipher import caesar, vigenere
from utils.config import Settings

LONG = ("we hold these truths to be self evident that all men are created equal "
        "that they are endowed by their creator with certain unalienable rights ") * 3
PLAIN = Settings(no_color=True, top_candidates=3)


def script(monkeypatch, answers):
    """Feed ``answers`` to input() in order; raise EOFError when exhausted."""
    queue = list(answers)

    def fake_input(prompt=""):
        if not queue:
            raise EOFError
        return queue.pop(0)

    monkeypatch.setattr("builtins.input", fake_input)


class TestMenuFlows:
    def test_encrypt_caesar(self, monkeypatch, capsys):
        script(monkeypatch, ["1", "Attack at dawn!", "3", "9"])
        assert run_interactive(PLAIN) == 0
        assert "Dwwdfn dw gdzq!" in capsys.readouterr().out

    def test_decrypt_caesar(self, monkeypatch, capsys):
        script(monkeypatch, ["2", "Dwwdfn dw gdzq!", "3", "9"])
        run_interactive(PLAIN)
        assert "Attack at dawn!" in capsys.readouterr().out

    def test_encrypt_and_decrypt_vigenere(self, monkeypatch, capsys):
        script(monkeypatch, ["4", "Attack at dawn!", "LEMON", "5", "Lxfopv ef rnhr!", "LEMON", "9"])
        run_interactive(PLAIN)
        out = capsys.readouterr().out
        assert "Lxfopv ef rnhr!" in out and "Attack at dawn!" in out

    def test_break_caesar_flow(self, monkeypatch, capsys):
        script(monkeypatch, ["3", caesar.encrypt(LONG, 11), "", "9"])
        run_interactive(PLAIN)
        assert "Key = 11" in capsys.readouterr().out

    def test_break_vigenere_flow(self, monkeypatch, capsys):
        script(monkeypatch, ["6", vigenere.encrypt(LONG, "LEMON"), "", "9"])
        run_interactive(PLAIN)
        assert "LEMON" in capsys.readouterr().out

    def test_compare_and_help(self, monkeypatch, capsys):
        script(monkeypatch, ["7", "8", "9"])
        run_interactive(PLAIN)
        out = capsys.readouterr().out
        assert "AES-256" in out and "plaintext" in out

    def test_statistics_shortcut(self, monkeypatch, capsys):
        script(monkeypatch, ["s", LONG, "9"])
        run_interactive(PLAIN)
        assert "Index of coincidence" in capsys.readouterr().out


class TestResilience:
    def test_invalid_menu_choice_reprompts(self, monkeypatch, capsys):
        script(monkeypatch, ["42", "9"])
        run_interactive(PLAIN)
        assert "not on the menu" in capsys.readouterr().out

    def test_bad_caesar_key_reprompts_without_losing_text(self, monkeypatch, capsys):
        script(monkeypatch, ["1", "hello", "banana", "3", "9"])
        run_interactive(PLAIN)
        out = capsys.readouterr().out
        assert "whole number" in out
        assert "khoor" in out  # the text survived the bad key

    def test_bad_vigenere_key_reprompts(self, monkeypatch, capsys):
        script(monkeypatch, ["4", "hello", "12345", "KEY", "9"])
        run_interactive(PLAIN)
        assert "only letters" in capsys.readouterr().out

    def test_empty_text_reprompts(self, monkeypatch, capsys):
        script(monkeypatch, ["1", "", "hi", "1", "9"])
        run_interactive(PLAIN)
        assert "Please enter some text" in capsys.readouterr().out

    def test_quit_word_exits_cleanly(self, monkeypatch, capsys):
        script(monkeypatch, ["1", "q"])
        assert run_interactive(PLAIN) == 0
        assert "Goodbye" in capsys.readouterr().out

    def test_eof_exits_cleanly(self, monkeypatch, capsys):
        script(monkeypatch, [])
        assert run_interactive(PLAIN) == 0
        assert "Goodbye" in capsys.readouterr().out


class TestFileAndExport:
    def test_file_prefix_reads_text(self, monkeypatch, capsys, tmp_path):
        path = tmp_path / "msg.txt"
        path.write_text("Attack at dawn!", encoding="utf-8")
        script(monkeypatch, ["1", f"file:{path}", "3", "9"])
        run_interactive(PLAIN)
        assert "Dwwdfn dw gdzq!" in capsys.readouterr().out

    def test_missing_file_reprompts(self, monkeypatch, capsys):
        script(monkeypatch, ["1", "file:/nope/x.txt", "hi", "1", "9"])
        run_interactive(PLAIN)
        assert "Could not read" in capsys.readouterr().out

    def test_export_after_break(self, monkeypatch, capsys, tmp_path):
        out = tmp_path / "r.json"
        script(monkeypatch, ["3", caesar.encrypt(LONG, 4), str(out), "9"])
        run_interactive(PLAIN)
        assert out.exists() and "recovered_key" in out.read_text()

    def test_bad_export_path_is_reported(self, monkeypatch, capsys, tmp_path):
        script(monkeypatch, ["3", caesar.encrypt(LONG, 4), str(tmp_path / "r.pdf"), "9"])
        run_interactive(PLAIN)
        assert "unsupported export format" in capsys.readouterr().out
