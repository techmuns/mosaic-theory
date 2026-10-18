---
id:
status: shipped
date: 2026-10-12
prs: [708]
supersedes:
superseded-by:
---

# The monitor runs at the latest close, and a past day is never written into the book — refused in code before anything is fetched — operator ruling on #707's open question

**WHAT.** The operator ruled option 1 of the three in
`docs/records/2026-10-11-monitor-reads-nothing-after-its-day.md` (2026-10-12): **a moved page gets a
NEW monitor day; a past day is never re-cut.** Stated so it needs no judgment: **`vinci monitor` is
run with NO `--ref`, which files the LATEST close** — the last session on or before today — and reads
filings through today.
- **Later than the newest committed day:** the run writes a new day.
- **The newest committed day itself:** the run is the same-session re-run.
- **A day that a later close sits after is never written into the book.** `--ref <close>` on a
  later morning would also bound the read at the close and hide that morning's 8-K, the defect
  #707's review fixed.

Where it lives:
- **`docs/RUNBOOKS.md` §j MONITOR DAY** — the loop: date, run, mirror, check, commit as an artifact.
- **The command refuses it, before anything is fetched** (`vinci/cli.py` `_cmd_monitor`). A `--ref`
  before today is refused unless `--out` names a scratch root. The command prints why and exits 1,
  with no price or filing call made and no book printed.
- **`--out <dir>` is the supported analysis re-cut.** The day is written to `<dir>/data/monitor/`
  while the history is still read from the book. An `--out` that resolves to the repo's own
  `data/monitor/` is refused.
- **`monitor.write_snapshot` refuses it too, for any Python caller.** That covers a day that a
  later day file already sits after: an overwrite, which an explicit `rewrite_history=True` still
  allows, or a BACK-DATED day never written, which has NO override. Both scans of the day directory
  go through one definition, `monitor.snapshot_days`.
- **The failure the operator meets.** `tests/test_panel_emit.py::
  test_emit_is_deterministic_over_the_committed_corpus` goes red whenever a page moves after the
  latest day, or when the emitter's code changes. Its assertion message names both causes and the
  ruled remedy, so the tempting fix (re-running the day it names) is answered where it is tempting.
  The assertion itself is unchanged.
- **STATE.md §5.0 row 5:** the past-day re-cut item #707 added is closed. The row's second "(b)"
  (phase 5 and the emitter), which duplicated a label, is relabelled "(c)".

**WHY.** #707 bounds every DATED input a day reads, but the panels, the measured rows and the
record-read fields read today's pages, records and cards. None of those has a per-item date to
filter on, so a re-cut after a later close writes later information into an earlier date; the 09-22
re-cut drew UBER's 10-09 multiple. Of the three options, the rule was already the practice (#705
wrote `2026-10-09.json` rather than re-cut `2026-09-22`). Versioning every document by commit date
(option 2) is kept for the day past days are re-cut for analysis. Stamping (option 3) would only
label the lookahead.

**FIRST REVIEW (same PR, before merge) — eight findings.**
- **Fixed in the review's own commit (`128fc99e`):**
  - **The run instruction.** It was `--ref <latest close>`, which brought back #707's hidden-8-K
    defect; it is now no `--ref`.
  - **The step-4 check.** It failed a correct run by comparing filings with the day's `as_of`; it
    now compares with the run date.
  - **The guard's description.** The runbook and record said `write_snapshot` refused more than it
    did.
  - **The test message.** It blamed every failure on "a page moved"; an emitter change also turns
    the pin red, and writing a new day over it would commit the regression.
  - **The falsifier.** It now counts ADDED day files too.
- **Fixed on top of it (`02aee736`, `112be3f1`):**
  - **A back-dated day.** `write_snapshot` now refuses a day never written, not only an overwrite.
  - **The duplicate "(b)"** in row 5.
  - **The PR description.**
  - **The "scratch re-cut" wording,** which pointed at a command that did not exist.

**SECOND REVIEW (same PR, before merge) — seven findings, all fixed here.**
1. **An explicit past `--ref` NEWER than the newest day still wrote.** The guard only looked for
   later day FILES, so with 2026-10-09 committed, `--ref 2026-10-14` run on 10-18 wrote a 10-14 day
   (reproduced by the reviewer through `_cmd_monitor`). It read 10-18's pages and hid every filing
   after 10-14. No guard fired, and no doc named the case.
