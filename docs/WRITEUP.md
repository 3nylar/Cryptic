# Breaking the Unbreakable

### A short report on classical ciphers, frequency analysis, and why key size is not security

_Accompanies the Cryptic project. Written for undergraduates meeting cryptography for the first time. ~2,400 words._

---

## 1. Introduction to classical cryptography

Encryption is old. The oldest examples we have are about four thousand years older than the mathematics needed to explain them, and for most of that history the discipline advanced the way cooking did: by people trying things and noticing what worked.

Four words carry the whole subject:

- **Plaintext** — the readable message.
- **Ciphertext** — the scrambled version.
- **Key** — the secret that turns one into the other.
- **Cipher** — the method itself.

_Encryption_ turns plaintext into ciphertext. _Decryption_ turns it back. The cipher is the recipe; the key is the ingredient only you and your correspondent have.

The distinction between the recipe and the ingredient is the most important idea in the field, and it took a surprisingly long time to state clearly. **Kerckhoffs's principle** (1883) says a cipher must remain secure even when the enemy knows exactly how it works — only the key is secret. Everything protecting your bank details today is published, argued over publicly, and attacked by anyone who fancies a go. Secrecy about the _method_ is not security. It is a delay, and a short one.

_Classical_ ciphers — the subject of this report — work on letters, and there are two families. **Transposition** ciphers shuffle the letters into a different order. **Substitution** ciphers replace each letter with another. This project concerns two substitution ciphers: Caesar, and Vigenère.

---

## 2. The Caesar cipher

Suetonius records that Julius Caesar shifted letters by three in his private correspondence, around 50 BC. A becomes D, B becomes E, and Z wraps around to C.

It worked. It is worth pausing on _why_ it worked: most of Caesar's enemies could not read. The cipher's security rested on illiteracy, not on mathematics — an early demonstration that being _unbroken_ and being _strong_ are different conditions.

Written as arithmetic, with A = 0 through Z = 25 and key _k_:

> **Encrypt: E(x) = (x + k) mod 26**
> **Decrypt: D(y) = (y − k) mod 26**

`mod 26` — "the remainder after dividing by 26" — is what wraps the alphabet. Z (25) shifted by 3 gives 28, and 28 mod 26 = 2 = C.

Notice that decryption is just encryption with the opposite shift. The same secret does both jobs, which makes this a **symmetric** cipher — as is AES, three thousand years later.

Notice also what the arithmetic reveals: **there are 26 keys.** One of them does nothing. A person can try all 26 by hand over a coffee; a computer does it before your finger leaves the Enter key. This is a **brute-force attack**, and a cipher only survives one if there are too many keys to try. Twenty-six is not too many.

But brute force is not even the interesting attack.

---

## 3. The Vigenère cipher

Described by Bellaso in 1553 and misattributed to Blaise de Vigenère ever since, this cipher fixes Caesar's obvious flaw. Instead of shifting everything by one number, you use a _keyword_, repeated under the message:

```
message:  A  T  T  A  C  K  A  T  D  A  W  N
keyword:  L  E  M  O  N  L  E  M  O  N  L  E
shift:   11  4 12 14 13 11  4 12 14 13 11  4
cipher:   L  X  F  O  P  V  E  F  R  N  H  R
```

Look at the A's in positions 0 and 3. The first becomes **L**; the second becomes **O**. **The same plaintext letter has encrypted to two different ciphertext letters.** This is what _polyalphabetic_ means, and it defeats the attack in the next section completely.

It also makes the keyspace enormous. A keyword of _m_ letters gives 26<sup>m</sup> possibilities: a twelve-letter key offers about 9.5 × 10<sup>16</sup> — ninety-five quadrillion. Brute-forcing that at a billion keys per second would take roughly three years.

For three hundred years it was considered unbreakable. It earned a nickname: _le chiffre indéchiffrable_.

