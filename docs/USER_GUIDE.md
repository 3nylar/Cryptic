# User Guide

Everything the tool does, and when to use which part.

**Contents:** [Two ways to run it](#two-ways-to-run-it) · [The menu](#the-interactive-menu) · [Commands](#command-line-reference) · [Reading the output](#reading-the-output) · [Getting good results](#getting-good-results) · [Exporting](#exporting-results) · [Configuration](#configuration) · [Recipes](#recipes)

---

## Two ways to run it

|            | Interactive                     | Command line                           |
| ---------- | ------------------------------- | -------------------------------------- |
| Start with | `python main.py`                | `python main.py caesar-break -t "..."` |
| Good for   | learning, demos, one-offs       | scripting, marking, pipelines          |
| Input      | prompts, one question at a time | flags, files, stdin                    |

They do the same work. Beginners should start with the menu.

---

## The interactive menu

```bash
python main.py
```

```
====================================
 Cryptic
====================================
1. Encrypt Caesar
2. Decrypt Caesar
3. Break Caesar
4. Encrypt Vigenère
5. Decrypt Vigenère
6. Break Vigenère
7. Compare Algorithms
8. Help
9. Exit
====================================
```

**Everywhere:** `q` (or Ctrl-C) leaves. Enter accepts the shown default. At any text prompt, `file:/path/to/file.txt` reads from a file instead of making you paste. A bad key re-asks for the key only — your text is safe.

### 1, 2 — Caesar encrypt / decrypt

You supply the shift: any whole number. `-1` and `25` do the same thing; so do `29` and `3`. Case, spaces, punctuation and emoji all survive.

```
  Text: Attack at dawn!
  Shift (a whole number, e.g. 3): 3
[OK] Ciphertext: Dwwdfn dw gdzq!
```

### 3 — Break Caesar

**No key needed.** Paste ciphertext; the tool tries all 26 keys, scores each result against English letter frequencies, and shows you the ranking.

```
[OK] Key = 11   confidence [####################] 100%
  Plaintext: we hold these truths to be self evident...

Top 5 candidate plaintexts
+-------+--------+-------+------------------------------------------+
| Shift | Chi-sq | Score | Plaintext preview                        |
+-------+--------+-------+------------------------------------------+
| 11    | 28.4   | 19.9  | we hold these truths to be self evident…  |
| 4     | 412.7  | 412.7 | dl solk wolzl aybaoz av il zlsm lcpkly…   |
...
```

The gap between row 1 and row 2 is the story. Row 1 looks like English; nothing else comes close.

### 4, 5 — Vigenère encrypt / decrypt

You supply a keyword — letters only, any length. `LEMON` and `lemon` are the same key.

### 6 — Break Vigenère

**No key needed.** Needs more text than Caesar does: roughly **20 letters per key letter**. See [Getting good results](#getting-good-results).

```
[OK] Key = 'LEMON'   confidence [####################] 100%

Key length evidence
+--------+--------+---------------+-------+
| Length | Avg IC | Kasiski votes | Score |
+--------+--------+---------------+-------+
| 5      | 0.0683 | 45            | 1.360 |
| 10     | 0.0617 | 0             | 0.715 |
| 4      | 0.0454 | 0             | 0.208 |
+--------+--------+---------------+-------+
```

Read the **Avg IC** column: 5 scores 0.068 (English), 4 scores 0.045 (mush). That single column is the key length announcing itself.

### 7 — Compare algorithms

The table that makes the point:

```
+----------+----------+---------------+----------------------------------+------------+
| Cipher   | Keyspace | Time to break | Best known attack                | Modern use |
+----------+----------+---------------+----------------------------------+------------+
| Caesar   | 26       | instant       | Ciphertext-only frequency analysis | None       |
| Vigenère | 26^m     | milliseconds  | Kasiski + IC + per-column chi-sq | None       |
| AES-256  | 2^256    | infeasible    | No practical attack known        | Standard   |
+----------+----------+---------------+----------------------------------+------------+
```

### 8 — Help

Defines every term the tool uses before it uses it. If you are new, read this first.

### Hidden: `s` — statistics

Not on the menu. Type `s` for the frequency histogram, index of coincidence and chi-squared of any text. The most educational option in the tool.

---

## Command-line reference

```bash
python main.py <command> [options]
python main.py <command> --help      # every command has its own help
```

| Command            | Does                                  | Key required |
| ------------------ | ------------------------------------- | ------------ |
| `caesar-encrypt`   | Encrypt with a shift                  | `-k N`       |
| `caesar-decrypt`   | Decrypt with a known shift            | `-k N`       |
| `caesar-break`     | **Recover the shift and plaintext**   | no           |
| `vigenere-encrypt` | Encrypt with a keyword                | `-k WORD`    |
| `vigenere-decrypt` | Decrypt with a known keyword          | `-k WORD`    |
| `vigenere-break`   | **Recover the keyword and plaintext** | no           |
| `stats`            | Histogram, IC, chi-squared            | —            |
| `compare`          | Caesar vs Vigenère vs AES             | —            |
| `interactive`      | Launch the menu                       | —            |

### Options

| Option                | Does                                                     |
| --------------------- | -------------------------------------------------------- |
| `-t`, `--text TEXT`   | Text to process                                          |
| `-f`, `--file PATH`   | Read text from a file (`-` for stdin)                    |
| `-k`, `--key KEY`     | The key (encrypt/decrypt only)                           |
| `--export PATH`       | Write a report: `.json`, `.md` or `.txt`                 |
| `--no-color`          | Plain ASCII output                                       |
| `--no-explain`        | Skip the step-by-step explanation                        |
| `--config PATH`       | Load settings from a JSON file                           |
| `--log-level LEVEL`   | `DEBUG` / `INFO` / `WARNING` / `ERROR` (to stderr)       |
| `--top N`             | Candidates to show (`caesar-break`)                      |
| `--max-key-length N`  | Largest key length to try (`vigenere-break`, default 20) |
| `--key-length N`      | Skip estimation; use this length (`vigenere-break`)      |
| `--version`, `--help` |                                                          |

### Input: three ways, all equal

```bash
python main.py caesar-break -t "Dwwdfn dw gdzq"     # inline
python main.py caesar-break -f secret.txt           # file
cat secret.txt | python main.py caesar-break        # pipe
```

### Exit codes

| Code  | Means                              |
| ----- | ---------------------------------- |
| `0`   | Success                            |
| `1`   | User error (bad key, missing file) |
| `2`   | Bad usage (argparse)               |
| `130` | Interrupted (Ctrl-C)               |

---

## Reading the output

### The confidence bar

```
confidence [####################] 100%     result
confidence [#########-----------]  45%     guess — check the warning
confidence [--------------------]   0%     no letters to work with
```

Confidence combines **how English the answer looks** with **how far ahead of the runner-up it is**. A candidate scoring 40 against a runner-up at 45 is a coin toss; 40 against 400 is a result. It is a display heuristic, not a probability.

**Below ~50%: treat the key as a guess.** The tool will also have printed a warning saying why.

### The Caesar candidates table

| Column                | Means                                                                                                      |
| --------------------- | ---------------------------------------------------------------------------------------------------------- |
| **Shift**             | The key being tried                                                                                        |
| **Chi-sq**            | Distance from English letter frequencies. **Lower is better.** Real English: 10–40. Wrong shift: 200–2000. |
| **Score**             | Chi-squared, discounted up to 30% if real English words appear                                             |
| **Plaintext preview** | The first ~50 characters                                                                                   |

### The Vigenère key-length table

| Column            | Means                                                                                        |
| ----------------- | -------------------------------------------------------------------------------------------- |
| **Length**        | Candidate key length `m`                                                                     |
| **Avg IC**        | Average index of coincidence of the `m` columns. **Near 0.067 = right.** Near 0.038 = wrong. |
| **Kasiski votes** | How many repeated-chunk distances were divisible by `m`                                      |
| **Score**         | Combined, with a small penalty for longer keys (Occam's razor)                               |

Watch for multiples: if the true key is 5, then 10, 15 and 20 will also score well, because they are the same columns sliced finer. The tool prefers the shortest good fit, which is why it reports 5.

### The explanation

Printed by default; `--no-explain` turns it off. Every number in it is real — generated during the attack, not written in advance.

---

## Getting good results

**These attacks are statistics. Statistics need data.** This is the single thing that determines whether the tool works.

| Cipher   | Comfortable                    | Marginal         | Won't work      |
| -------- | ------------------------------ | ---------------- | --------------- |
| Caesar   | 40+ letters                    | 20–40            | < 20            |
| Vigenère | **20+ letters per key letter** | 10–20 per letter | < 10 per letter |

So a 5-letter Vigenère key wants **100+ letters**; a 12-letter key wants **240+**.

| Helps                    | Hurts                                                                             |
| ------------------------ | --------------------------------------------------------------------------------- |
| Ordinary English prose   | Other languages (every constant here is English)                                  |
| More text                | Lists of names, code, numbers                                                     |
| Natural word frequencies | Deliberately odd text (_Gadsby_, written without any E, defeats the whole method) |

**If it fails:** feed it more text; try `--key-length N` if you know it; check the ciphertext really is one of these two ciphers (`stats` will tell you — IC near 0.067 means one alphabet, near 0.038 means many).

---

## Exporting results

```bash
python main.py caesar-break -f secret.txt --export report.md
python main.py vigenere-break -f secret.txt --export results.json
```

| Format  | Contains                                                          | Good for           |
| ------- | ----------------------------------------------------------------- | ------------------ |
| `.json` | key, confidence, timing, plaintext, steps, full candidate ranking | scripting, marking |
| `.md`   | the same, as a formatted report with tables                       | handing in         |
| `.txt`  | key, confidence, plaintext, steps                                 | quick notes        |

In the menu, every break offers an export path at the end.

---

## Configuration

`config.json` in the project root:

```json
{
  "max_key_length": 20,
  "top_candidates": 5,
  "no_color": false,
  "log_level": "WARNING",
  "log_file": null,
  "explain": true
}
```

Precedence, lowest to highest: **built-in defaults → `config.json` → `--config PATH` → command-line flags.** Files hold your habits; flags hold your exceptions. A malformed config warns and falls back to defaults rather than refusing to start.

---

## Recipes

**See why the IC works** — the most instructive pair of commands here:

```bash
python main.py stats -f examples/06_plaintext_sample.txt        # IC ≈ 0.067
python main.py stats -f examples/04_vigenere_cryptography.txt   # IC ≈ 0.041
```

Same language, same author. One number tells them apart, and that number is what makes the whole Vigenère attack possible.

**Watch a big keyspace fall:**

```bash
python main.py vigenere-break -f examples/04_vigenere_cryptography.txt
```

12-letter key, 9.5 × 10¹⁶ possibilities, ~40 ms.

**Watch it fail honestly:**

```bash
python main.py vigenere-break -f examples/05_vigenere_short_hard.txt
```

**Break a whole folder:**

```bash
for f in examples/*caesar*.txt; do
  echo "=== $f"
  python main.py caesar-break -f "$f" --no-explain --no-color 2>/dev/null | head -1
done
```

**Encrypt, then break your own message:**

```bash
python main.py vigenere-encrypt -f essay.txt -k SECRET > secret.txt
python main.py vigenere-break -f secret.txt
```

**Prove the key was never needed:**

```bash
python main.py caesar-encrypt -t "Meet me at midnight by the old oak tree" -k 17 \
  | python main.py caesar-break
```
