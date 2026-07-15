"""CLI and end-to-end tests: argument parsing, exit codes, stdout hygiene."""

import json

import pytest

from cli.args import build_parser, run, EXIT_OK, EXIT_USER_ERROR
from cipher import caesar, vigenere

LONG = (
    "we hold these truths to be self evident that all men are created equal "
    "that they are endowed by their creator with certain unalienable rights "
) * 3


class TestParser:
    def test_subcommands_registered(self):
        parser = build_parser()
        for command in [
            "caesar-encrypt", "caesar-decrypt", "caesar-break",
            "vigenere-encrypt", "vigenere-decrypt", "vigenere-break",
            "stats", "compare", "interactive",
        ]:
            args = ["-t", "x"] if command in ("caesar-break", "vigenere-break", "stats") else []
            if command.endswith(("encrypt", "decrypt")):
                args = ["-t", "x", "-k", "3"]
            assert parser.parse_args([command] + args)

    def test_text_and_file_are_mutually_exclusive(self):
        with pytest.raises(SystemExit):
            build_parser().parse_args(["caesar-break", "-t", "a", "-f", "b.txt"])

    def test_missing_key_is_usage_error(self):
        with pytest.raises(SystemExit) as exc:
            build_parser().parse_args(["caesar-encrypt", "-t", "hi"])
        assert exc.value.code == 2


class TestCommands:
    def test_caesar_encrypt_prints_only_ciphertext(self, capsys):
        assert run(["caesar-encrypt", "-t", "Attack at dawn!", "-k", "3", "--no-color"]) == EXIT_OK
        assert capsys.readouterr().out.strip() == "Dwwdfn dw gdzq!"

    def test_caesar_decrypt(self, capsys):
        run(["caesar-decrypt", "-t", "Dwwdfn dw gdzq!", "-k", "3", "--no-color"])
        assert capsys.readouterr().out.strip() == "Attack at dawn!"

    def test_vigenere_round_trip_through_cli(self, capsys):
        run(["vigenere-encrypt", "-t", "Attack at dawn!", "-k", "LEMON", "--no-color"])
        ciphertext = capsys.readouterr().out.strip()
        assert ciphertext == "Lxfopv ef rnhr!"
        run(["vigenere-decrypt", "-t", ciphertext, "-k", "LEMON", "--no-color"])
        assert capsys.readouterr().out.strip() == "Attack at dawn!"

    def test_caesar_break_reports_key(self, capsys):
        code = run(["caesar-break", "-t", caesar.encrypt(LONG, 11), "--no-color"])
        out = capsys.readouterr().out
        assert code == EXIT_OK
        assert "Key = 11" in out
        assert LONG.split()[0] in out

    def test_vigenere_break_reports_key(self, capsys):
        code = run(["vigenere-break", "-t", vigenere.encrypt(LONG, "LEMON"), "--no-color"])
        assert code == EXIT_OK
        assert "LEMON" in capsys.readouterr().out

    def test_stats_shows_ioc(self, capsys):
        run(["stats", "-t", LONG, "--no-color"])
        assert "Index of coincidence" in capsys.readouterr().out

    def test_compare_needs_no_input(self, capsys):
        assert run(["compare", "--no-color"]) == EXIT_OK
        assert "AES-256" in capsys.readouterr().out


class TestErrorHandling:
    def test_bad_caesar_key_is_user_error(self, capsys):
        assert run(["caesar-encrypt", "-t", "hi", "-k", "abc", "--no-color"]) == EXIT_USER_ERROR
        assert "whole number" in capsys.readouterr().out

    def test_bad_vigenere_key_is_user_error(self, capsys):
        assert run(["vigenere-encrypt", "-t", "hi", "-k", "12345", "--no-color"]) == EXIT_USER_ERROR

    def test_missing_file_is_user_error(self, capsys):
        assert run(["caesar-break", "-f", "/nonexistent/x.txt", "--no-color"]) == EXIT_USER_ERROR
        assert "could not read" in capsys.readouterr().out.lower()


class TestFileAndExport:
    def test_reads_from_file(self, tmp_path, capsys):
        path = tmp_path / "secret.txt"
        path.write_text(caesar.encrypt(LONG, 5), encoding="utf-8")
        run(["caesar-break", "-f", str(path), "--no-color"])
        assert "Key = 5" in capsys.readouterr().out

    def test_export_json(self, tmp_path, capsys):
        out = tmp_path / "report.json"
        run(["caesar-break", "-t", caesar.encrypt(LONG, 5), "--export", str(out), "--no-color"])
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["recovered_key"] == 5
        assert data["cipher"] == "caesar"

    def test_export_markdown(self, tmp_path):
        out = tmp_path / "report.md"
        run(["vigenere-break", "-t", vigenere.encrypt(LONG, "LEMON"), "--export", str(out), "--no-color"])
        text = out.read_text(encoding="utf-8")
        assert "# Cryptanalysis report" in text and "LEMON" in text

    def test_unsupported_export_format(self, tmp_path, capsys):
        run(["caesar-break", "-t", caesar.encrypt(LONG, 5), "--export", str(tmp_path / "r.pdf"), "--no-color"])
        assert "unsupported export format" in capsys.readouterr().out
