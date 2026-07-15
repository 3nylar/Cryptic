# Security Notes

## The short version

**Do not use these ciphers for anything. Ever.**

Caesar has been broken since the 9th century. Vigenère has been broken since 1863 — and was probably broken in 1854 by Babbage, who didn't publish. Both fall to a laptop in milliseconds. This tool exists to *demonstrate* that, and it is safe to publish precisely because it gives no capability against anything anyone uses.

If you need real encryption, skip to [What to use instead](#what-to-use-instead).

---

## Why they fail

### Caesar: 26 keys

That's the whole story. A human tries all 26 in a minute; a computer does it in microseconds. No amount of cleverness helps — the keyspace *is* the limit.

### Vigenère: the key repeats

This one is worth understanding properly, because the shape of the failure recurs in modern systems.

The keyspace is genuinely enormous — 26¹² ≈ 9.5 × 10¹⁶ for a twelve-letter key. Brute-forcing it at a billion keys per second would take about three years.

**Nobody brute-forces it.** The key repeats every 12 letters, so the message is really 12 interleaved Caesar ciphers. The attacker finds the length (the index of coincidence hands it over), splits the text into 12 columns, and solves each one independently:

> **26¹² = 95,428,956,661,682,176 → 26 × 12 = 312**

Exponential to linear. About 40 milliseconds.

**The lesson generalises: a large keyspace with exploitable internal structure is not a large keyspace.** Structure is what gets you, not size. That is not a historical footnote — it is the shape of a great many real breaks, including modern ones.

---

## Attack models

Cryptographers grade attacks by what the attacker is *given*. Weaker inputs make stronger attacks.

| Model | Attacker has | Caesar | Vigenère | AES |
|---|---|---|---|---|
| **Ciphertext-only** | just the ciphertext | ✗ broken | ✗ broken | ✓ secure |
| **Known-plaintext** | some plaintext + its ciphertext | ✗ 1 letter reveals the key | ✗ m letters reveal the key | ✓ secure |
| **Chosen-plaintext** | can encrypt anything they like | ✗ encrypt `A`, read the key | ✗ encrypt `AAAA…`, ciphertext **is** the key | ✓ secure (proper mode) |
| **Chosen-ciphertext** | can decrypt things too | ✗ | ✗ | ✓ secure (authenticated mode) |

**Ciphertext-only is the weakest thing an attacker can be given, and it is enough for both.** That is what "broken" means.

The others are not hypothetical. Known plaintext is everywhere: `Dear Sir`, `--BEGIN`, a date, a fixed header. Breaking Enigma leaned on guessing that a German weather report contained *WETTER*. Chosen plaintext is what a web form is: type something, watch it get encrypted.

---

## Dictionary attacks

Vigenère keys are words, because humans have to remember them. `LEMON`, `SECRET`, `PASSWORD`, `LIVERPOOL`. A 100,000-word list beats 26^m for any key a person actually chose.

This has not aged into irrelevance. The modern equivalent is a password list, and it is still how most accounts fall. Humans are a terrible source of randomness, and we have known it for four hundred years.

---

## Modern computing power

Caesar was safe in 50 BC — against people who could not read. Vigenère was safe in 1553 — against people doing arithmetic with a quill. Both assumptions expired.

**Attacker capability only ever increases.** So "nobody has broken it yet" is not a security claim; it is an absence of evidence. AES-256 is specified with a margin against machines that do not exist, because that is what designing for the future means.

---

## Comparison with AES

| Property | Caesar | Vigenère | AES-256 |
|---|---|---|---|
| Year | 50 BC | 1553 | 2001 |
| Keyspace | 26 | 26^m | 1.2 × 10⁷⁷ |
| **Effective work to break** | **26** | **26 × m** | **2²⁵⁶** |
| Diffusion | none | none | yes |
| Confusion | none | none | yes |
| Non-linear | no | no | yes |
| Same input → same output | always | always | no (random IV) |
| Statistical fingerprint | full | partial | none detectable |
| Public scrutiny | none | none | 25+ years, worldwide |
| **Status** | **broken (9th c.)** | **broken (1863)** | **unbroken** |

### What AES has that these lack

1. **Confusion and diffusion** (Shannon, 1949). Flip one plaintext bit; about half the output bits change, unpredictably. Caesar changes exactly one letter — the structure survives the encryption, and structure is what the attacker eats.
2. **Rounds.** 14 of them, each substituting, permuting and mixing. Classical ciphers apply one simple operation once.
3. **Non-linearity.** AES's S-box is deliberately non-linear. Caesar and Vigenère are *linear* in ℤ/26ℤ — and linear systems are solvable systems.
4. **Adversarial public design.** AES was chosen by open competition: five years, fifteen candidates, the world's cryptanalysts attacking every one. Kerckhoffs's principle, industrialised.
5. **Semantic security.** Encrypt the same message twice with a proper mode, get different ciphertext. Caesar gives the same answer every time, forever.

### Even AES can be used badly

**ECB mode.** Encrypt an image of the Linux penguin with AES-ECB and you can still see the penguin — identical blocks encrypt identically, so the structure survives. A perfect cipher, applied wrongly, leaks. It is the same failure as Vigenère's repeating key, wearing a modern suit.

**Reused IVs.** A repeated nonce in CTR/GCM can collapse the security of both messages.

**Unauthenticated encryption.** An attacker who can flip bits undetected has often already won — even without reading anything. Encryption without authentication is a hazard, not a feature.

---

## What to use instead

**Never write your own.** Not the algorithm, not the mode, not the padding. This is not gatekeeping; it is the accumulated experience of everyone who tried.

**Python:**

```python
from cryptography.fernet import Fernet

key = Fernet.generate_key()      # keep this secret; don't invent it yourself
f = Fernet(key)
token = f.encrypt(b"Attack at dawn")
f.decrypt(token)                 # b'Attack at dawn'
```

Fernet is AES-128-CBC with HMAC authentication, sane defaults, and no knobs to get wrong. If you need the knobs, you need `cryptography`'s AEAD APIs and to know why.

**Generally:**

| Need | Use |
|---|---|
| Symmetric encryption | **AES-GCM** or **ChaCha20-Poly1305** (both authenticated) |
| Password → key | **Argon2id**, scrypt, or PBKDF2 — never the password directly |
| Password storage | **Argon2id** or bcrypt — and never encryption, always hashing |
| Transport | **TLS 1.3**, via your platform's library |
| Libraries | `cryptography` (Python), libsodium / NaCl (C and everything), your OS keystore |
| Randomness | `secrets` / `os.urandom` — **never** `random`, which is predictable by design |

**Rules that survive contact with reality:** authenticate everything you encrypt; never reuse a nonce; get keys from a KDF or a CSPRNG, never from your imagination; keep the algorithm public and the key secret; assume the attacker has your source code, because they do.

---

## Security of this tool

This is a teaching tool with **no security claims**, so it has no vulnerabilities to speak of — but the trust boundary is worth stating:

| Aspect | Status |
|---|---|
| Network | none. It never opens a socket. |
| Data handling | text in memory; nothing written unless you pass `--export` |
| Untrusted input | ciphertext is treated as data, never evaluated |
| Dependencies | zero required (`rich` optional) — a small supply chain is a small attack surface |
| `--file` | reads any path you can read. **No size limit** — a 4 GB file is an easy self-DoS. Known; see PLANNING.md §18. |
| Corpus | `data/english_corpus.txt` is trusted without an integrity check |
| Logs | may contain your plaintext at `--log-level DEBUG`. Don't do that with anything you care about. |

**Reporting:** open a GitHub issue. There is no embargo process, because there is nothing here worth embargoing.

---

## Ethics

This tool attacks ciphers that have been publicly broken for over 160 years. Publishing it gives an attacker nothing they could not get from a Wikipedia article and an afternoon — which is exactly why it is safe to publish, and why teaching this material openly is right.

**The principle:** understanding attacks is how defences get built. A generation of engineers who have never watched a cipher fall will build systems that fail the same way. The people who broke Enigma were not villains; they were the reason it mattered.

**The boundary:** this is for messages you own or have permission to read. Using it on someone else's data is unlawful in most jurisdictions, and the fact that the cipher is weak is not a defence — an unlocked door is not an invitation.
