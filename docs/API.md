# API Reference

Every public function, by module. The library is importable on its own — no CLI required:

```python
import sys; sys.path.insert(0, "/path/to/cipher-breaker")

from cipher import caesar, vigenere
from analysis.caesar_breaker import break_caesar
from analysis.vigenere_breaker import break_vigenere

ct = vigenere.encrypt("Attack at dawn!", "LEMON")   # 'Lxfopv ef rnhr!'
break_caesar(caesar.encrypt("hello world " * 5, 7)).key   # 7
```

---

## `cipher.caesar`

Shift every letter by a fixed number. Key: an integer 0–25 (anything else wraps).

### `encrypt(plaintext: str, shift: object) -> str`
Shift each letter forward. Non-letters pass through; case is preserved.
```python
>>> caesar.encrypt("Attack at dawn!", 3)
'Dwwdfn dw gdzq!'
```

### `decrypt(ciphertext: str, shift: object) -> str`
Encryption with the opposite shift.
```python
>>> caesar.decrypt("Dwwdfn dw gdzq!", 3)
'Attack at dawn!'
```

### `validate_shift(shift: object) -> int`
Coerce and check a key, normalised to 0–25. Accepts `int` or a digit string.
**Raises** `CaesarKeyError` if not an integer. Booleans are rejected explicitly (`True` is an `int` in Python, and `shift=True` silently meaning 1 would be a nasty bug).
```python
>>> caesar.validate_shift("-1")
25
```

### `brute_force(ciphertext: str) -> list[tuple[int, str]]`
All 26 decryptions as `(shift, plaintext)`. The entire keyspace.

### `CaesarKeyError(ValueError)`

---

## `cipher.vigenere`

Shift every letter by a different amount, taken from a repeating keyword.

### `encrypt(plaintext: str, key: str) -> str`
```python
>>> vigenere.encrypt("Attack at dawn!", "LEMON")
'Lxfopv ef rnhr!'
```

### `decrypt(ciphertext: str, key: str) -> str`

### `validate_key(key: object) -> str`
Non-empty, letters only; returns it uppercased.
**Raises** `VigenereKeyError`. Rejects rather than strips: silently turning `"lemon 5"` into `"LEMON"` would let encrypt and decrypt disagree.

### `key_schedule(key: str, length: int) -> list[int]`
The first `length` shifts produced by repeating the key.
```python
>>> vigenere.key_schedule("LEMON", 7)
[11, 4, 12, 14, 13, 11, 4]
```

### `effective_key_length(key: str, text: str) -> int`
How many key letters actually touch the text. A 20-letter key on an 8-letter message uses 8.

### `VigenereKeyError(ValueError)`

---

## `analysis.frequency`

The statistical toolkit. Cipher-agnostic by design — it does not know which cipher it serves.

### Constants

| Name | Value | Meaning |
|---|---|---|
| `ENGLISH_FREQUENCIES` | dict | Letter proportions of English prose |
| `ENGLISH_IOC` | 0.0667 | IC of English |
| `RANDOM_IOC` | 0.0385 | IC of random letters (1/26) |
| `ENGLISH_FITNESS` | −2.30 | Bigram fitness of English (calibrated on held-out prose) |
| `RANDOM_FITNESS` | −3.25 | Bigram fitness of random letters |

### `letter_counts(text: str) -> Counter`
Counts A–Z, ignoring case and non-letters. **All 26 keys always present**, including zeros.

### `letter_frequencies(text: str) -> dict[str, float]`
Proportions summing to 1.0. Empty text → all zeros, not `ZeroDivisionError`.

### `chi_squared(text: str) -> float`
Distance from English letter frequencies. **Lower is better.** English (~500 letters): 10–40. Wrong shift: 200–2000. Returns `inf` if there are no letters.

### `index_of_coincidence(text: str) -> float`
Probability two random letters match. English ≈ 0.067, random ≈ 0.038.
**Invariant under alphabet shifts** — the property the Vigenère attack depends on. Texts under 2 letters → 0.0.

### `bigram_fitness(text: str) -> float`
Average log₁₀ probability of the text's letter pairs. **Higher is better**; always negative.
Independent of the per-column χ² fit, which is the entire point — see PLANNING.md §10.7. Under 2 letters → `RANDOM_FITNESS`.

### `english_score(text: str) -> float`
χ², discounted up to 30% for real English words. Lower is better.

### `word_hit_rate(text: str) -> float`
Fraction of tokens among the 60 commonest English words. Returns 0.0 with no word breaks — a **bonus signal only**, never a verdict.

### `confidence(best, runner_up=None) -> float`
0–1, from χ²-style scores. Combines absolute quality with the margin over second place. A display heuristic, not a probability.

### `fitness_confidence(best, runner_up=None) -> float`
The same, for bigram fitness.

### `histogram_rows(text, width=40) -> list[tuple[str, float, float, str]]`
`(letter, observed %, English %, bar)` for display.

---

## `analysis.caesar_breaker`

