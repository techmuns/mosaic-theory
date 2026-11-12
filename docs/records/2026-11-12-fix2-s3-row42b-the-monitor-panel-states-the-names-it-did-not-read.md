---
id: 2026-11-12-fix2-s3-row42b-dropped-names
status: shipped
date: 2026-11-12
prs: [1029]
supersedes:
superseded-by:
---

# The monitor day carries the names it dropped, typed, and the web's freshness panel states them: "N of M names read · <T> not read — <cause>" (STATE row 42 (b))

**WHAT.** TeamNostra fix request 2, stream S3, STATE §5.0 row 42 (b). The operator approved the
Phase-1 preview on 2026-11-12, in chat with the coordinator: "Approve, build it".
- **Before:**
  - `vinci monitor` drops a name's freshness row in two cases: its EDGAR filings window cannot be
    read (#1020), or its record's evidence date cannot be (`UnreadableEvidenceDateError`).
  - It said so only in the day's `notes`, and the web's freshness panel
    (`frontend/views/shared/decision-log.js`, `freshnessPanel`) reads `freshness` alone. So the
    deployed desk showed N−1 names with no word of the missing one.
  - #1020 widened it: one unreadable window used to write no day at all.
- **Now:**
  - The day carries `freshness_dropped`. `MonitorSnapshot` holds one `FreshnessDrop` per name:
    the ticker, a closed cause (`filings_unread` or `record_date_unreadable`), and the whole
    detail.
  - `_cmd_monitor` writes it at both sites, and each note line is rendered from it
    (`FreshnessDrop.note()`), byte for byte the line written before. As with `RealizedRow`, the
    note and the field are one definition.
  - A day committed before the field loads as one that dropped none, which every committed day
    is.
- **The panel** leads with "N of M names read · <T> not read — <cause>".
  - The count is the whole set's, and every dropped name is listed, never cut to a first few.
  - The whole reason sits one click down, in a `<details>` "Why it was not read" ("Why they were
    not read" for more than one), force-opened in print with every other `<details>`.
  - A voided call is neither counted nor listed. That is the filter the cards' labels use
    (`voidedBefore`): a call ruled out of the record after the day, with no live decision open.
  - A day with no drop, or committed before the field, renders exactly as before.

- **The extraction drift guard:** `vinci/monitor.py` is re-pinned as `refactor`. A page build
  reads only `benchmark_for_cap` from it, which this PR does not touch, so no dossier output
  changes.

**WHY.** "A TRUNCATED OUTPUT PRINTS ITS OWN TRUNCATION." A panel showing eight names where the day
had nine reads as a complete book. And "parsers consume structured values": the dropped names
were a fact carried only in prose, which no reader could take without parsing English.

**HOW VERIFIED.**
- **`tests/test_monitor_dropped_names.py`, 10 tests.** 8 fail on main `9708fbc0`. The other 2,
  the committed-day negative pins for 2026-11-02 and 2026-11-11, pass on both.
  - **The day:** the real `vinci monitor` command over the committed ledger, securities and
    assignments (#1020's harness).
    - IT's page -001 as a 404 is a typed `filings_unread` drop, and its FILINGS note is that
      drop's `note()`.
    - WERN's typo'd amendment date is a typed `record_date_unreadable` drop.
    - A day that reads every name drops none.
    - On every committed day, the drop notes are exactly the typed drops' `note()`s. This is an
      invariant, so a day committed later passes it too. The 10 committed so far
      (2026-07-20 → 2026-11-11) carry neither.
  - **The panel:** the real decision-log `render()` under node over the committed frontend.
    - The committed 2026-11-02 day and the deployed latest, 2026-11-11, print no line and no
      tier. Each renders identically with the field absent or empty.
    - One drop (IT) prints "8 of 9 names read · IT not read — its EDGAR filings could not be
      read", with its detail under "Why it was not read".
    - Two drops (IT, WERN) print "7 of 9", list both, and use the plural.
    - GOOGL, voided on 2026-11-11, dropped beside IT, prints "7 of 8" and is named in neither
      the line nor the tier. Dropped alone, nothing prints.
- **Byte comparison under node** against main `9708fbc0`: main's decision-log page and this
  build's are byte-identical on 2026-11-02 (42,553 bytes) and on 2026-11-11, the deployed latest
  (39,776 bytes). On the one-drop day, the build's page is
  byte-identical to the approved preview's, so the approved shots are what ships.
- **Review round 0** (`/code-review high --fix`, 2 findings, both fixed):
  - The committed-day test first asserted that no day carries the field. Every day the monitor
    writes from now on carries it, so the first such day would have turned the suite red. It now
    states an invariant over every day.
  - `droppedNames` was exported with no reader, and is now module-private.
- **Shots:** six, 1280 wide at 2x, taken with headless Brave over DevTools. Both days, collapsed,
  every `<details>` opened, and print media. They are committed under
  `docs/monitor/dropped-names-2026-11-12/screenshots/` and shown in the PR.

**BOUNDARY.** The 10 committed days are `data/monitor/20*.json` at main `9708fbc0`, 2026-07-20 →
2026-11-11. Measured 2026-11-12.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Two ways a name leaves the freshness set are NOT typed here, by the approved preview's
  scope:**
  - A live name with no `scenarios/<T>.json` is skipped with no note at all
    (`_cmd_monitor`: `if not rec_path.exists(): continue`).
  - A record that states no evidence by the day gets no row, but a note. That is correct, since
    the record did not exist on that day, but the panel does not say so either.
  - Typing either is a cause to add to `FreshnessDrop` with its own render. Found, not fixed.
- **A residual of #1024 (row 42 (a)), recorded here at the coordinator's request:** when the theme
  desk's filings walk stops short, the enrichment candidate still stores `foreign_filer=False`.
  - `enrich.py`'s `foreign` is False because the foreign-filer check read None, and
    `EnrichmentCandidate.foreign_filer` is `bool = False` (`vinci/theme_intelligence/schemas.py`).
    So an unknown is recorded as "not foreign".
  - `cards.py` then shows the ticker hint without "the US line of a foreign filer". `market.py`
    skips the name anyway, since it has no verified ticker.
  - #1024's basis note now names the unreadable page, so the reason is stated; only the boolean
    overstates.
  - Measured live: 0 of 261 (CIK, as-of) pairs walk past their recent page (#1024's record).
  - The fix makes the field `bool | None`, a schema change for its own PR. Found, not fixed.
- **STATE ROW 42 IS CLOSED HERE.** (a) merged first, in #1024 (`9708fbc0`), so this PR, the
  second, deletes the row from §5.0, per CLAUDE.md's closing rule. The row has no entry in the
  frozen archive below to strike. Row 60's bookkeeping, which said row 42 "stays open on its
  items (a) and (b)", now says those items closed it.
