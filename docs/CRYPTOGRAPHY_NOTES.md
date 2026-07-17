

Cryptography notes · MD
# Cryptography Notes
 
The mathematics behind the tool, derived rather than asserted. Nothing here needs more than school algebra.
 
**Contents:** 
1. [What this owes to the textbook](#0-what-this-owes-to-the-textbook) 
2. [Modular arithmetic](#1-modular-arithmetic)
3. [Caesar](#2-the-caesar-cipher)
4. [Vigenère](#3-the-vigenère-cipher)
5. [Frequency analysis](#4-frequency-analysis)
6. [Chi-squared](#5-the-chi-squared-test)
7. [Index of coincidence](#6-the-index-of-coincidence)
8. [Kasiski](#7-the-kasiski-examination) 
9. [The attack](#8-the-full-vigenère-attack) 
10. [Bigrams](#9-the-bigram-model)
11. [Reading](#further-reading)
 
---
 
## 0. What this owes to the textbook
 
This project is built on Paar & Pelzl, *Understanding Cryptography* (Springer, 2010). It's worth being precise about which parts of what follows come directly from the book and which parts go beyond it, rather than blurring the two together.
 
**Straight from Chapter 1** ("Introduction to Cryptography and Data Security"): the vocabulary (plaintext, ciphertext, key, Alice/Bob/Oscar), the cryptology/cryptography/cryptanalysis split, Kerckhoffs's Principle, the general substitution cipher and its 26! key space, letter frequency analysis, brute-force vs. analytical attacks, modular arithmetic, the shift/Caesar cipher, and the affine cipher. All of this is §1.1–1.4, pp. 1–20.
 
**Not in the book at all.** I checked — the words *Vigenère*, *Kasiski*, *index of coincidence*, *Friedman*, and *polyalphabetic* do not appear anywhere in the text. The book's classical-cipher coverage stops at the affine cipher. Everything from §3 onward in this file (Vigenère, Kasiski, IC, the chi-squared formalization, the bigram anti-overfitting model) is this project's own extension into classical cryptanalysis, sourced from Friedman (1922) and Kasiski (1863) directly, not from the assigned reading. It's built in the same spirit as the book — and it's the natural next question the book leaves open, since Chapter 1 stops right at the point where a cipher acquires a *repeating* key — but it should be cited as such.
 
Where a claim below is a direct quotation, it's marked with a page number and set off in a blockquote. Everything else is paraphrase or derivation.
 
---
 
## 1. Modular arithmetic
 
Everything here happens in **ℤ/26ℤ** — the integers 0 to 25, where counting past 25 wraps to 0.
 
Write letters as numbers: **A = 0, B = 1, …, Z = 25.**
 
> **a mod n** = the remainder when *a* is divided by *n*.
 
`28 mod 26 = 2`, `26 mod 26 = 0`, `(-1) mod 26 = 25`.
 
That last one deserves attention. Mathematically, `a mod n` is defined to land in `[0, n)`, so −1 mod 26 = 25. **Python agrees; C, Java and JavaScript do not** — they return −1, following the sign of the dividend. This is why `caesar.encrypt(text, -1)` needs no special case in this code and would need one in a port. If you rewrite this project in another language, that line is where the bug will be.
 
### The structure
 
The 26 shifts form a **cyclic group** under addition mod 26:
 
| Property | Meaning here |
|---|---|
| **Closure** | shift 20 then shift 10 = shift 4 (30 mod 26). Still a shift. |
| **Identity** | shift 0 does nothing |
| **Inverse** | shift *k* is undone by shift 26 − *k* |
| **Associativity** | the order you compose shifts in doesn't matter |
 
This is elegant, and it is exactly why the cipher is weak. The group is **small** (26 elements) and the operation is **linear** — and linear systems are solvable systems. Every classical cipher in this project is linear in ℤ/26ℤ. AES's S-box is deliberately non-linear, and that is not an aesthetic choice.
 
---
 
## 2. The Caesar cipher
 
### First, the cipher Caesar is a special case of
 
Before the book ever mentions Caesar, it teaches the **general substitution cipher**: pick *any* one-to-one mapping of the 26 letters to the 26 letters — not a shift, any rearrangement at all.
 
> "For instance, the pop group *ABBA* would be encrypted as `kddk`." — Example 1.1, p. 6
 
The key is the whole mapping table. Counting how many such tables exist is a straightforward "how many ways can you arrange things" argument, done one letter at a time: 26 choices for what A becomes, 25 remaining choices for B, 24 for C, and so on down to 1 choice for the last letter:
 
> "key space of the substitution cipher = 26 · 25 ··· 3 · 2 · 1 = 26! ≈ 2⁸⁸" — p. 8
 
That's roughly 4 × 10²⁶ possible keys — enough that the book itself notes *"even with hundreds of thousands of high-end PCs such a search would take several decades!"* (p. 8). Brute force is a genuine dead end here. And yet:
 
> "Good ciphers should hide the statistical properties of the encrypted plaintext. The ciphertext symbols should appear to be random. Also, a large key space alone is not sufficient for a strong encryption function." — "Lesson learned," §1.2.2, p. 9
 
The reason a 2⁸⁸ key space falls anyway: every occurrence of a given plaintext letter maps to the *same* ciphertext letter, everywhere. English letter frequencies are lumpy (E ≈ 13%, Z ≈ 0.07%), and that lumpiness survives the substitution untouched — it just gets relabeled. Counting ciphertext letters and matching frequency rank to the known English distribution recovers the key without trying any of the 26! tables. The book gives three concrete techniques for doing this (p. 8–9):
 
1. **Single-letter frequency** — most common ciphertext letter is probably standing in for E, second-most for T, and so on.
2. **Letter-pair patterns** — *"in English... the letter Q is almost always followed by a U"* (p. 8) — a digram regularity that survives substitution the same way single-letter frequency does.
3. **Word-shape spotting** — *"If we assume that word separators (blanks) have been found... one can often detect frequent short words such as THE, AND"* (p. 8), instantly revealing several letters at once.
This project's `analysis.frequency` module is a direct implementation of all three: `chi_squared`/`letter_frequencies` is technique 1, `bigram_fitness` is a generalization of technique 2 (a full pair-probability table rather than just "Q→U"), and `word_hit_rate` is technique 3.
 
### Where Caesar fits on this ladder
 
Caesar is not a different cipher — it's the substitution cipher with the mapping constrained to a single, very specific shape: "add a constant."
 
> "We now introduce another historical cipher, the shift cipher. It is actually **a special case of the substitution cipher** and has a very elegant mathematical description." — §1.4.3, p. 18
 
Collapsing the general 26!-sized key space down to "one number, 0–25" doesn't just make brute force *possible* — it makes it trivial. But note what it does *not* do: it doesn't touch the frequency-analysis weakness at all, because the same-letter-maps-to-same-letter property that the analytical attack exploits is completely unaffected by *which* substitution table you picked, shift-shaped or not. The book states this explicitly for the shift cipher:
 
> "There are two ways of attacking it: 1. Since there are only 26 different keys... one can easily launch a brute-force attack... 2. As for the substitution cipher, one can also use letter frequency analysis." — §1.4.3, p. 19
 
### Definition
 
For plaintext letter *x*, key *k* ∈ ℤ/26ℤ:
 
> **E_k(x) = (x + k) mod 26**
> **D_k(y) = (y − k) mod 26**
 
Correctness is one line: **D_k(E_k(x)) = ((x + k) − k) mod 26 = x mod 26 = x**.
 
### Worked example
 
Encrypt `HELLO` with k = 3:
 
| Letter | H | E | L | L | O |
|---|---|---|---|---|---|
| x | 7 | 4 | 11 | 11 | 14 |
| x + 3 | 10 | 7 | 14 | 14 | 17 |
| mod 26 | 10 | 7 | 14 | 14 | 17 |
| Result | **K** | **H** | **O** | **O** | **R** |
 
`KHOOR`. Note L → O twice: **identical inputs always give identical outputs.** That is the fingerprint the attack follows.
 
Encrypt `XYZ` with k = 3: 23 + 3 = 26 → **0** = A. The wrap in action.
 
### Complexity
 
| | Time | Space |
|---|---|---|
| Encrypt / decrypt | O(n) | O(1) working |
| Brute force | O(26n) = **O(n)** | O(n) |
 
The keyspace is a constant. Brute-forcing a Caesar cipher is *linear in the message length* — the key contributes nothing to the cost.
 
---
 
## 3. The Vigenère cipher
 
### Definition
 
Key = a word of *m* letters, k₀ … k_{m−1}. For the plaintext letter at **letter-position** *i* (counting letters only — punctuation does not advance the key):
 
> **E(xᵢ) = (xᵢ + k_{i mod m}) mod 26**
> **D(yᵢ) = (yᵢ − k_{i mod m}) mod 26**
 
Why punctuation must not advance the key: an attacker knows where the spaces are. If spaces consumed key letters, the key stream's alignment would be partly public. It costs nothing to skip them, so skip them.
 
### Worked example
 
```
i:        0  1  2  3  4  5  6  7  8  9 10 11
message:  A  T  T  A  C  K  A  T  D  A  W  N
x:        0 19 19  0  2 10  0 19  3  0 22 13
keyword:  L  E  M  O  N  L  E  M  O  N  L  E
k:       11  4 12 14 13 11  4 12 14 13 11  4
x+k:     11 23 31 14 15 21  4 31 17 13 33 17
mod 26:  11 23  5 14 15 21  4  5 17 13  7 17
cipher:   L  X  F  O  P  V  E  F  R  N  H  R
```
 
Look at positions 0 and 3: both are plaintext **A**. They encrypt to **L** and **O**. The fingerprint is broken — *at the level of single letters*.
 
And look at positions 2 and 7: both are plaintext **T**, four apart... but 2 mod 5 = 2 and 7 mod 5 = 2, **the same key position**. Both give **F**. That is the crack, visible in the worked example. Every *m* letters, the cipher repeats itself.
 
### Keyspace vs strength
 
| m | Keyspace 26^m | Naive brute force @ 10⁹/s | **Actual attack** |
|---|---|---|---|
| 3 | 17,576 | instant | 78 tests |
| 5 | 1.2 × 10⁷ | 0.01 s | 130 tests |
| 8 | 2.1 × 10¹¹ | 3.5 min | 208 tests |
| 12 | 9.5 × 10¹⁶ | ~3 years | **312 tests** |
| 20 | 2.0 × 10²⁸ | 10¹¹ years | 520 tests |
 
The final column is the whole story of this project.
 
### The one-time pad
 
Stop repeating the key — make it random, as long as the message, and never reuse it — and Vigenère becomes the **one-time pad**, which Shannon proved in 1949 is *information-theoretically* secure: the ciphertext gives an attacker with unlimited computing power exactly zero information about the plaintext, because every possible plaintext of that length is equally consistent with it.
 
So why isn't everything a one-time pad? Because you must securely deliver a key as long as everything you will ever send — which is the original problem, restated and made larger. Every gram of Vigenère's convenience is bought with security, and the one-time pad shows you the exchange rate.
 
---
 
## 4. Frequency analysis
 
### Naming the two attack families precisely
 
The book draws a sharp, formal line between two kinds of attack, and this project's "Break Caesar" command is actually a hybrid of both, worth naming precisely rather than calling the whole thing "brute force" loosely:
 
> "Cryptanalysis can be divided into **analytical attacks**, which exploit the internal structure of the encryption method, and **brute-force attacks**, which treat the encryption algorithm as a black box and test all possible keys." — §1.3.1, p. 10
 
A pure brute-force attack, formally, checks a candidate key against known plaintext:
 
> "A brute-force attack now checks for every kᵢ ∈ K if d_kᵢ(y) ?= x. If the equality holds, a possible correct key is found." — Def. 1.2.1, p. 7
 
`break_caesar()` doesn't do that — it needs no known plaintext at all. It combines cheap **exhaustive key enumeration** (trying all 26 shifts, which is only possible because Caesar's key space is tiny) with an **analytical** scoring step (χ², judging which of the 26 results looks like English) to automate what a human would otherwise do by eye. Kerckhoffs's Principle is what licenses treating the method as fully known in the first place:
 
> "A cryptosystem should be secure even if the attacker (Oscar) knows all details about the system, with the exception of the secret key." — Def. 1.3.1, p. 10
 
Described by **Al-Kindi** in Baghdad in the 9th century — the first recorded cryptanalytic technique in history, and the concrete ancestor of the analytical attack above. It still works on anything that preserves letter identity.
 
The premise: **English is lumpy, and both ciphers preserve the lumps.**
 
| Letter | Freq | | Letter | Freq |
|---|---|---|---|---|
| E | 12.70% | | M | 2.41% |
| T | 9.06% | | W | 2.36% |
| A | 8.17% | | F | 2.23% |
| O | 7.51% | | G | 2.02% |
| I | 6.97% | | Y | 1.97% |
| N | 6.75% | | P | 1.93% |
| S | 6.33% | | B | 1.49% |
| H | 6.09% | | V | 0.98% |
| R | 5.99% | | K | 0.77% |
| D | 4.25% | | J | 0.15% |
| L | 4.03% | | X | 0.15% |
| C | 2.78% | | Q | 0.10% |
| U | 2.76% | | Z | 0.07% |
 
**E appears 170× more often than Z.** Caesar slides this whole distribution sideways by *k* without changing its shape — so finding *k* means finding how far the shape moved.
 
---
 
## 5. The chi-squared test
 
We need a number for "does this look like English?"
 
> **χ² = Σ_{letters} (Oᵢ − Eᵢ)² / Eᵢ**
 
where Oᵢ is the observed count of letter *i*, and Eᵢ = (English frequency of *i*) × N.
 
Read it as a **penalty**. Zero is a perfect match; it grows with deviation.
 
**Why each piece is there:**
 
- *Why subtract?* We want the distance from English.
- *Why square?* Two reasons. Overshoots and undershoots would otherwise cancel — 10 too many E's and 10 too few T's would score 0. And squaring makes one big error cost more than several small ones, which is what we want: a single wildly wrong letter is stronger evidence than diffuse noise.
- *Why divide by Eᵢ?* Scale. Ten extra Z's (expected 0.4) is astonishing; ten extra E's (expected 63) is a Tuesday. Without the division, rare letters are ignored — and rare letters are the most informative ones.
### Worked intuition
 
100 letters of English. Expected E's: 12.7. Observed:
 
| Observed E | (O−E)²/E | Reads as |
|---|---|---|
| 13 | 0.007 | perfect |
| 8 | 1.7 | plausible |
| 0 | 12.7 | very suspicious |
| 30 | 23.0 | not English |
 
Sum that over all 26 letters and you have χ².
 
**Typical values (~500 letters):** English **10–40**; wrong Caesar shift **200–2000**. The signal is not subtle.
 
### Sample size
 
χ² needs Eᵢ ≳ 5 for the rare letters to be meaningful, which means **~40+ letters minimum**. Below that the test is noise wearing a lab coat — which is why the tool warns instead of answering.
 
---
 
## 6. The index of coincidence
 
Friedman, 1922. The single most useful number in classical cryptanalysis.
 
> **IC = Σ_{letters} nᵢ(nᵢ − 1) / N(N − 1)**
 
**Meaning:** pick two letters from the text at random, without replacement. IC is the probability they are the same letter.
 
**Derivation.** Ways to pick 2 identical *i*'s: nᵢ(nᵢ − 1). Ways to pick any 2: N(N − 1). Divide. That's all it is.
 
| Text | IC | Why |
|---|---|---|
| Random letters | 0.0385 = 1/26 | every letter equally likely |
| English | **0.0667** | so much of it is E, T, A, O |
| Caesar-encrypted English | **0.0667** | ← **unchanged** |
| Vigenère, key length 5 | ~0.045 | five distributions mixed |
| Vigenère, long key | → 0.0385 | approaches random |
 
### The property that matters
 
**IC is invariant under any relabelling of the alphabet.**
 
Look at the formula: it depends only on the *counts* nᵢ, never on which letter has which count. A Caesar shift permutes the labels. The multiset of counts is untouched. So the IC does not move.
 
This is why the IC sees straight through Caesar — and why one number answers "was this encrypted with one alphabet, or many?" The tool pins this down as a property test (`test_invariant_under_caesar_shift`), because it is the mathematical claim the whole Vigenère attack rests on.
 
### Finding the key length
 
Take every *m*-th letter of the ciphertext:
 
- **If *m* is the true key length:** every letter in that slice was shifted by the *same* key letter. The slice is Caesar-encrypted English, so its IC ≈ **0.067**.
- **If *m* is wrong:** the slice mixes several key letters, so its IC ≈ **0.038**.
Try m = 1, 2, 3, …, average the IC across the slices, and look for the jump.
 
```
m=1: 0.042    m=4: 0.045
m=2: 0.044    m=5: 0.068   ← the key is 5 letters
m=3: 0.049    m=6: 0.043
```
 
Multiples of the true length also score high (m=10 slices the same columns finer), so prefer the **shortest** length that scores well.
 
### Friedman's estimate
 
The same statistic, solved directly for *m*:
 
> **m ≈ 0.027N / ((N−1)·IC − 0.038N + 0.065)**
 
We use the per-slice method instead — it degrades more gracefully on short texts, and it is easier to *see*. Friedman's formula is a good next exercise (see PLANNING.md §16).
 
---
 
## 7. The Kasiski examination
 
Kasiski, 1863. (Babbage got there around 1854 and published nothing, which is why it isn't called the Babbage examination.)
 
If a plaintext word lands on the same part of the key twice, it encrypts identically both times:
 
```
position:   0         10        20
plaintext:  THE QUICK THE BROWN THE
key:        KEY KEYKE YKE YKEYK EYK
ciphertext: DLC AYSMO RRI ZBSUX XFO
                ↑              ↑
            "THE" at 0 and at 20: 20 is divisible by 3 → same encryption → DLC
            "THE" at 10: 10 is not divisible by 3 → different encryption → RRI
```
 
**Therefore: the distance between identical ciphertext chunks is usually a multiple of the key length.**
 
Method: find all repeated 3-grams, measure the distances, factor them, and count votes.
 
| Repeat | Distance | Factors ≤ 20 |
|---|---|---|
| `DLC` | 20 | 2, 4, 5, 10, 20 |
| `XFO` | 15 | 3, 5, 15 |
| `RRI` | 25 | 5 |
| | | **5 appears every time** |
 
**Why 3-grams and not 2?** In 1,000 letters, two-letter repeats occur constantly by chance; three-letter coincidences are rare enough to be signal. Mostly. Kasiski still votes for every factor of every distance, including chance ones — which is why the tool combines it with the IC rather than trusting either alone.
 
---
 
## 8. The full Vigenère attack
 
```
ciphertext (n letters, unknown key of length m)
    │
    ├─ Kasiski: repeated 3-grams → distances → factors → votes
    ├─ IC: for each m, average the IC of the m slices
    │
    └─→ combined ranking of candidate lengths
            │
            └─ for each of the top 3 lengths m:
                  split into m columns          ← each column is a CAESAR cipher
                  solve each column by χ²        ← 26 tests per column
                  reduce key to minimal period   ← LEMONLEMON → LEMON
                  score the plaintext by BIGRAM fitness
            │
            └─→ among near-equal candidates, take the SHORTEST key
                  → key, plaintext, confidence
```
 
### The cost
 
| Approach | Work for m = 12 |
|---|---|
| Brute force the keyspace | 26¹² ≈ 9.5 × 10¹⁶ |
| **Divide and conquer** | 26 × 12 = **312** |
 
> **O(26^m) → O(26m).** Exponential to linear.
 
The key never had 10¹⁶ worth of strength. It had 10¹⁶ worth of *appearance*, and the repetition let the attacker take the lock apart one tumbler at a time.
 
**This is the single most important idea in the project.** It is also not a historical curiosity: the same shape of failure — a large keyspace with exploitable internal structure — is behind real modern breaks. Structure, not size, is what gets you.
 
---
 
## 9. The bigram model
 
Single-letter statistics are not enough, and the reason is subtle enough to be worth the section.
 
The per-column solver **chooses shifts to minimise χ²**. That makes χ² a *fitted* quantity, not an independent measurement. And a 20-letter key has 20 free parameters where the true 5-letter key has 5 — so the longer key can always fit the letter counts at least as well, even when its plaintext is visible garbage.
 
Measured, on real ciphertext with true key `LEMON`:
 
| Length | Recovered key | χ² score (lower=better) | Plaintext |
|---|---|---|---|
| 5 | `LEMON` | 92.2 | perfect English |
| 20 | `LEMHGLEMONEXMONLXMON` | **77.9 — "better"** | **garbage** |
 
The scorer preferred the garbage. It was not wrong; it was answering a different question from the one we cared about.
 
### The fix: evidence the optimiser cannot manufacture
 
Letter **pairs** run *across* column boundaries. No choice of per-column shifts can arrange for TH, HE and IN to appear in quantity — those only show up if the text really is English.
 
> **fitness = (1/(n−1)) · Σᵢ log₁₀ P(cᵢcᵢ₊₁ | English)**
 
Higher is better; always negative (log of a probability). Averaged per pair so the scale is length-independent.
 
**Add-one (Laplace) smoothing:** P(pair) = (count + 1) / (total + 676). Without it, one unusual pair like `ZQ` sends the whole score to −∞ and a single oddity vetoes a correct answer.
 
**Calibration** (on prose *held out* of the corpus — scoring the training text would flatter the model and inflate every confidence figure the tool prints):
 
| Text | Fitness |
|---|---|
| English | **−2.30** |
| Random letters | **−3.25** |
| Vigenère ciphertext | −3.21 |
 
### The general lesson
 
**When a search optimises a metric, that metric stops being a fair judge of the search.**
 
That is not a cryptography insight. It is the same failure as training and testing on the same data, and it has a lot of names — overfitting, Goodhart's law, teaching to the test. The remedy is always the same shape: find evidence the optimiser had no hand in producing.
 
---
 
## Further reading
 
**Books**
- Simon Singh, *The Code Book* — the history, superbly told. Start here.
- Christof Paar & Jan Pelzl, *Understanding Cryptography* — the standard modern textbook.
- David Kahn, *The Codebreakers* — the definitive history, and enormous.
**Papers**
- Shannon, *Communication Theory of Secrecy Systems* (1949) — confusion, diffusion, and the one-time pad proof.
- Friedman, *The Index of Coincidence and Its Applications in Cryptography* (1922).
- Kasiski, *Die Geheimschriften und die Dechiffrir-kunst* (1863).
**Practice**
- [Cryptopals](https://cryptopals.com) — the best cryptography exercises there are. Set 1 covers this material and then keeps going.
- [CrypTool](https://www.cryptool.org) — visual, interactive, free.
**Modern crypto, when you're ready to leave the classics**
- [`cryptography`](https://cryptography.io) (Python) — the library to actually use.
- Aumasson, *Serious Cryptography* — the bridge from here to real systems.
 
