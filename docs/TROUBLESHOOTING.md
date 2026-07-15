# Troubleshooting

Errors are listed by what you actually see on screen.

---

## It won't start

### `'python' is not recognized` / `command not found: python`

Python isn't installed, or isn't on your PATH. Try `python3`, then `py -3`. If none work, reinstall from [python.org](https://www.python.org/downloads/) and **tick "Add Python to PATH"** on the installer's first screen. That checkbox is the cause of this error roughly always.

### `SyntaxError` on startup, or something about f-strings

You are running Python 2, or a very old 3.x. Check with `python --version`; you need **3.9+**. Use `python3 main.py`.

### `ModuleNotFoundError: No module named 'cipher'`

You are running from the wrong directory. `main.py` adds its own folder to the path, so:

```bash
cd /path/to/cryptic
python main.py                  # works
python /path/to/cryptic/main.py    # also works
```

But `python cryptic/main.py` from a parent directory with a _different_ `cipher` package installed can confuse imports. `cd` into the project.

### `ModuleNotFoundError: No module named 'rich'`

This should never happen — `rich` is optional and the import is guarded. If you see it, something is importing `rich` outside the guard, which is a bug: please open an issue with the traceback.

---

## It runs, but the output looks wrong

### Output is full of `←[1;32m` or `\033[1;36m`

Your terminal doesn't understand colour codes (usually old `cmd.exe`).

```bash
python main.py caesar-break -t "..." --no-color
```

Or set `NO_COLOR=1` in your environment to make it permanent, or use PowerShell / Windows Terminal.

### Tables are misaligned or wrapped

The terminal is narrower than ~80 columns. Widen it, or reduce the candidate count in `config.json` (`"top_candidates": 3`).

### Redirecting to a file gives me the tables too

It shouldn't — plaintext goes to stdout, everything else to stderr:

```bash
python main.py caesar-break -f secret.txt > plaintext.txt      # clean
python main.py caesar-break -f secret.txt > out.txt 2>&1       # includes tables
```

If you want the analysis in a file, use `--export report.md` instead.

---

## It gives me the wrong answer

### "It found the wrong key"

Almost always **not enough ciphertext.** These attacks are statistical; statistics need data.

| Cipher   | Comfortable                                                              | Marginal         | Hopeless        |
| -------- | ------------------------------------------------------------------------ | ---------------- | --------------- |
| Caesar   | 40+ letters                                                              | 20–40            | < 20            |
| Vigenère | 20+ letters **per key letter** (so 100+ for a 5-letter key, 240+ for 12) | 10–20 per letter | < 10 per letter |

Check the confidence figure. Below ~50% the tool is telling you it's guessing, and it will have said so in a warning. Feed it more text.

### "Confidence is low even though the plaintext looks right"

Confidence measures two things: how English the result looks, _and_ how far ahead it is of the runner-up. A short message can be correct and still score low, because there wasn't enough evidence to rule out the alternatives. The tool is being honest about what it knows, not about what happens to be true.

### "It found a 10-letter key but the real one is 5 letters"

Report it — this should be fixed. The breaker reduces keys to their minimal period (`LEMONLEMON` → `LEMON`) and prefers the shortest key among near-equal candidates. If you have a case that defeats that, it's a genuinely interesting bug: please open an issue with the ciphertext.

Meanwhile, force it:

```bash
python main.py vigenere-break -f secret.txt --key-length 5
```

### "The text isn't English"

Then this tool cannot break it. Every constant here — letter frequencies, the IC target of 0.067, the bigram corpus — is English. The _methods_ are universal, but the _numbers_ are not. Supporting another language means swapping the frequency table and the corpus; see PLANNING.md §16.

### "My message has no spaces and it still worked"

Expected. Word matching is a bonus signal only; chi-squared and the bigram model work fine on unbroken blocks of letters.

---

## Errors from commands

### `[X] no input: use --text, --file, or pipe text on stdin`

You ran a command that needs text without giving it any.

```bash
python main.py caesar-break -t "Dwwdfn"
python main.py caesar-break -f secret.txt
cat secret.txt | python main.py caesar-break
```

### `[X] shift must be a whole number (got 'banana')`

Caesar keys are numbers 0–25. Negative and large values are fine (`-1` = 25, `29` = 3); words are not.

### `[X] key must contain only letters A-Z (got 'lemon5')`

Vigenère keys are words. This is rejected rather than silently cleaned to `LEMON` on purpose: if the tool quietly changed your key, encrypting and decrypting could use different keys and you'd never know why the result was garbage.

### `[X] unsupported export format '.pdf'`

Use `.json`, `.md` or `.txt`. For PDF, export Markdown and convert with pandoc.

### `[X] could not read /path/file.txt`

Check the path and permissions. In the interactive menu, use `file:/full/path/to/file.txt`.

---

## Performance

### "It's slow on a big file"

Roughly linear: ~2 s to break 50k letters, ~5 s for 100k. Anything much worse suggests a very long `--max-key-length`; the work grows with it. Try `--max-key-length 12`.

### "It used a lot of memory on a huge file"

The whole text is held in memory, several times over during candidate generation. A 100 MB file is not a good idea. Split it, or take a 10k-letter sample — the attack needs statistics, not the whole book.

---

## Tests

### `pytest: command not found`

```bash
pip install -r requirements-dev.txt
python -m pytest tests -q       # `python -m` avoids PATH problems entirely
```

### Tests fail on a fresh clone

That's a bug, not your fault. Please open an issue with the failing test name and `python --version`.

---

## Still stuck?

Open an issue with: the command you ran, the full output, `python --version`, and your OS. If it involves a ciphertext that misbehaves, include it — those are the most valuable bug reports this project can get.
