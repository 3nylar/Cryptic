# Cryptic — website

An interactive, beginner-friendly explainer for the Caesar and Vigenère ciphers,
with a **working code-breaker that runs entirely in the browser** (no server).
It defines each cipher in plain language, compares them, shows why they are
insecure, and lets visitors try the real tool live.

## Deploy it (pick one — all free)

This is a static site: just `index.html` and a few assets. Nothing to build.

### GitHub Pages

1. Create a repo and upload these files (or put them in a `/docs` folder).
2. Repo **Settings → Pages → Source: main branch**.
3. Your site is live at `https://<you>.github.io/<repo>/` in a minute.

### Netlify / Vercel

Drag this folder onto the Netlify dashboard, or `vercel` from inside it. Done.

### Test locally first

```bash
python -m http.server 8000     # then open http://localhost:8000
```

(Opening index.html directly with file:// also works, but a local server is closer to production.)

## One thing to set: your repo link

Open **`config.js`** and change the one URL to your GitHub repository:

```js
window.CIPHER_BREAKER_CONFIG = {
  repoUrl: "https://www.github.com/3nylar/Cryptic",
};
```

Every "Clone" / "View on GitHub" button and the `git clone` command on the page
update automatically. That's the only edit needed.

## Files

| File          | What it is                                                                          |
| ------------- | ----------------------------------------------------------------------------------- |
| `index.html`  | The whole page (HTML + CSS inline)                                                  |
| `engine.js`   | The ciphers + breakers, ported to JavaScript — this is what makes the terminal work |
| `app.js`      | Page behaviour: the demos and the live terminal                                     |
| `config.js`   | **Edit this** — your repo URL                                                       |
| `cryptic.zip` | The full Python project, for the "Download" button                                  |
| `.nojekyll`   | Tells GitHub Pages to serve files as-is                                             |

## How the in-browser tool works

The terminal is not a mock-up. `engine.js` is a faithful port of the Python
project's cipher and cryptanalysis code — Caesar and Vigenère encrypt/decrypt,
frequency analysis, index of coincidence, Kasiski examination, per-column
solving, and the bigram model. Everything runs on the visitor's device; nothing
is ever sent anywhere.