The nickname was wrong, and the reason is visible in the diagram above if you know where to look. Positions 2 and 7 are both plaintext **T**, and both encrypt to **F** — because 2 and 7 are five apart, and the key is five letters long. **The key repeats.** Every _m_ letters, the cipher does exactly what it did before.

---

## 4. Frequency analysis

The attack that killed the Caesar cipher was described by **Al-Kindi**, in Baghdad, in the 9th century — the first recorded cryptanalytic technique in history. It rests on a single observation:

**English is lumpy.**

Count the letters in a page of ordinary English and you find E at about 12.7% and Z at about 0.07%. E appears roughly **170 times more often than Z**. That lumpiness is a fingerprint of the language, and here is the fatal part: **a Caesar cipher does not erase the fingerprint. It slides it sideways.** If E is the commonest plaintext letter and the shift is 3, then H is the commonest ciphertext letter. The shape is untouched; only its position moved.

So to break the cipher, find where the fingerprint went.

Doing this by eye works, but a computer needs a number. We use the **chi-squared test**:

> **χ² = Σ (observed − expected)² / expected**

Read it as a _penalty_. Decrypt with a candidate shift, count the letters, compare against English. A perfect match scores 0; the more the counts deviate, the higher it climbs. Squaring stops overshoots and undershoots from cancelling and makes one big error outweigh several small ones. Dividing by _expected_ is what keeps rare letters relevant — ten surplus Z's (expected: 0.4) is astonishing evidence, while ten surplus E's (expected: 63) is a Tuesday.

Real English, over five hundred letters, scores about 10–40. A wrong shift scores in the hundreds or thousands. The signal is not subtle:

```
Shift | Chi-sq | Plaintext preview
   11 |   28.4 | we hold these truths to be self evident…   ←
    4 |  412.7 | dl solk wolzl aybaoz av il zlsm lcpkly…
   17 |  489.1 | pr ahwe iaxlx mnkmal mh un lxey xobwxgm…
```

The attack needs no dictionary, no guessing and no luck — only about forty letters and some counting. It is _ciphertext-only_: it needs nothing but the encrypted message. That is the weakest thing an attacker can be handed, and it is enough.

Against Vigenère, though, this fails completely. Count the letters of a Vigenère ciphertext and the distribution is flat — several alphabets mixed together average out into mush. The fingerprint is gone.

Or rather: it is hidden. Which is not the same thing.

---

## 5. Why these ciphers are insecure today

### Finding the key length

Two methods, both from the 19th and early 20th centuries.

**Kasiski examination (1863).** If a word lands on the same part of the key twice, it encrypts identically both times. So repeated chunks in the ciphertext are usually not coincidence, and _the distance between them is a multiple of the key length_. Collect those distances, factor them, and the key length is the factor that keeps appearing.

**Index of coincidence (Friedman, 1922).** Pick two letters from a text at random. How often are they the same letter? In random gibberish, once in 26 (0.038). In English, far more often — 0.067 — because so much of the text is E, T, A and O.

The magic is what the IC _ignores_. The formula depends only on how often each letter occurs, never on which letter it is. Relabelling the alphabet cannot change it. **So Caesar-encrypting English leaves the IC at 0.067, exactly.** A single number sees straight through the cipher and answers a question frequency analysis cannot: _is this one alphabet, or many?_

And it does more. Take every _m_-th letter of a Vigenère ciphertext. If _m_ is the true key length, every letter in that slice was shifted by the _same_ key letter — so the slice is pure Caesar-encrypted English, and its IC leaps back to 0.067. If _m_ is wrong, the slice is still a mixture, and the IC stays near 0.038. Try every _m_ and watch for the jump:

```
m=1: 0.042    m=4: 0.045
m=2: 0.044    m=5: 0.068   ←
m=3: 0.049    m=6: 0.043
```

The key length has announced itself.

### The kill: divide and conquer

Here is the part that matters.

