---
id: 2026-11-12-fix2-s3-price-stale-note-reference-date
status: shipped
date: 2026-11-12
prs: [1034]
supersedes:
superseded-by:
---

# The stock-info price note counts a stale close from the page's own reference date, never from today, so the synthesis request no longer moves with the calendar; the assembly-time check against today is a stderr warning only

**WHAT.** The operator approved this in chat on 2026-11-12: "Yes, fix it", answering the
coordinator's "Fix the stale-price note by counting from each page's own date?".
- **Before:**
  - `mechanical._price_stale_note(last_close, today)` was called with `date.today()` at both of
    its sites: `_stock_info`, for `stock_info.price.note`, and `assemble_mechanical`, for the QA
    twin `stock-info: …`.
  - Its text, "PRICE STALE AT ASSEMBLY: last stored close <date> is <N> calendar days before
    assembly", reached the synthesis request with the page's facts, and N grew by one each day.
  - So the same inputs still sent a different request every day, and panel captures stayed
    pinned to one UTC day. The coordinator read it on every head request of #1031's impact run.
- **Now:**
  - Both sites count from the page's REFERENCE DATE, the date the page is as of. They keep the
    same 7-day cadence (`_ASSEMBLY_PRICE_STALE_DAYS`), in words that name that date: "PRICE STALE
    AT THE REFERENCE DATE: last stored close <date> is <N> calendar days before the page's
    reference date <date> — run `vinci refresh` and re-assemble". The same inputs give the same
    note on any day.
  - The check against today keeps its purpose, a fail-loud warning that the build is reading a
    store `vinci refresh` has not brought up. It is now a stderr line printed at assembly
    (`_warn_stale_at_assembly`), never written to `dossier.json`, its frontend mirror or the
    request.
  - `_stock_info` no longer takes `today`.
- **Why the reference date, not the price cut:** assembly's cut (`page_price_date`) is the last
  stored close itself, so a gap counted to it would always be 0. The reference date is the
  deterministic date a stale close can be measured against.
- **Nothing else reads the note's text.** Searched in `vinci/`, `frontend/lib`, `frontend/views`
  and `tests/`: the two sites, one unit pin and #1031's two-day test. No committed page carries
  the note (0 of the 27 `data/dossiers/*/dossier.json` at main `85152609`), because each was
  assembled on a fresh store.
- **The assembly-run record** (`vinci/dossier/run_metrics.py`) has no field for run-time
  warnings, so the stderr line is the only carrier. Adding one is a schema change to a committed
  series, not made here.
- **The vintage** is `2026-11-12.price-stale-note-counts-from-reference-date`; `mechanical.py` is
  re-pinned to it.

**WHY.** A request that moves with the calendar cannot be replayed, and it puts a difference no
code made into every panel measurement. The day the build runs is a fact about the build, not
the page.

**HOW VERIFIED.**
- **`tests/test_statement_recon_build_date.py`**, #1031's NIKE harness, extended with a reference
  date that can trail the close. 3 tests fail on main `85152609` (a 4th, round 1's, fails on its
  mutant):
  - **The two-day test, with the stale case live.** A close of 2026-09-30 on a page as of
    2026-10-16 is built on 2026-11-01 and on 2026-11-05. On main the note read "32" and then "36
    calendar days before assembly", and the requests differed. On head both read "16 calendar days
    before the page's reference date 2026-10-16", the note is in the request, and the requests are
    byte-identical.
  - **The negative pin.** A close of 2026-10-16 on a page as of 2026-10-20, built on 2026-11-30,
    has no note. On main it read "45 calendar days before assembly". Stderr says
    "… 45 calendar days before today (2026-11-30)".
  - **The stderr pin.** #1031's "the faked day reaches a clock read" test is CHANGED
    DELIBERATELY: that clock read is the stderr WARNING now ("… 16 calendar days before today
    (2026-11-01)"), and the fresh page carries no note.
- **PR round 1** (the coordinator's review of `1a6a5325`): 5 mutants, 4 killed. The survivor put
  the QA twin (`stock-info: …`, stored in `dossier.json`'s QA flags) back on today, and nothing
  failed, so a committed page would still have differed day to day.
  `test_a_stale_close_writes_the_same_qa_flags_on_any_day` builds the stale case on two faked UTC
  days and requires the same QA flags, with the twin counted from the reference date. The one
  wall-clock number among the flags, the release fetch's latency, is masked. The test fails on
  that mutant.
- **`tests/test_dossier.py::test_price_stale_note_fires_only_past_the_cadence`** is CHANGED
  DELIBERATELY. It pins the reference-date count and its words, and that the stderr warning
  fires past the cadence and not inside it.
- **`tests/test_cap_vintage_label.py`** drops the `today=` argument `_stock_info` no longer takes.
- **The impact run, base `4b2f0cb9` (main after #1026) against head on ONE UTC day (2026-11-12), $0.**
  - It built 17 of the 27 committed pages at $0 with each side's code; the other 10 have no
    price history in the impact store, at either ref.
  - **The note moves on all 17:** AMZN, BRBR, CNXC, EPAM, FUBO, IT, MVST, NCNO, NKE, ORKA,
    PARR, SMPL, TECX, VITL, VRRM, WERN and WLK.
    - In `stock_info.price.note` and its QA twin, "last stored close 2026-08-05 is 99
      calendar days before assembly" becomes "… is 72 calendar days before the page's
      reference date 2026-10-16".
    - The 99 is the impact store's frontier counted to the run's day; the 72 is that frontier
      counted to the pages' reference date, the same on any day.
  - **Each of the 17 synthesis requests differs by exactly that one facts line**: system and
    tool schema the same, USER −1 +1. This is a facts-only request move, so no paid panel
    check (fix request 2, batch 3 item 2).
  - No committed `dossier.md` re-renders differently: none carries the note.
  - The one frontend file that differs is `snapshots/extraction_versions.json`, the new
    vintage.

**BOUNDARY.** The committed pages are the 27 `data/dossiers/*/dossier.json` at main `4b2f0cb9`.
The impact run builds them with base and head code on ONE UTC day (2026-11-12), against the
impact store (store frontier 2026-08-05).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A page built late on a store that was current at its reference date carries no note now.**
  Only stderr says the build is late. That is the point: the lateness is the build's, not the
  page's.
- **The stderr line is not recorded anywhere persistent.** The run record has no field for it
  (above).
