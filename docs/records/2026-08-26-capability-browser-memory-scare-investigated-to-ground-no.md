---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
date-source: MIGRATION DATE — this record was cut out of STATE.md on 2026-08-26; the work it describes is earlier and is dated in the body. The filename prefix is therefore the migration date, not the event date.
migrated-from: STATE.md §2 Built and verified
---

# **BROWSER-MEMORY SCARE — investigated to ground; NOT the app. Recorded so it is not re-investigated.**

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - Heap snapshot named the mechanism: `Window (global*)` **×195**, `Detached HTMLDocument` ×65,
    `{__esModule}` **×4,686** (≈24 modules × ~195 realms), `Function` ×673k, `(compiled code)` ×895k.
    The app is ~325 KB across ~24 modules and creates **zero** iframes / `window.open` / `document.write`
    — it cannot produce ~900k compiled functions or 195 JS realms. That is injected third-party code.
  - **RESOLVED: browser EXTENSIONS injecting into the tab.** The same deployed page in an Incognito
    window (extensions off) reads **4.6 MB** — matching a local measurement of the identical route
    (4.4 MB, same 391 DOM nodes). Extensions accounted for ~132 MB, ~97% of the reported figure.
  - App-side facts, measured, no leak: **3–7 MB** heap across all 11 screens; 42 sequential navigations
    gave heap 3.9 → 6.1 → **2.7 MB** (falls — no monotonic growth); DOM fully reclaimed each cycle.
    Heaviest render is the Ranker at 5,115 nodes / 276 rows. There is NO 4–5× memory win available:
    the app's entire footprint is smaller than the noise floor of the browser it runs in.
  - **METHOD for any repeat doubt — do this FIRST (30 seconds, before any snapshot analysis):** open
    the page in Incognito and run `+(performance.memory.usedJSHeapSize/1048576).toFixed(1)`. It
    separates app from extensions immediately. A heap snapshot is only worth taking if Incognito is
    ALSO high.
  - **METHODOLOGICAL TRAP (cost a wrong conclusion here):** the first measurements were taken against
    a stale worktree while `main` had moved **56 commits** ahead (adding `scenarios/`, `uw-card.js`,
    `lib/cites.js`), so the benchmarked build was NOT the deployed one. Measure the DEPLOYED commit.
  - **NOT fixed (accepted, low value):** `lib/snapshots.js` fetches with `cache: "no-store"`, so every
    revisit re-downloads + re-parses (AORT's 209 KB was fetched 3× in one session). That is a SPEED
    cost only, with no memory implication; always-fresh fetches match the "static mirror lags local
    state until the next `git push`" design. Revisit only if navigation latency becomes a complaint.
