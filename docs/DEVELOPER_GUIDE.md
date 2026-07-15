# Developer Guide

For anyone extending, porting or grading this project.

**Contents:** [Setup](#setup) · [Architecture](#architecture) · [The rules](#the-rules) · [Adding a cipher](#adding-a-cipher) · [Adding an attack](#adding-an-attack) · [Testing](#testing) · [Style](#style) · [Traps](#traps-for-the-unwary)

---

## Setup

```bash
git clone https://github.com/yourname/cipher-breaker.git
cd cipher-breaker
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

python -m pytest tests -q                                  # 204 tests, ~7s
python -m pytest --doctest-modules cipher analysis utils   # 14 doctests
python -m pytest tests --cov=cipher --cov=analysis --cov=utils --cov=cli
```

---

## Architecture

Four layers. **Dependencies point downward, always.**

```
cli/        interactive.py, args.py        ← the ONLY layer that prints
   ↓
analysis/   caesar_breaker, vigenere_breaker, frequency
   ↓
cipher/     caesar, vigenere
   ↓
utils/      alphabet, formatting, config, export
```

| Layer | Owns | Never |
|---|---|---|
| `cli/` | prompts, argparse, exit codes, rendering | computes anything |
| `analysis/` | the attacks, the statistics, the explanations | prints |
| `cipher/` | encrypt, decrypt, key validation | knows attacks exist |
| `utils/` | letter maths, rendering, config, export | knows about specific ciphers (except `alphabet.py`, which is the letter maths) |

**Why this matters in practice:** because `analysis/` never prints, the same `break_caesar()` serves the CLI, the exporter and the test suite. Because `cli/interactive.py` never computes, the menu is testable by monkeypatching `input()` — no subprocess, no pexpect, 18 tests in 0.4 seconds. Layering is not tidiness; it is what makes the tests cheap enough to actually write.

### Results are data

```python
result = break_caesar(ciphertext)
result.key           # 3
result.plaintext     # "Attack at dawn!"
result.confidence    # 0.98
result.candidates    # all 26, ranked
result.steps         # ["Read 42 letters...", "The Caesar keyspace is only 26..."]
result.to_dict()     # for JSON/Markdown export
```

Three consumers, one object, no duplicated logic.

### Explanations are generated, not written

`steps[]` is built *during* the attack, quoting the real numbers:

```python
steps.append(
    f"Best candidate: shift {best.shift} scores {best.score:.1f}; "
    f"runner-up shift {second.shift} scores {second.score:.1f}. "
    f"The winner is {second.score / best.score:.1f}x better..."
)
```

A hard-coded description would eventually describe something the code no longer does. This one cannot.

---

## The rules

1. **Nothing below `cli/` calls `print()`.** Return data; let the caller render.
2. **`cipher/` must not import `analysis/`.** If that arrow ever reverses, the design is gone.
3. **Reject bad keys; never silently fix them.** Turning `"lemon 5"` into `"LEMON"` means encrypt and decrypt can disagree, and the user will never know why.
4. **Every public function gets a docstring with an example.** Doctests run in CI; the examples cannot rot.
5. **Every bug gets a regression test** in `TestRegression`, forever.
6. **Never let colour carry meaning alone.** `[OK]`, `[!]`, `[X]` come first.
7. **Third-party imports are optional imports.** See the `rich` guard in `utils/formatting.py`.

---

## Adding a cipher

The architecture is built for this: a new cipher is a **new file**, not an edit to an old one (Open/Closed). Worked example — the **Affine cipher**, `E(x) = (ax + b) mod 26`:

### 1. `cipher/affine.py`

Match the shape the other ciphers expose — `encrypt`, `decrypt`, `validate_key`, and a `*KeyError`:

```python
"""The Affine cipher: multiply, then add.

Caesar is the special case a=1. The multiply is the new idea, and it comes with
a catch: `a` must be coprime with 26, or the cipher is not reversible. With
a=2, both A(0) and N(13) map to A -- information is destroyed, and no key can
bring it back.
"""
from math import gcd
from utils.alphabet import ALPHABET_SIZE, char_to_index, index_to_char, is_letter, preserve_case

VALID_A = [a for a in range(1, 26) if gcd(a, 26) == 1]  # 12 values

class AffineKeyError(ValueError):
    """Raised when an affine key is not invertible."""

def validate_key(key) -> tuple[int, int]:
    a, b = key
    if gcd(a, ALPHABET_SIZE) != 1:
        raise AffineKeyError(f"a={a} shares a factor with 26, so the cipher "
                             f"cannot be reversed. Use one of {VALID_A}.")
    return a % ALPHABET_SIZE, b % ALPHABET_SIZE

def encrypt(plaintext: str, key) -> str:
    a, b = validate_key(key)
    return "".join(
        preserve_case(c, index_to_char(a * char_to_index(c) + b)) if is_letter(c) else c
        for c in plaintext
    )

def decrypt(ciphertext: str, key) -> str:
    a, b = validate_key(key)
    a_inv = pow(a, -1, ALPHABET_SIZE)   # modular inverse; Python 3.8+
    return "".join(
        preserve_case(c, index_to_char(a_inv * (char_to_index(c) - b))) if is_letter(c) else c
        for c in ciphertext
    )
```

### 2. `analysis/affine_breaker.py`

Twelve valid `a` values × 26 `b` values = **312 keys**. Brute force them all and score with `english_score` — the frequency toolkit does not care which cipher produced the text:

```python
from analysis.frequency import confidence, english_score
from cipher import affine

def break_affine(ciphertext: str):
    candidates = sorted(
        ((english_score(affine.decrypt(ciphertext, (a, b))), (a, b))
         for a in affine.VALID_A for b in range(26)),
        key=lambda t: t[0],
    )
    best, second = candidates[0], candidates[1]
    return best[1], affine.decrypt(ciphertext, best[1]), confidence(best[0], second[0])
```

### 3. Tests, then CLI

`tests/test_affine.py` — round-trip every valid key, assert bad `a` raises, assert `a=1` is exactly Caesar. Then add subcommands in `cli/args.py` and a menu entry.

**Note what you did not touch:** `caesar.py`, `vigenere.py`, `frequency.py`, `alphabet.py`. That is the architecture doing its job.

---

## Adding an attack

Attacks live in `analysis/` and follow one contract:

1. Take ciphertext (plus options), return a **result dataclass**.
2. Populate **`steps[]`** during the work, with real numbers.
3. Report **confidence**, and **warn** when the data is too thin.
4. **Print nothing.**

Reuse `analysis/frequency.py` — `chi_squared`, `index_of_coincidence`, `bigram_fitness`, `english_score`, `confidence` are cipher-agnostic by design.

**Before you use χ² to choose between models of different sizes, read `docs/PLANNING.md` §10.7.** That mistake is already in this codebase's history.

---

## Testing

| File | Level | What |
|---|---|---|
| `test_caesar.py`, `test_vigenere.py` | unit | maths, validation, edge cases |
| `test_frequency.py` | unit + property | statistics, IC invariance, anti-overfitting |
| `test_breakers.py` | integration + regression | encrypt → break → recover |
| `test_cli.py` | contract | exit codes, stdout hygiene, export |
| `test_interactive.py` | contract | the menu, via scripted keystrokes |
| `test_utils.py` | unit | alphabet, config, export, formatting |

### Patterns worth copying

**Parametrise the matrix:**
```python
@pytest.mark.parametrize("shift", range(26))
def test_recovers_every_shift(self, shift):
    assert break_caesar(caesar.encrypt(MEDIUM, shift)).key == shift
```

**Test the theory, not just the code:**
```python
def test_invariant_under_caesar_shift(self):
    assert math.isclose(index_of_coincidence(ENGLISH),
                        index_of_coincidence(caesar.encrypt(ENGLISH, 13)))
```
If that fails, the mathematics is wrong, not the implementation.

**Test the menu without a subprocess:**
```python
def script(monkeypatch, answers):
    queue = list(answers)
    def fake_input(prompt=""):
        if not queue: raise EOFError
        return queue.pop(0)
    monkeypatch.setattr("builtins.input", fake_input)

def test_bad_key_reprompts_without_losing_text(self, monkeypatch, capsys):
    script(monkeypatch, ["1", "hello", "banana", "3", "9"])
    run_interactive(PLAIN)
    out = capsys.readouterr().out
    assert "whole number" in out
    assert "khoor" in out          # the text survived the bad key
```

**Test failure, not only success:**
```python
def test_short_text_warns_instead_of_lying(self):
    result = break_vigenere(vigenere.encrypt("hello there", "LEMON"))
    assert result.warnings and result.confidence <= 0.45
```

### Standards

- Coverage ≥ 85% overall, 100% for `cipher/` and `utils/alphabet.py`.
- Suite under 10 seconds. A slow suite is a suite nobody runs.
- Assert on *relations* (English scores better than gibberish), not magic numbers — so the corpus can improve without breaking 40 tests.

---

## Style

- **PEP 8**, 88-column soft limit, type hints on public functions.
- **Google-style docstrings** with an `Examples:` block that runs as a doctest.
- **Comments explain *why*.** The code already says what.
- Guard clauses over nesting; dataclasses for structured returns; f-strings.

### The docstring standard

Docstrings here are courseware. They explain the concept before the API:

```python
def index_of_coincidence(text: str) -> float:
    """Probability that two letters drawn at random from ``text`` match.

    Pick two letters out of the text blindly. How often are they the same
    letter? In random gibberish, once every 26 tries (about 0.038). In English,
    far more often -- about 0.067 -- because so much of the text is E, T, A, O.

    Why this matters: the value **does not change when you shift the alphabet**...
    """
```

Someone reading this file should be able to learn the subject from it. That is the bar.

---

## Traps for the unwary

**`bool` is an `int` in Python.** `isinstance(True, int)` is `True`, so `validate_shift(True)` would silently mean "shift by 1". Rejected explicitly in `caesar.validate_shift`.

**`%` differs across languages.** `(-1) % 26` is `25` in Python and `-1` in C, Java and JavaScript. Porting this code without fixing that gives you a cipher that fails only on negative keys — which the tests catch, and a human review would not.

**Non-letters must not advance the Vigenère key.** Punctuation positions are public knowledge; letting them consume key letters leaks alignment for free.

**Don't compare models of different sizes with a fitted metric.** §10.7. It cost three hours and produced the bigram model.

**The corpus must stay original.** `data/english_corpus.txt` is prose written for this project. Never paste copyrighted text in — a repo you cannot publish is a repo that failed.

**`rich` is optional and must stay optional.** Both paths are tested. Breaking the fallback breaks the lecture-theatre demo, which is the one use case that cannot be retried.

---

## Contributing

1. Branch. 2. Write the test first. 3. Make it pass. 4. Run the full suite plus doctests. 5. Update the docs in the same commit — a change that leaves the docs stale is not finished.

Good first issues: implement Friedman's formula as a third key-length estimator; add the Affine cipher (walked through above); add `--tutorial` mode; split `Formatter` into policy and renderer (see the design review, §18).