### `break_caesar(ciphertext: str, top_n: int = 26) -> CaesarBreakResult`
Recover the shift and plaintext from ciphertext alone. Tries all 26 keys, scores each with `english_score`. Never raises on odd input — text with no letters returns confidence 0.0.
```python
>>> break_caesar(caesar.encrypt("the quick brown fox jumps over the lazy dog", 7)).key
7
```

### `CaesarBreakResult`

| Attribute | Type | |
|---|---|---|
| `key` | `int` | recovered shift |
| `plaintext` | `str` | recovered message |
| `confidence` | `float` | 0–1 |
| `candidates` | `list[Candidate]` | all 26, ranked best-first |
| `steps` | `list[str]` | the explanation, generated during the attack |
| `elapsed_seconds` | `float` | |
| `best` | `Candidate` | `candidates[0]` |
| `to_dict()` | `dict` | for export |

### `Candidate`
`shift`, `plaintext`, `chi_squared`, `score`, `.preview(width=60)`.

---

## `analysis.vigenere_breaker`

### `break_vigenere(ciphertext, max_key_length=20, known_key_length=None, candidates_to_try=3) -> VigenereBreakResult`
Recover the keyword and plaintext. Estimates the key length (IC + Kasiski), solves the top candidates column by column, and picks the shortest key that explains the text.
```python
>>> break_vigenere(vigenere.encrypt("we hold these truths ... " * 4, "LEMON")).key
'LEMON'
```
**Warns and caps confidence at 0.45** below 20 letters per key position.

### `VigenereBreakResult`

| Attribute | Type | |
|---|---|---|
| `key` | `str` | recovered keyword |
| `plaintext` | `str` | |
| `confidence` | `float` | 0–1 |
| `key_length_guesses` | `list[KeyLengthGuess]` | ranked, with evidence |
| `kasiski_factors` | `dict[int, int]` | `{length: votes}` |
| `steps` | `list[str]` | |
| `warnings` | `list[str]` | why the answer may be unreliable |
| `to_dict()` | `dict` | |

### `KeyLengthGuess`
`length`, `average_ioc`, `kasiski_votes`, `combined_score`.

### `kasiski_examination(ciphertext, min_sequence=3, max_key_length=20) -> dict[int, int]`
Repeated 3-gram distances → factors → `{key_length: votes}`. Votes for the true length *and its factors*, which is why it is combined with the IC rather than trusted alone.

### `ioc_key_lengths(ciphertext, max_key_length=20) -> list[tuple[int, float]]`
`(length, average IC of its columns)`. Look for the jump to ~0.067.

### `estimate_key_length(ciphertext, max_key_length=20) -> list[KeyLengthGuess]`
Ranked candidates, combining both methods with a small penalty for longer keys.

### `recover_key(ciphertext, key_length) -> str`
Solve each column by χ², assuming the length is right. **Raises** `ValueError` if `key_length < 1`.

### `minimal_period(key: str) -> str`
Shortest repeating unit. `"LEMONLEMON"` → `"LEMON"`.

---

## `utils.alphabet`

`ALPHABET`, `ALPHABET_SIZE` (26), `is_letter`, `char_to_index` (`'C'`→2, raises on non-letters), `index_to_char` (wraps: 26→`'A'`, −1→`'Z'`), `normalise_shift` (−1→25), `letters_only` (`"Hi, Bob!"`→`"HIBOB"`), `fold_unicode` (`"café"`→`"cafe"`), `preserve_case`.

## `utils.formatting`

### `Formatter(plain: bool = False)`
All terminal output. `title`, `success` (`[OK]`), `warn` (`[!]`), `error` (`[X]`), `muted`, `banner`, `menu`, `progress(label)` (context manager), `confidence_bar`, `caesar_candidates`, `key_length_table`, `frequency_histogram`, `steps`.

Colour is suppressed by `plain=True`, the `NO_COLOR` env var, or a non-TTY stdout. `RICH_AVAILABLE` reports whether `rich` was importable.

## `utils.config`

### `Settings`
`max_key_length`, `top_candidates`, `no_color`, `log_level`, `log_file`, `explain`.
`Settings.load(path=None)` — JSON, falling back to defaults. Missing file, malformed JSON and unknown keys all warn rather than raise.

### `setup_logging(level="WARNING", log_file=None)`
Logs to **stderr** so piped plaintext on stdout stays clean.

## `utils.export`

### `export_result(result, path) -> Path`
Format from the extension: `.json`, `.md`, `.txt`. Creates parent directories.
**Raises** `ExportError` on an unsupported extension or an unwritable path.

## `cli.args`

### `run(argv=None) -> int`
One CLI invocation → exit code (0 ok, 1 user error, 2 usage, 130 interrupt).

### `build_parser() -> argparse.ArgumentParser`

## `cli.interactive`

### `run_interactive(settings=None) -> int`
The menu loop. Reads via `input()`, so tests drive it with `monkeypatch`.

---

## Exceptions

| Exception | Base | Raised when |
|---|---|---|
| `CaesarKeyError` | `ValueError` | shift isn't an integer |
| `VigenereKeyError` | `ValueError` | key is empty or has non-letters |
| `ExportError` | `ValueError` | bad export format or unwritable path |

All inherit `ValueError`, so `except ValueError` catches every user-input error the library raises.
