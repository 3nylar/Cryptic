/* ============================================================================
   Cryptic — browser engine
   A faithful JavaScript port of the Python project's cipher and cryptanalysis
   code, so the terminal on this page runs the real algorithms with no server.
   Encrypt, decrypt and break Caesar & Vigenere ciphers entirely client-side.
   ========================================================================== */
(function (global) {
  "use strict";

  const A = 26;
  const UP = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  const isLetter = (c) => (c >= "A" && c <= "Z") || (c >= "a" && c <= "z");
  const toIdx = (c) => c.toUpperCase().charCodeAt(0) - 65;
  const toChar = (i, up) =>
    String.fromCharCode((up ? 65 : 97) + (((i % A) + A) % A));
  const keepCase = (src, ch) =>
    src === src.toUpperCase() ? ch.toUpperCase() : ch.toLowerCase();
  const lettersOnly = (t) =>
    t
      .split("")
      .filter(isLetter)
      .map((c) => c.toUpperCase())
      .join("");

  const ENGLISH_FREQ = {
    A: 0.08167,
    B: 0.01492,
    C: 0.02782,
    D: 0.04253,
    E: 0.12702,
    F: 0.02228,
    G: 0.02015,
    H: 0.06094,
    I: 0.06966,
    J: 0.00153,
    K: 0.00772,
    L: 0.04025,
    M: 0.02406,
    N: 0.06749,
    O: 0.07507,
    P: 0.01929,
    Q: 0.00095,
    R: 0.05987,
    S: 0.06327,
    T: 0.09056,
    U: 0.02758,
    V: 0.00978,
    W: 0.0236,
    X: 0.0015,
    Y: 0.01974,
    Z: 0.00074,
  };
  const ENGLISH_IOC = 0.0667,
    RANDOM_IOC = 1 / A;
  const ENGLISH_FITNESS = -2.3,
    RANDOM_FITNESS = -3.25;
  const COMMON = new Set(
    (
      "the be to of and a in that have i it for not on with he as you do at " +
      "this but his by from they we say her she or an will my one all would there their what so up " +
      "out if about who get which go me when make can like time no just him know take people into " +
      "year your good some could them"
    ).split(" "),
  );

  // ---- Caesar -------------------------------------------------------------
  function caesarShift(text, k, sign) {
    let out = "";
    for (const c of text)
      out += isLetter(c) ? keepCase(c, toChar(toIdx(c) + sign * k)) : c;
    return out;
  }
  const caesarEncrypt = (t, k) => caesarShift(t, ((k % A) + A) % A, 1);
  const caesarDecrypt = (t, k) => caesarShift(t, ((k % A) + A) % A, -1);

  // ---- Vigenere -----------------------------------------------------------
  function vigenereApply(text, key, sign) {
    key = key.toUpperCase().replace(/[^A-Z]/g, "");
    if (!key) throw new Error("key must contain at least one letter");
    const shifts = key.split("").map(toIdx);
    let out = "",
      pos = 0;
    for (const c of text) {
      if (isLetter(c)) {
        out += keepCase(
          c,
          toChar(toIdx(c) + sign * shifts[pos % shifts.length]),
        );
        pos++;
      } else out += c;
    }
    return out;
  }
  const vigenereEncrypt = (t, k) => vigenereApply(t, k, 1);
  const vigenereDecrypt = (t, k) => vigenereApply(t, k, -1);

  // ---- Statistics ---------------------------------------------------------
  function letterCounts(text) {
    const c = {};
    for (const L of UP) c[L] = 0;
    for (const ch of lettersOnly(text)) c[ch]++;
    return c;
  }
  function chiSquared(text) {
    const c = letterCounts(text);
    let n = 0;
    for (const L of UP) n += c[L];
    if (n === 0) return Infinity;
    let s = 0;
    for (const L of UP) {
      const e = ENGLISH_FREQ[L] * n,
        d = c[L] - e;
      s += (d * d) / e;
    }
    return s;
  }
  function indexOfCoincidence(text) {
    const c = letterCounts(text);
    let n = 0;
    for (const L of UP) n += c[L];
    if (n < 2) return 0;
    let num = 0;
    for (const L of UP) num += c[L] * (c[L] - 1);
    return num / (n * (n - 1));
  }
  function wordHitRate(text) {
    const toks = text
      .split(/\s+/)
      .map((w) => w.replace(/[^a-zA-Z]/g, "").toLowerCase())
      .filter(Boolean);
    if (!toks.length) return 0;
    return toks.filter((t) => COMMON.has(t)).length / toks.length;
  }
  function englishScore(text) {
    const base = chiSquared(text);
    return base === Infinity ? base : base * (1 - 0.3 * wordHitRate(text));
  }
  function confidence(best, runnerUp) {
    if (best === Infinity) return 0;
    const absolute = 1 / (1 + Math.max(best, 0) / 60);
    if (runnerUp == null || runnerUp === Infinity || best <= 0)
      return Math.min(absolute, 1);
    const margin = (runnerUp - best) / Math.max(runnerUp, 1e-9);
    return Math.min(
      0.5 * absolute + 0.5 * Math.max(0, Math.min(margin * 1.5, 1)),
      1,
    );
  }

  // ---- Bigram model (built once from the embedded corpus) -----------------
  const CORPUS = `A language leaves fingerprints everywhere, and not only in the letters that appear most often. English also has strong habits about which letters follow which. After a Q there is almost always a U. After a T there is very often an H, and the pair TH is one of the most common in the whole language. The letter J is rarely followed by anything except a vowel, and the pair ZX does not occur in ordinary writing at all. These habits are what a machine can measure. This file is a small sample of ordinary English prose. The program reads it once when it starts and counts how often each pair of letters occurs. Those counts become a rough model of the language, and the model is used to judge whether a piece of recovered text reads like English or merely looks like English when you squint at a bar chart of its letters. The distinction matters more than it might seem. Suppose you are trying to break a message and you allow yourself a great many adjustable settings. With enough settings you can always make the letter counts come out looking reasonable, in the same way that a tailor with enough pins can make any coat hang straight on any person. The coat still will not fit when the person moves. A test that looks at pairs of letters is harder to fool, because the pairs run across the seams. Here then is a stretch of plain writing on no particular subject, chosen only because it uses common words in common arrangements. The morning train was late again, and the platform filled slowly with people who had learned not to expect very much from the timetable. An older man read his newspaper standing up, turning the pages with one hand. Two students argued quietly about a film they had both seen and remembered differently. A woman with a large bag of shopping looked down the empty line and sighed, and then looked again, as though the second glance might be luckier than the first. When the train finally arrived it was crowded, and everybody found a way to fit. This is a thing people do without being asked. They turn sideways, they lift their bags, they make room. Nobody thanks anybody, and yet the whole small arrangement works, day after day, in cities all over the world. Consider now how a house is built. First there is a plan, drawn on paper, and the plan is wrong in several places, because every plan is. Then the ground is dug and the foundation is poured, and the concrete takes a week to cure while nothing appears to happen. The walls go up quickly after that, which is why people who watch a building think the early weeks were wasted. They were not. A house with a poor foundation will stand for a while and then it will not, and the failure will seem sudden even though it was decided long before. Software is much the same, and so is an argument, and so is a friendship. Consider the sea. It is not a single thing but a great many things doing different work at different depths. The top few feet are bright and warm and busy, and almost every picture ever taken of the ocean is a picture of that thin layer. Below it the light fails quickly. By a few hundred feet down the colour red has gone entirely, and everything that was red appears black or grey. Further down still the water is cold and dark and under enormous pressure, and yet it is not empty. Animals live there that have never seen the sun, and they make their own light instead, in small blue and green sparks that travel a surprising distance in water so clear. Reading is a strange skill when you look at it closely. The marks on this page are nothing but shapes, and yet you are not seeing shapes. The words arrive as meaning, already unpacked, faster than you could describe how it happens. A child learning to read must sound out each letter, slowly and painfully, and then one day the sounding out disappears and never comes back. Nobody remembers the day it happened to them. Mathematics has a similar trick in it. A student first learns that adding is counting, then that multiplying is repeated adding, then that a great deal of what looked like separate rules was really one rule wearing different hats. The moment when the rules collapse into one idea feels less like learning and more like having been told a secret. Weather is worth thinking about because it is the plainest example of a system that is perfectly understood and still cannot be predicted very far ahead. Every rule the air follows is known. Air moves from high pressure toward low pressure, warm air rises, water vapour carries heat and releases it when it condenses. There is no mystery in any single step. And yet a forecast three days out is good, a forecast ten days out is a guess, and a forecast for a month from now is not really a forecast at all. Small differences grow. This is not a failure of the science but a fact about the world. A good question is worth more than a good answer, because an answer closes a door and a question opens one. Teachers know this and still find it hard to practise, since a class that is asking questions is a class that is not moving through the material. Every hour spent on a question is an hour not spent on the syllabus. The best teachers accept the trade and the worst pretend there is no trade. Old tools deserve respect even after they stop being useful. A stone axe is not a good axe by any modern standard. It is heavy, it is dull, it must be resharpened constantly, and a steel axe of the same size will outwork it in every way. But somebody thought of it first, and before that nobody had thought of it at all, and that first thought is worth more than any improvement made since. The people who invented these things were not less clever than we are. They simply had less to build on, and they built anyway. Every craft has its own version of this lesson. The carpenter keeps a hand plane in the drawer long after buying the electric one. The cook keeps a knife that was old when they were young. These things are not kept for use, or not only for use. They are kept because a person who forgets where the work came from will eventually make worse work. Letters, numbers, tools, and habits: all of them are ways of storing what someone else already figured out, so that we do not each have to begin at the beginning. That is what writing is for, in the end. Somebody worked something out, and wrote it down, and now you know it too, and it cost you an afternoon instead of a life.`;
  let BIGRAM = null,
    FLOOR = -6;
  function bigramModel() {
    if (BIGRAM) return BIGRAM;
    const letters = lettersOnly(CORPUS),
      counts = {};
    for (let i = 0; i < letters.length - 1; i++) {
      const p = letters[i] + letters[i + 1];
      counts[p] = (counts[p] || 0) + 1;
    }
    let total = A * A;
    for (const k in counts) total += counts[k];
    const m = {};
    for (const a of UP)
      for (const b of UP)
        m[a + b] = Math.log10(((counts[a + b] || 0) + 1) / total);
    FLOOR = Math.log10(1 / total);
    BIGRAM = m;
    return m;
  }
  function bigramFitness(text) {
    const m = bigramModel(),
      letters = lettersOnly(text);
    if (letters.length < 2) return RANDOM_FITNESS;
    let s = 0;
    for (let i = 0; i < letters.length - 1; i++)
      s += m[letters[i] + letters[i + 1]] ?? FLOOR;
    return s / (letters.length - 1);
  }
  function fitnessConfidence(best, runnerUp) {
    const span = ENGLISH_FITNESS - RANDOM_FITNESS;
    const absolute = Math.max(0, Math.min((best - RANDOM_FITNESS) / span, 1));
    if (runnerUp == null) return absolute;
    const margin = Math.max(0, Math.min((best - runnerUp) / (0.5 * span), 1));
    return Math.min(0.6 * absolute + 0.4 * margin, 1);
  }

  // ---- Caesar breaker -----------------------------------------------------
  function breakCaesar(ciphertext) {
    const letters = lettersOnly(ciphertext);
    const cands = [];
    for (let k = 0; k < A; k++) {
      const pt = caesarDecrypt(ciphertext, k);
      cands.push({
        shift: k,
        plaintext: pt,
        chi: chiSquared(pt),
        score: englishScore(pt),
      });
    }
    cands.sort((a, b) => a.score - b.score);
    const steps = [
      `Read ${letters.length} letters of ciphertext (${ciphertext.length} characters including spaces and punctuation).`,
      `The Caesar keyspace is only 26 keys, so try every one of them.`,
      `Score each of the 26 candidates with the chi-squared test against English letter frequencies (lower = more English-like).`,
    ];
    let conf = 0;
    if (letters.length === 0)
      steps.push("No letters found, so nothing can be scored. Confidence 0.");
    else {
      const best = cands[0],
        second = cands[1];
      conf = confidence(best.score, second.score);
      steps.push(
        `Best candidate: shift ${best.shift} scores ${best.score.toFixed(1)}; runner-up shift ${second.shift} scores ${second.score.toFixed(1)}. The winner is ${(second.score / Math.max(best.score, 1e-9)).toFixed(1)}x better, which is why confidence is ${Math.round(conf * 100)}%.`,
      );
      steps.push(
        `Recovered key = ${best.shift}. Decrypting with it gives readable English.`,
      );
    }
    return {
      key: cands[0].shift,
      plaintext: cands[0].plaintext,
      candidates: cands,
      confidence: conf,
      steps,
    };
  }

  // ---- Vigenere breaker ---------------------------------------------------
  function factors(n, max) {
    const f = [];
    for (let i = 2; i <= Math.min(n, max); i++) if (n % i === 0) f.push(i);
    return f;
  }
  function kasiski(ciphertext, maxLen) {
    const letters = lettersOnly(ciphertext),
      pos = {},
      votes = {};
    for (let i = 0; i <= letters.length - 3; i++) {
      const c = letters.slice(i, i + 3);
      (pos[c] = pos[c] || []).push(i);
    }
    for (const c in pos) {
      const occ = pos[c];
      if (occ.length < 2) continue;
      for (let j = 0; j < occ.length - 1; j++)
        for (const f of factors(occ[j + 1] - occ[j], maxLen))
          votes[f] = (votes[f] || 0) + 1;
    }
    return votes;
  }
  function iocLengths(ciphertext, maxLen) {
    const letters = lettersOnly(ciphertext),
      res = [];
    for (let m = 1; m <= maxLen; m++) {
      if (letters.length < m * 2) break;
      let sum = 0,
        cnt = 0;
      for (let i = 0; i < m; i++) {
        let col = "";
        for (let j = i; j < letters.length; j += m) col += letters[j];
        if (col.length > 1) {
          sum += indexOfCoincidence(col);
          cnt++;
        }
      }
      res.push([m, cnt ? sum / cnt : 0]);
    }
    return res;
  }
  function estimateKeyLength(ciphertext, maxLen) {
    const iocTable = iocLengths(ciphertext, maxLen),
      kas = kasiski(ciphertext, maxLen);
    const maxVotes = Math.max(0, ...Object.values(kas));
    const guesses = iocTable.map(([len, ioc]) => {
      let close = (ioc - RANDOM_IOC) / (ENGLISH_IOC - RANDOM_IOC);
      close = Math.max(0, Math.min(close, 1.2));
      const share = maxVotes ? (kas[len] || 0) / maxVotes : 0;
      return {
        length: len,
        ioc,
        votes: kas[len] || 0,
        score: close + 0.35 * share - 0.012 * (len - 1),
      };
    });
    guesses.sort((a, b) => b.score - a.score);
    return guesses;
  }
  function recoverKey(ciphertext, keyLen) {
    const letters = lettersOnly(ciphertext);
    let key = "";
    for (let i = 0; i < keyLen; i++) {
      let col = "";
      for (let j = i; j < letters.length; j += keyLen) col += letters[j];
      if (!col) {
        key += "A";
        continue;
      }
      let bestShift = 0,
        bestChi = Infinity;
      for (let s = 0; s < A; s++) {
        let shifted = "";
        for (const c of col) shifted += toChar(toIdx(c) - s);
        const chi = chiSquared(shifted);
        if (chi < bestChi) {
          bestChi = chi;
          bestShift = s;
        }
      }
      key += toChar(bestShift);
    }
    return key;
  }
  function minimalPeriod(key) {
    for (let p = 1; p < key.length; p++)
      if (
        key.length % p === 0 &&
        key.slice(0, p).repeat(key.length / p) === key
      )
        return key.slice(0, p);
    return key;
  }
  function breakVigenere(ciphertext, maxLen, knownLen) {
    maxLen = maxLen || 20;
    const letters = lettersOnly(ciphertext);
    const steps = [
      `Read ${letters.length} letters of ciphertext.`,
      `Whole-text index of coincidence = ${indexOfCoincidence(letters).toFixed(4)} (English ~ 0.0667, random ~ ${RANDOM_IOC.toFixed(4)}). A value near random says several alphabets are in use, i.e. Vigenere, not Caesar.`,
    ];
    const warnings = [];
    if (letters.length < 2)
      return {
        key: "",
        plaintext: ciphertext,
        guesses: [],
        confidence: 0,
        steps: steps.concat("Too few letters to analyse."),
        warnings: [
          "Ciphertext contains fewer than 2 letters; nothing to attack.",
        ],
      };

    const kas = kasiski(ciphertext, maxLen);
    if (Object.keys(kas).length) {
      const top = Object.entries(kas)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);
      steps.push(
        "Kasiski examination: distances between repeated 3-letter chunks favour key lengths " +
          top.map(([l, v]) => `${l} (${v} votes)`).join(", ") +
          ".",
      );
    } else
      steps.push(
        "Kasiski examination found no repeated 3-letter chunks (the text is short); relying on the index of coincidence alone.",
      );

    let guesses;
    if (knownLen) {
      guesses = [
        { length: knownLen, ioc: 0, votes: kas[knownLen] || 0, score: 1 },
      ];
      steps.push(`Key length was supplied: ${knownLen}.`);
    } else {
      guesses = estimateKeyLength(ciphertext, maxLen);
      if (guesses.length)
        steps.push(
          "Slicing the text every m letters and averaging each slice's IC ranks the key lengths: " +
            guesses
              .slice(0, 4)
              .map((g) => `${g.length} (IC ${g.ioc.toFixed(3)})`)
              .join(", ") +
            ".",
        );
    }
    if (!guesses.length) guesses = [{ length: 1, ioc: 0, votes: 0, score: 0 }];

    const attempts = guesses.slice(0, 3).map((g) => {
      const key = minimalPeriod(recoverKey(ciphertext, g.length));
      const pt = key ? vigenereDecrypt(ciphertext, key) : ciphertext;
      return { fit: bigramFitness(pt), guess: g, key, plaintext: pt };
    });
    attempts.sort((a, b) => b.fit - a.fit);
    const bestFit = attempts[0].fit,
      tol = 0.05;
    const plausible = attempts
      .filter((a) => a.fit >= bestFit - tol)
      .sort((a, b) => a.key.length - b.key.length || b.fit - a.fit);
    const win = plausible[0];
    steps.push(
      "For each candidate length, split the text into that many columns (each column is a plain Caesar cipher) and solve every column with chi-squared. Then judge each plaintext on letter PAIRS (TH, HE, IN...), which a per-column shift cannot fake.",
    );
    steps.push(
      `Shortest key that explains the text: ${win.key.length} letters. Recovered key = "${win.key}".`,
    );

    const others = attempts.filter((a) => a.key !== win.key).map((a) => a.fit);
    let conf = fitnessConfidence(
      bestFit,
      others.length ? Math.max(...others) : null,
    );
    const perCol = letters.length / Math.max(win.key.length, 1);
    if (perCol < 20) {
      warnings.push(
        `Only ~${Math.round(perCol)} letters per key position (want 20+). Frequency statistics are shaky here, so treat the key as a guess rather than a result.`,
      );
      conf = Math.min(conf, 0.45);
    }
    steps.push(
      `Confidence ${Math.round(conf * 100)}%, based on how English the plaintext looks and how far ahead it is of the next-best key length.`,
    );

    return {
      key: win.key,
      plaintext: win.plaintext,
      guesses: guesses.slice(0, 6),
      confidence: conf,
      steps,
      warnings,
    };
  }

  global.CipherEngine = {
    caesarEncrypt,
    caesarDecrypt,
    breakCaesar,
    vigenereEncrypt,
    vigenereDecrypt,
    breakVigenere,
    chiSquared,
    indexOfCoincidence,
    bigramFitness,
    letterCounts,
    ENGLISH_FREQ,
    ENGLISH_IOC,
    RANDOM_IOC,
    lettersOnly,
  };
})(window);
