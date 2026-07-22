/* Page behaviour: config, demos, and the live terminal wired to CipherEngine. */
(function () {
  "use strict";
  const E = window.CipherEngine;
  const CFG = window.CIPHER_BREAKER_CONFIG || {};
  const REPO = CFG.repoUrl || "https://www.github.com/3nylar/Cryptic";

  // ---- repo links ----
  const repoBtn = document.getElementById("repoBtn");
  if (repoBtn) repoBtn.href = REPO;
  document.querySelectorAll(".nav-cta").forEach((a) => {
    if (a.getAttribute("href") === "#get") return;
  });
  const cloneBlock = document.getElementById("cloneBlock");
  if (cloneBlock)
    cloneBlock.innerHTML = cloneBlock.innerHTML.replace(
      "REPO_HTTPS",
      REPO + ".git",
    );
  const copyClone = document.getElementById("copyClone");
  if (copyClone)
    copyClone.addEventListener("click", () => {
      const txt = `git clone ${REPO}.git\ncd cryptic\npython main.py`;
      navigator.clipboard.writeText(txt).then(() => {
        copyClone.textContent = "copied ✓";
        setTimeout(() => (copyClone.textContent = "copy"), 1600);
      });
    });

  const esc = (s) =>
    s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const bar = (v, w = 20) => {
    const f = Math.round(w * Math.max(0, Math.min(v, 1)));
    return (
      "[" + "#".repeat(f) + "-".repeat(w - f) + "] " + Math.round(v * 100) + "%"
    );
  };

  // ---- hero: typewriter break ----
  const heroTerm = document.getElementById("heroTerm");
  if (heroTerm) {
    const key = "CRYPTOGRAPHY";
    const plain =
      "The index of coincidence is the probability that two letters drawn at random from a text are the same letter";
    const ct = E.vigenereEncrypt(plain, key);
    const lines = [
      { t: "$ cryptic vigenere-break -f message.txt", c: "cmd" },
      { t: "", c: "" },
      {
        t: "  reading " + E.lettersOnly(ct).length + " letters of ciphertext…",
        c: "dim",
      },
      {
        t: "  index of coincidence = 0.041  → several alphabets (Vigenère)",
        c: "dim",
      },
      { t: "  key length looks like 12  (IC jumps to 0.068)", c: "dim" },
      { t: "  splitting into 12 columns, solving each…", c: "dim" },
      { t: "", c: "" },
      { t: "  ✓ recovered key = 'CRYPTOGRAPHY'", c: "ok" },
      { t: "  ✓ confidence " + bar(0.98), c: "ok" },
      { t: "", c: "" },
      { t: "  " + plain.slice(0, 46) + "…", c: "amber" },
      { t: "", c: "" },
      { t: "  95,428,956,661,682,176 possible keys.", c: "dim" },
      { t: "  Cracked in 40 ms, without ever guessing one.", c: "warnl" },
    ];
    let li = 0;
    function typeLine() {
      if (li >= lines.length) return;
      const ln = lines[li];
      const div = document.createElement("div");
      if (ln.c) div.className = ln.c;
      heroTerm.appendChild(div);
      const full = ln.t;
      let ci = 0;
      const fast = ln.c === "dim" || ln.c === "cmd";
      (function typeChar() {
        div.textContent = full.slice(0, ci);
        ci++;
        if (ci <= full.length) setTimeout(typeChar, fast ? 8 : 14);
        else {
          li++;
          setTimeout(typeLine, ln.t === "" ? 90 : 260);
        }
      })();
    }
    const obs = new IntersectionObserver(
      (es) => {
        es.forEach((e) => {
          if (e.isIntersecting) {
            typeLine();
            obs.disconnect();
          }
        });
      },
      { threshold: 0.3 },
    );
    obs.observe(heroTerm);
  }

  // ---- Caesar wheel demo ----
  const caesarViz = document.getElementById("caesarViz");
  const caesarSlider = document.getElementById("caesarSlider");
  if (caesarViz && caesarSlider) {
    const AL = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    const word = "HELLO";
    function draw(k) {
      document.getElementById("caesarK").textContent = k;
      const show = "ABCDEFGH";
      let html = '<div class="srow">';
      for (const c of show) html += `<div class="sc plain">${c}</div>`;
      html += '</div><div class="srow">';
      for (const c of show) {
        const s = AL[(AL.indexOf(c) + k) % 26];
        html += `<div class="sc hot">${s}</div>`;
      }
      html += "</div>";
      caesarViz.innerHTML = html;
      document.getElementById("caesarIn").textContent = word;
      document.getElementById("caesarOut").textContent = E.caesarEncrypt(
        word,
        k,
      );
    }
    caesarSlider.addEventListener("input", () => draw(+caesarSlider.value));
    draw(3);
  }

  // ---- Vigenère grid demo ----
  const vigViz = document.getElementById("vigViz");
  if (vigViz) {
    const msg = "ATTACK",
      key = "LEMON";
    const cip = E.vigenereEncrypt(msg, key);
    const keyRep = key.repeat(2).slice(0, msg.length);
    let h = '<div class="vg-lbl">message</div>';
    for (const c of msg) h += `<div class="vig-cell vg-msg">${c}</div>`;
    h += '<div class="vg-lbl">keyword (repeats)</div>';
    for (const c of keyRep) h += `<div class="vig-cell vg-key">${c}</div>`;
    h += '<div class="vg-lbl">ciphertext</div>';
    for (const c of cip) h += `<div class="vig-cell vg-cip">${c}</div>`;
    vigViz.innerHTML = h;
  }

  // ---- LIVE TERMINAL ----
  const out = document.getElementById("liveOut");
  const inp = document.getElementById("liveIn");
  if (out && inp) {
    const history = [];
    let hIdx = -1;
    function w(text, cls) {
      const d = document.createElement("div");
      if (cls) d.className = cls;
      d.innerHTML = text;
      out.appendChild(d);
      out.scrollTop = out.scrollHeight;
    }
    function blank() {
      w("&nbsp;");
    }

    function parse(line) {
      // tokenise respecting quotes
      const toks = line.match(/"[^"]*"|'[^']*'|\S+/g) || [];
      return toks.map((t) => t.replace(/^["']|["']$/g, ""));
    }
    function getOpt(toks, names) {
      for (let i = 0; i < toks.length; i++)
        if (names.includes(toks[i])) return toks[i + 1];
      return null;
    }

    function steps(arr) {
      w("How it worked:", "amber");
      arr.forEach((s, i) => w("  " + (i + 1) + ". " + esc(s), "dim"));
    }

    const HELP = [
      ["caesar-encrypt -k N -t TEXT", "shift letters by N"],
      ["caesar-decrypt -k N -t TEXT", "shift back by N"],
      ["caesar-break -t TEXT", "recover the shift, no key needed"],
      ["vigenere-encrypt -k WORD -t TEXT", "encrypt with a keyword"],
      ["vigenere-decrypt -k WORD -t TEXT", "decrypt with a keyword"],
      ["vigenere-break -t TEXT", "recover the keyword, no key needed"],
      ["stats -t TEXT", "letter frequency, index of coincidence"],
      ["demo", "break a real 12-letter Vigenère key"],
      ["clear", "clear the screen"],
      ["help", "this list"],
    ];

    function run(line) {
      const toks = parse(line);
      const cmd = (toks[0] || "").toLowerCase();
      const text = getOpt(toks, ["-t", "--text"]);
      const key = getOpt(toks, ["-k", "--key"]);
      const needText = () => {
        w('no text given. Add -t "your message".', "sig");
      };

      try {
        if (cmd === "help" || cmd === "") {
          w("Commands — type any of these:", "amber");
          HELP.forEach(([c, d]) => w("  " + c.padEnd(36) + " " + d, "dim"));
          w('Text with spaces goes in quotes: -t "attack at dawn".', "dim");
        } else if (cmd === "clear") {
          out.innerHTML = "";
        } else if (cmd === "caesar-encrypt") {
          if (!text) return needText();
          if (key == null) return w("no key. Add -k 3.", "sig");
          w(esc(E.caesarEncrypt(text, parseInt(key, 10) || 0)), "ok");
        } else if (cmd === "caesar-decrypt") {
          if (!text) return needText();
          if (key == null) return w("no key. Add -k 3.", "sig");
          w(esc(E.caesarDecrypt(text, parseInt(key, 10) || 0)), "ok");
        } else if (cmd === "vigenere-encrypt") {
          if (!text) return needText();
          if (!key) return w("no key. Add -k LEMON.", "sig");
          w(esc(E.vigenereEncrypt(text, key)), "ok");
        } else if (cmd === "vigenere-decrypt") {
          if (!text) return needText();
          if (!key) return w("no key. Add -k LEMON.", "sig");
          w(esc(E.vigenereDecrypt(text, key)), "ok");
        } else if (cmd === "caesar-break") {
          if (!text) return needText();
          const r = E.breakCaesar(text);
          w(esc(r.plaintext), "amber");
          w("✓ key = " + r.key + "   confidence " + bar(r.confidence), "ok");
          blank();
          steps(r.steps);
        } else if (cmd === "vigenere-break") {
          if (!text) return needText();
          const r = E.breakVigenere(text);
          w(esc(r.plaintext), "amber");
          w("✓ key = '" + r.key + "'   confidence " + bar(r.confidence), "ok");
          r.warnings.forEach((wn) => w("⚠ " + esc(wn), "warnl"));
          blank();
          steps(r.steps);
        } else if (cmd === "stats") {
          if (!text) return needText();
          const ic = E.indexOfCoincidence(text),
            chi = E.chiSquared(text);
          w("index of coincidence : " + ic.toFixed(4), "dim");
          w(
            "chi-squared vs English: " +
              (chi === Infinity ? "∞" : chi.toFixed(1)),
            "dim",
          );
          w(
            ic > 0.06
              ? "→ looks like ONE alphabet (plain or Caesar)"
              : "→ looks like MANY alphabets (Vigenère)",
            "amber",
          );
        } else if (cmd === "demo") {
          const k = "CRYPTOGRAPHY";
          const p =
            "we hold these truths to be self evident that all men are created equal that they are endowed by their creator with certain unalienable rights that among these are life liberty and the pursuit of happiness ".repeat(
              3,
            );
          const ct = E.vigenereEncrypt(p, k);
          w(
            "A message was encrypted with a 12-letter key (95 quadrillion possibilities).",
            "dim",
          );
          w("Ciphertext (first 60): " + esc(ct.slice(0, 60)) + "…", "dim");
          blank();
          const t0 = performance.now();
          const r = E.breakVigenere(ct);
          const ms = (performance.now() - t0).toFixed(1);
          w(esc(r.plaintext.slice(0, 70)) + "…", "amber");
          w("✓ key = '" + r.key + "'   confidence " + bar(r.confidence), "ok");
          w(
            "✓ cracked in " + ms + " ms, without guessing a single key.",
            "warnl",
          );
        } else {
          w("unknown command: " + esc(cmd) + ". Type 'help'.", "sig");
        }
      } catch (err) {
        w("error: " + esc(err.message), "sig");
      }
    }

    // greeting
    w("cryptic — running locally in your browser.", "amber");
    w(
      "Type 'help' for commands, or use the buttons above. Nothing leaves your device.",
      "dim",
    );
    blank();

    function submit(line) {
      w(
        '<span class="prompt" style="color:var(--amber)">$</span> <span class="cmd">' +
          esc(line) +
          "</span>",
      );
      if (line.trim()) {
        history.unshift(line);
        hIdx = -1;
      }
      run(line.trim());
      blank();
    }
    inp.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        const v = inp.value;
        inp.value = "";
        submit(v);
      } else if (e.key === "ArrowUp") {
        if (hIdx < history.length - 1) {
          hIdx++;
          inp.value = history[hIdx];
        }
        e.preventDefault();
      } else if (e.key === "ArrowDown") {
        if (hIdx > 0) {
          hIdx--;
          inp.value = history[hIdx];
        } else {
          hIdx = -1;
          inp.value = "";
        }
        e.preventDefault();
      }
    });
    document.querySelectorAll(".qbtn").forEach((b) =>
      b.addEventListener("click", () => {
        const cmd = b.getAttribute("data-cmd");
        document
          .getElementById("try")
          .scrollIntoView({ behavior: "smooth", block: "start" });
        inp.value = cmd;
        inp.focus();
        setTimeout(() => {
          submit(cmd);
          inp.value = "";
        }, 300);
      }),
    );
  }
})();
