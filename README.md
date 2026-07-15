# Cipher Breaker

**Encrypt and decrypt Caesar and Vigenère ciphers — then break them without the key, and watch the tool explain how.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-204%20passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-93%25-brightgreen)](tests/)
[![Dependencies](https://img.shields.io/badge/dependencies-none%20required-brightgreen)](requirements.txt)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

A teaching tool for classical cryptography and cryptanalysis. Built for a university Ch. 1–2 assignment, written to be readable by someone who has never studied either.

---

## The 30-second demo

Someone hands you this. No key. No hints.

```bash
$ python main.py caesar-break -t "Dwwdfn dw gdzq. Eulqj wkuhh odgghuv dqg wkh orqj ursh."
Attack at dawn. Bring three ladders and the long rope.
[OK] Key = 3   confidence [####################] 100%
```

Fine — Caesar has 26 keys, that is just brute force. So try the one that was called *unbreakable* for three hundred years, with a **twelve-letter key**:

```bash
$ python main.py vigenere-break -f examples/04_vigenere_cryptography.txt
The index of coincidence is the probability that two letters drawn at random...
[OK] Key = 'CRYPTOGRAPHY'   confidence [####################] 100%
```

That key has **95,428,956,661,682,176 possibilities** — 9.5 × 10¹⁶. It fell in about **40 milliseconds**, and the tool never tried a second key.

**That gap is the entire point of this project.** Not "the keyspace was too small" — it was enormous. The key *repeated*, and repetition let the attacker take the lock apart one tumbler at a time: 26 × 12 = 312 tests instead of 10¹⁶.

> **Key size is not security.**

---

## Install

```bash
git clone https://github.com/yourname/cipher-breaker.git
cd cipher-breaker
python main.py
```

That's it. **No dependencies are required** — the tool runs on a bare Python 3.9+ and falls back to plain ASCII output. `pip install rich` gets you colour and tables if you want them.

Full details: [docs/INSTALL.md](docs/INSTALL.md).

---

## Use it

### Interactive (start here)

```bash
python main.py
```

```
====================================
 Cipher Breaker
====================================
1. Encrypt Caesar        4. Encrypt Vigenère      7. Compare Algorithms
2. Decrypt Caesar        5. Decrypt Vigenère      8. Help
3. Break Caesar          6. Break Vigenère        9. Exit
====================================
```

Every prompt tells you what a valid answer looks like. A typo re-asks for the key — it never throws away the text you just pasted. Type `q` at any prompt to leave.

### Command line

```bash
# Encrypt and decrypt
python main.py caesar-encrypt   -t "Attack at dawn!" -k 3
python main.py vigenere-encrypt -t "Attack at dawn!" -k LEMON

# Break, with no key
python main.py caesar-break   -f examples/01_caesar_shift3.txt
python main.py vigenere-break -f examples/03_vigenere_lemon.txt

# Look at the statistics that make it possible
python main.py stats -f examples/06_plaintext_sample.txt        # IC ≈ 0.067
python main.py stats -f examples/04_vigenere_cryptography.txt   # IC ≈ 0.041

# Pipe it, script it, export it
cat secret.txt | python main.py caesar-break --export report.md
python main.py compare
```

Plaintext goes to stdout and everything else to stderr, so `> out.txt` gives you a clean file. Exit codes: `0` success, `1` user error, `2` bad usage.

---

## It explains itself

The explanation is the product; the plaintext is a by-product.

```
How the attack worked
  1. Read 779 letters of ciphertext.
  2. Whole-text index of coincidence = 0.0413 (English ~ 0.0667, random ~
     0.0385). A value near random says several alphabets are in use, i.e.
     Vigenère, not Caesar.
  3. Kasiski examination: distances between repeated 3-letter chunks favour
     key lengths 2 (45 votes), 3 (43 votes), 6 (42 votes), 12 (40 votes).
  4. Slicing the text every m letters and averaging each slice's IC ranks the
     key lengths: 12 (IC 0.075), 6 (IC 0.062), 18 (IC 0.062), 3 (IC 0.049).
  5. For each candidate length, split the text into that many columns (each
     column is a plain Caesar cipher) and solve every column with chi-squared.
     Then judge each resulting plaintext on letter *pairs* (TH, HE, IN...),
     which a per-column shift cannot fake.
  6. Shortest key that explains the text: 12 letters. Recovered key = 'CRYPTOGRAPHY'.
```

Those numbers are generated during the attack, not written in advance — so the explanation cannot drift away from what the code actually did.

## It admits when it doesn't know

```bash
$ python main.py vigenere-break -f examples/05_vigenere_short_hard.txt
[OK] Key = 'XCKE'   confidence [#########-----------] 45%
[!] Only ~3 letters per key position (want 20+). Frequency statistics are
    shaky here, so treat the key as a guess rather than a result.
```

That example **fails on purpose** and ships in the repo. Cryptanalysis is statistics, and statistics need data — a tool that always claims success teaches the wrong lesson.

---

## How it works

**Caesar** — try all 26 keys, score each result with a chi-squared test against English letter frequencies, take the best. Done in under a millisecond.

**Vigenère** — three moves:

1. **Find the key length.** Two independent methods vote: *Kasiski* (repeated ciphertext chunks sit a multiple of the key length apart) and the *index of coincidence* (slice the text every m letters; when m is right, each slice is Caesar-encrypted English and its IC jumps from 0.038 to 0.067).
2. **Split.** With the length known, the message is just m interleaved Caesar ciphers.
3. **Conquer.** Solve each column separately with chi-squared. Each answer is one key letter.

The maths, properly: [docs/CRYPTOGRAPHY_NOTES.md](docs/CRYPTOGRAPHY_NOTES.md).

### One bug worth reading about

The Vigenère breaker originally preferred a **20-letter key over the true 5-letter one** — and by its own scoring, it was right to. A longer key has more free parameters, and more parameters always fit the letter counts better, even when the plaintext is visible garbage. The optimiser had learned to satisfy the scorer instead of doing the job.

The fix was not a bigger penalty; it was a second opinion the optimiser cannot bribe. **Letter pairs** (TH, HE, IN) run *across* the column boundaries, so no choice of per-column shifts can manufacture them.

The general lesson has nothing to do with cryptography: *when a search optimises a metric, that metric stops being a fair judge of the search.* Written up in [docs/PLANNING.md §10.7](docs/PLANNING.md#107-scoring-algorithms--and-a-bug-worth-keeping).

---

## Speed

```
  letters |    C-enc |  C-break |    V-enc |   V-break |      V key
    1,000 |    0.53m |   31.57m |    0.61m |     50.2m |   LEMONADE
   10,000 |    5.43m |  319.53m |    6.23m |    407.7m |   LEMONADE
   50,000 |   28.24m | 1641.71m |   31.90m |   2215.7m |   LEMONADE
```

Milliseconds, on an ordinary laptop (`python benchmark.py`). For scale: brute-forcing AES-256 at a trillion keys per second would take about **10⁵⁷ years**.

| Cipher | Keyspace | Effective work to break | Status |
|---|---|---|---|
| Caesar | 26 | 26 | Broken since the 9th century |
| Vigenère (m letters) | 26^m | **26 × m** | Broken since 1863 |
| AES-256 | 1.2 × 10⁷⁷ | 2²⁵⁶ | Unbroken after 25 years of public attack |

---

## Project layout

```
cipher/      the ciphers          — knows nothing about attacks
analysis/    the attacks          — imports cipher/, never the reverse
utils/       alphabet, output, config, export
cli/         the only layer allowed to print
tests/       204 tests, 93% coverage
docs/        planning, guides, the maths, the write-up
examples/    sample ciphertexts (one fails on purpose)
```

Dependencies point one way, downward. That is why the test suite can drive the interactive menu with fake keystrokes, and why a web front end would be a renderer swap rather than a rewrite.

---

## Documentation

| Document | For |
|---|---|
| [INSTALL.md](docs/INSTALL.md) | Getting it running, on any OS |
| [USER_GUIDE.md](docs/USER_GUIDE.md) | Every command and menu option |
| [WRITEUP.md](docs/WRITEUP.md) | **The report** — classical crypto, why it fails, vs AES |
| [CRYPTOGRAPHY_NOTES.md](docs/CRYPTOGRAPHY_NOTES.md) | The mathematics in full |
| [PLANNING.md](docs/PLANNING.md) | PRD, architecture, design review (19 sections) |
| [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) | Architecture; how to add a cipher |
| [API.md](docs/API.md) | Module reference |
| [SECURITY.md](docs/SECURITY.md) | Why these fail; what to use instead |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | When something goes wrong |

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest tests -q                    # 204 tests, ~7 seconds
python -m pytest --doctest-modules cipher analysis utils
```

---

## ⚠️ Do not use this for anything real

Every cipher here has been publicly broken for over a century. This tool exists to *demonstrate* that. It is safe to publish precisely because it gives no capability against anything anyone uses.

For real encryption, never write your own — use [`cryptography`](https://cryptography.io) (Python), libsodium, or your platform's audited primitives. AES-GCM or ChaCha20-Poly1305, with keys from a proper KDF. See [docs/SECURITY.md](docs/SECURITY.md).

## Licence

MIT — see [LICENSE](LICENSE). The bundled corpus (`data/english_corpus.txt`) is original prose written for this project.