2. **The accepted risk was not earned — a correction of the first fix.** It argued the remaining
   check needed the session calendar or a page-date ruling. That was true only INSIDE
   `write_snapshot`. `_cmd_monitor` already holds `--ref` and today, so refusing a past `--ref` costs
   no fetch and no calendar. It is built; the risk is closed, not accepted.
3. **The refusal came after all the work.** It fired at `write_snapshot`, after every EDGAR and
   price fetch and after a complete-looking book for the refused day had been printed, then died with
   a traceback. The command now refuses first, with a message and exit 1.
4. **"Pass rewrite_history=True"** named a flag `vinci monitor` does not have, and on a back-dated
   day it would have created a day that never existed. Now:
   - the back-dated case has no override;
   - the overwrite message says the parameter is Python-only.
5. **The step-4 check compared against "its `--ref`".** That would pass exactly the run it should
   catch. It now compares against today.
6. **`--ref`'s help** read as an ordinary as-of selector. It now states the rule, and `--out` is
   documented beside it.
7. **Two scans of the day directory.** The prior-day history and the later-day guard each globbed it
   with the same filter, free to drift apart. They now share `snapshot_days`.

**HOW VERIFIED.**
- **The real command, on the committed corpus** (days 07-20, 08-11, 09-16, 09-22, 10-09; run on
  2026-10-18, main `37006726` merged):

  | command | result |
  |---|---|
  | `--ref 2026-10-14` | exit 1 in ~1s, "is before today (2026-10-18)… Nothing fetched, nothing written" |
  | `--ref 2026-10-01` | exit 1, the same refusal |
  | `--ref 2026-09-22 --out .` | exit 1, "resolves to this repo's own data/monitor/ — the book, not a scratch root" |
  | `--ref 2026-09-22 --out <scratch>` | exit 0; wrote `<scratch>/data/monitor/2026-09-22.json` |
  | no `--ref` | exit 0; filed the latest close, 2026-10-16, into the book (removed afterwards: a test day, not this PR's) |

  - **After the three refusals:** `data/monitor/` was unchanged.
  - **The scratch re-cut of 09-22:** no filing after 09-22. Its only freshness difference from the
    committed day is IT's verdict, BUY → watch (#707's closure fix).
- **The message, on the real failure shape.** With `2026-10-09.json` set aside so `2026-09-22` is
  the latest day, the pin fails on UBER's two panels and prints the remedy.
- **Pins:**
  - `test_a_past_ref_into_the_book_is_refused_before_anything_is_fetched`, for 10-14 and 10-01:
    exit 1, the message, zero price and filing calls, no book printed, nothing written.
  - `test_an_out_root_that_is_the_book_is_refused`.
  - `test_a_run_with_no_ref_still_writes_into_the_book`.
  - `test_a_back_dated_day_is_refused_even_though_it_was_never_written`: `rewrite_history` does not
    let a back-dated day through.
  - #707's past-day pins now run through `--out`, the supported path.
- **Mutation** (5 mutants, 5 killed):
  - a past `--ref` allowed into the book;
  - `--out` allowed to point at the book;
  - `--out` ignored;
  - `rewrite_history` overriding a back-dated day;
  - the back-dated guard removed.

**BOUNDARY.**
- **The real runs:** the committed corpus as listed, 2026-10-18, through the repo's own EDGAR and
  Polygon clients.
- **"UBER's two panels":** `multiple_and_price` and `dilution`, out of 124 rows.
- **"Before today":** the machine's local date (`date.today()`).

**WHAT IT COSTS / WHAT IS RESIDUAL.**
- **A Python caller can still re-run the newest day after a later close.** One that hands
  `write_snapshot` a past day with no later file is not refused: the files alone cannot show a later
  close exists. Nothing in the repo does this — `_cmd_monitor` is the only caller (`grep
  write_snapshot` over `vinci/`, `scripts/`, `frontend/`, `.github/`).
- **"The latest close" is the last session Polygon has published.** A page rebuilt on a later
  source, such as a CIQ export, before Polygon publishes that session's close would be drawn into the
  earlier day by a routine run. Falsifier: a committed day whose panels cite a source dated after
  its `as_of`.
- **An `--out` re-cut is analysis, not record.** Its panels and record-read fields are today's
  documents; the committed day remains what the book recorded.
- **A moved page can leave the panel-emit pin red until the next close** when the page is struck on
  a session later than the latest committed day. The remedy is to run the latest close.
