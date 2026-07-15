# Installation Guide

**Short version:** clone it and run `python main.py`. There is nothing to install.

```bash
git clone https://github.com/yourname/cipher-breaker.git
cd cipher-breaker
python main.py
```

If the menu appears, you are done. The rest of this page is for when it doesn't.

---

## Requirements

| | Needed | Notes |
|---|---|---|
| **Python** | 3.9 or newer | 3.9 is from 2020; anything current works |
| **Dependencies** | **none** | `rich` is optional and adds colour only |
| **OS** | any | Linux, macOS, Windows, WSL, Raspberry Pi |
| **Disk** | ~1 MB | |

### Check your Python

```bash
python --version        # or python3 --version
```

If it says 2.7 or "command not found", try `python3`. On Windows, try `py -3`. If nothing works, install from [python.org](https://www.python.org/downloads/) and tick **"Add Python to PATH"** on the first screen of the installer — skipping that box is the single most common cause of `'python' is not recognized`.

Throughout these docs, `python` means whichever of `python`, `python3` or `py -3` works on your machine.

---

## Optional: nicer output

```bash
pip install rich
```

This gets you colour, drawn tables and a spinner. **Everything works identically without it** — the tool detects the absence and prints plain ASCII with the same information. That is deliberate: locked-down lab machines and lecture-theatre lecterns rarely have pip access, and a demo that dies on a missing package is a demo that dies in front of an audience.

Or:

```bash
pip install -r requirements.txt
```

---

## Optional: install as a command

```bash
pip install -e .
cipher-breaker --help          # now available from anywhere
```

`-e` (editable) means your edits take effect immediately, without reinstalling.

---

## For development

```bash
pip install -r requirements-dev.txt   # rich + pytest + pytest-cov
python -m pytest tests -q             # 204 tests, ~7 seconds
```

### Virtual environment (recommended)

Keeps this project's packages away from everything else on your machine.

```bash
python -m venv .venv

source .venv/bin/activate      # macOS / Linux
.venv\Scripts\activate         # Windows

pip install -r requirements-dev.txt
deactivate                     # when you're done
```

---

## Verify

```bash
python main.py caesar-break -t "Dwwdfn dw gdzq"
```

Expect `Attack at dawn` and `Key = 3`. If you get that, everything works.

Fuller check:

```bash
python -m pytest tests -q          # should end: 204 passed
python main.py --version
python benchmark.py --sizes 1000   # should take about a second
```

---

## Platform notes

**Windows.** Use PowerShell or Terminal rather than `cmd.exe` — colour support in `cmd` is unreliable. If output looks like `←[1;32m`, run with `--no-color` or use a modern terminal.

**macOS.** The system Python may be old; `brew install python` gives you a current one.

**Linux.** Some distributions ship Python without `pip` or `venv`: `sudo apt install python3-pip python3-venv`. If pip refuses to install anything system-wide ("externally managed environment"), use a virtual environment — that message is the OS protecting itself, and it is right.

**No internet / air-gapped.** Everything works. Skip the `rich` step entirely; that is what the fallback is for.

---

## Uninstall

Delete the folder. If you ran `pip install -e .`, also run `pip uninstall cipher-breaker`.

---

Still stuck? [TROUBLESHOOTING.md](TROUBLESHOOTING.md) covers the specific error messages.