Once you know the key is five letters long, the ciphertext is not one hard problem. It is **five easy ones**. Letters 1, 6, 11, 16… were all shifted by the same key letter — that pile is a plain Caesar cipher. So is the pile starting at letter 2. And so on.

Solve each pile separately with chi-squared. Each answer is one letter of the key.

> **26<sup>m</sup> → 26 × m**

For a twelve-letter key: **95,428,956,661,682,176 → 312.**

Ninety-five quadrillion possibilities, and the attacker performs three hundred and twelve tests. On the tool built for this project, that takes about **forty milliseconds** — and it never tries a second key, because it never guesses. It measures.

The lock appeared to have twelve tumblers. It never did. It had twelve tumblers' worth of _appearance_, because the repeating key let the attacker pick them one at a time.

### The general failure

> **A large keyspace with exploitable internal structure is not a large keyspace.**

This is the sentence to take away. "26<sup>12</sup> is a huge number" is true and irrelevant. The keyspace was never the obstacle; the _structure_ was the vulnerability, and structure is what an attacker eats.

The failure is not a historical curiosity either. The same shape — impressive numbers, exploitable internals — recurs in modern breaks. WEP had a 104-bit key and fell in minutes, not because 2<sup>104</sup> is small but because the way it used its key leaked information. Big numbers are necessary. They have never been sufficient.

### Everything else that is wrong with them

**Known-plaintext.** Guess one word and Caesar is finished; guess _m_ letters and Vigenère hands over its key by subtraction. This is not exotic: `Dear Sir`, a date, a fixed header. Breaking Enigma leaned on the reasonable guess that a German weather report contained _WETTER_.

**Chosen-plaintext.** If you can get the target to encrypt text you choose, encrypt `AAAA…`. For Vigenère, the ciphertext **is** the key, repeated. Total, immediate break.

**Dictionary attacks.** Vigenère keys are words, because humans must remember them. `LEMON`, `SECRET`, `PASSWORD`. A hundred-thousand-word list beats 26<sup>m</sup> for any key a person actually chose — and this has not aged into irrelevance. The modern version is a password list, and it is still how most accounts fall.

**Computers.** Caesar was safe against people who could not read. Vigenère was safe against people doing arithmetic with a quill. Both assumptions expired, and attacker capability only ever increases — which is why "nobody has broken it yet" is not a security claim.

---

## 6. Comparison with modern encryption

|                          | Caesar          | Vigenère       | AES-256               |
| ------------------------ | --------------- | -------------- | --------------------- |
| Year                     | 50 BC           | 1553           | 2001                  |
| Keyspace                 | 26              | 26<sup>m</sup> | 1.2 × 10<sup>77</sup> |
| **Work to break**        | **26**          | **26 × m**     | **2<sup>256</sup>**   |
| Works on                 | letters         | letters        | 128-bit blocks        |
| Diffusion                | none            | none           | yes                   |
| Non-linear               | no              | no             | yes                   |
| Same input → same output | always          | always         | no                    |
| Fingerprint              | full            | partial        | none detectable       |
| Status                   | broken (9th c.) | broken (1863)  | unbroken              |

AES has five things these lack, and each maps onto something we watched fail:

1. **Confusion and diffusion** (Shannon, 1949). Flip one plaintext bit and about half the output bits change, unpredictably. Caesar changes exactly one letter — the structure survives, and the structure is the whole attack surface.
2. **Rounds.** Fourteen of them, each substituting, permuting and mixing. Classical ciphers apply one simple operation once.
3. **Non-linearity.** AES's S-box is deliberately non-linear. Caesar and Vigenère are _linear_ in ℤ/26ℤ, and linear systems are solvable systems.
4. **Adversarial public design.** AES was chosen by open competition — five years, fifteen candidates, the world's cryptanalysts attacking each one. Kerckhoffs's principle, industrialised.
5. **Semantic security.** Encrypt the same message twice, get different ciphertext. Vigenère gives the same answer every time, forever.

