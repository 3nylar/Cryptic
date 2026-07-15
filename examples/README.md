# Sample files

Feed any of these to the tool. Nothing here needs a key — that is the point.

| File | Cipher | Key (don't peek) | What it demonstrates |
|---|---|---|---|
| `01_caesar_shift3.txt` | Caesar | 3 | The classic. Broken instantly. |
| `02_caesar_shift19.txt` | Caesar | 19 | Any shift is equally weak — the key value is irrelevant. |
| `03_vigenere_lemon.txt` | Vigenere | LEMON | Comfortable length; IC and Kasiski agree. |
| `04_vigenere_cryptography.txt` | Vigenere | CRYPTOGRAPHY | A 12-letter key (~10^17 keys) still falls in milliseconds. |
| `05_vigenere_short_hard.txt` | Vigenere | SPY | **Fails on purpose.** 12 letters is too little data; the tool reports low confidence instead of guessing. |
| `06_plaintext_sample.txt` | none | — | Plain English, for comparing statistics against ciphertext. |

## Try it

```bash
python main.py caesar-break -f examples/01_caesar_shift3.txt
python main.py vigenere-break -f examples/04_vigenere_cryptography.txt
python main.py stats -f examples/06_plaintext_sample.txt      # IC near 0.067
python main.py stats -f examples/04_vigenere_cryptography.txt # IC near 0.038
```

The last two commands are the most instructive pair in the repository: same
language, same author, and one number tells them apart.
