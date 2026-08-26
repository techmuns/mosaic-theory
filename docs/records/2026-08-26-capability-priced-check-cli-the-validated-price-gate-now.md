---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
migrated-from: STATE.md §2 Built and verified
---

# **PRICED-CHECK CLI — the validated price gate now has a repo home (2026-07-15, feat/priced-check;

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **REPRODUCTION-VERIFIED EXACT** against the committed `report_all.txt` T007 basket
    (WERN/MRTN/HTLD/LSTR/ARCB/RXO @ 2026-07-10): **12mo exSPY +25.8%, exIWM +14.8%, tag MIXED** — and
    every other figure (6/18mo, all six quarters, valuation 99%ile per-name, dispersion +0.57) matched
    to the printed precision. `--asof` matched the report's LATEST → **zero drift, no method mismatch**.
    (`daily_bars` adjusted closes == the grouped-daily adjusted closes the ad-hoc used.)
  - **UNRESOLVED #1 (runbook §c) CLOSED** — runbook §c now carries the real invocation; the KNOWN GAP
    section is empty (every loop reproducible from the repo). Tests (network-free, stubbed bars, 6):
    median/excess, `<3`-UNDEFINED, tag boundaries, stale exclusion, dispersion. ruff + `mypy --strict
    vinci` + pytest (654) green.