**RSA** is different in kind. It is _asymmetric_: a public key encrypts, a private key decrypts, so two strangers can communicate securely without ever having met — which no classical cipher can do at any key size.

And a caution: even AES fails when used badly. Encrypt an image with AES in ECB mode and you can still see the picture, because identical blocks encrypt identically. That is Vigenère's repeating-key failure, wearing a modern suit. The tool is only as good as the hands.

---

## 7. Lessons learned

**Key size is not security.** A twelve-letter Vigenère key offers 10<sup>17</sup> possibilities and dies in forty milliseconds. If you remember one sentence from this report, this is it.

**Structure is what gets you.** Every attack here exploited _pattern_, not smallness: repeated letters, repeated keys, the shape of a language. AES's design is best understood as three decades of learning to destroy pattern.

**Statistics need data, and honesty needs both.** Given twelve letters, the tool built for this project reports low confidence and says why. That is not a limitation, it is the point: cryptanalysis is measurement, and a measurement without enough data is a guess wearing a lab coat.

**Building the attack taught more than reading about it.** One lesson was not on the syllabus. The Vigenère breaker was, at first, quietly wrong: it preferred a twenty-letter key over the true five-letter one, because a longer key has more free parameters and more parameters always fit the letter counts better — even when the plaintext is visible garbage. The scorer wasn't broken. It was answering a different question from the one that mattered, and it had been _optimised against_, so it could no longer judge fairly.

The fix was to find evidence the search could not manufacture: letter _pairs_ (TH, HE, IN) run across the columns, so no choice of per-column shifts can fake them. The general principle — **when a search optimises a metric, that metric stops being a fair judge of the search** — is not a cryptography idea at all. It is overfitting, Goodhart's law, teaching to the test. It was found by reading the output instead of trusting the score, which may be the most transferable thing in this project.

**Never write your own crypto.** Not because you are not clever. Bellaso was clever. Three centuries of cryptographers were clever, and all of them were wrong about _le chiffre indéchiffrable_. Use `cryptography`, libsodium, or your platform's audited primitives — AES-GCM or ChaCha20-Poly1305, keys from a KDF.

---

## 8. Conclusion

Two ciphers, four hundred years apart, both broken by the same idea: **language leaves fingerprints, and neither cipher could erase them.** Caesar left the fingerprint intact and merely moved it. Vigenère smeared it — and then repeated its key, which let an attacker un-smear it one column at a time.

The Vigenère cipher is the more instructive failure, because it does not look like a failure. It looks like a success: an enormous keyspace, a genuine defeat of the obvious attack, three hundred years of unbroken service. And it dies in milliseconds. Everything that made it _convenient_ — a short key, a memorable word, a repeating pattern — is exactly what killed it. The one version that cannot be broken, the one-time pad, is also very nearly unusable.

That trade never went away. It is the same trade every system makes today, and the reason security is hard is that the convenient thing and the safe thing are so rarely the same thing.

Which is why the exercise is worth doing rather than reading about. Anyone can be told that a big keyspace is not enough. Encrypting your own message with a twelve-letter key, handing a machine nothing but the ciphertext, and watching your words come back forty milliseconds later is a different kind of knowing — and it is the kind that survives into a career.

---

### References

Al-Kindi (9th c.), _Manuscript on Deciphering Cryptographic Messages_ · Kasiski, F. (1863), _Die Geheimschriften und die Dechiffrir-kunst_ · Friedman, W. (1922), _The Index of Coincidence and Its Applications in Cryptography_ · Kerckhoffs, A. (1883), "La cryptographie militaire", _Journal des sciences militaires_ · Shannon, C. (1949), "Communication Theory of Secrecy Systems", _Bell System Technical Journal_ · NIST (2001), _FIPS 197: Advanced Encryption Standard_ · Singh, S. (1999), _The Code Book_ · Paar, C. & Pelzl, J. (2010), _Understanding Cryptography_
