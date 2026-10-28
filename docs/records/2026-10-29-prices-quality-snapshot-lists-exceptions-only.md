---
status: open
date: 2026-10-29
prs: []
---

# The prices quality snapshot lists its exceptions only: every row a check did not confirm in full is committed in full, the rest are counted with the count stated, and the full card stays beside the store, git-ignored (operator ruling C1)

**WHAT.**
- **The ruling.** Operator, 2026-10-29, verbatim: "C1: compact". It answered one question: keep
  committing the full price-quality snapshot, or commit a compact one.
- **A source declares what its snapshot holds** (`Source.committed_rows` in `vinci/quality/core.py`):
  `full` or `exceptions`. Only `prices` declares `exceptions`. `validate` refuses any other value.
- **The exceptions form** (`core.compact`, schema `data_quality/1+exceptions`). Per check:
  - It keeps every row the check did not confirm in full, exactly as the full card holds it. That
    is a row with a unit that differs (stated or unexplained) or is unchecked, a unit the check's
    own rule excludes, no unit judged at all, or the check not run on the name.
  - It counts the rest: `not_listed` holds `confirmed_names` and `confirmed_units`, and
    `not_applicable` holds `{reason, count}` in place of the name list.
  - It states both in a `listing`. From 2026-10-29's `stale_bar`: "10 of 2,440 names listed in
    full: 10 the check ran on and did not confirm in full, 0 it did not run on. Counted, not
    listed: 2,430 names whose every bar is confirmed (2,564,668 bar(s)), and 0 it does not apply
    to".
  - Unchanged from the full card: the boundary (its population list, the inputs sha256 and the
    commit), the fleet counts, the not-run groups, the coverage map and the failure-class summary.
  - `rows.statement` describes the form, and `rows.full` names the full card by path and sha256.
- **The guard** (`core.reconcile`). It raises, naming the check, when:
  - a listed row is not an exception, or names a name outside the boundary;
  - the not-run rows are not the not-run groups, reason for reason;
  - listed rows plus counted names and units do not equal the fleet's names run, not run and not
    applicable, and its units per status; or the fleet's item count is not the boundary's;
  - the `listing` does not state those numbers, or the card lacks its statement or its full
    card's path and hash.
  `compact` calls it before it returns, so an unreconciled card is never produced.
- **The command.** `vinci audit quality --write` on an `exceptions` source writes the full card to
  `data/data_quality_full/<source>/<date>.json`, then the exceptions snapshot to the usual
  `data/snapshots/data_quality/<source>/<date>.json`. `data/*` already ignores the full card; an
  explicit `.gitignore` line names it. A card that does not reconcile writes neither file and
  exits 1.
- **History is not rewritten.** The committed full snapshots (2026-10-24, 10-26, 10-28) stay as
  they are. 2026-10-29 is the first point in the exceptions form, in its own artifact commit.

**WHY.**
- **The size.** The price source writes every security for every check. On main before this
  build: `2026-10-24.json` 2,135,590 bytes, `2026-10-26.json` 2,135,590, `2026-10-28.json`
  3,041,630. That is 7,312,810 bytes in five days, in a public repo whose history keeps every copy.
- **The open call.** `docs/records/2026-10-24-prices-quality-source.md` ("COST: the snapshot is
  2.1 MB") called the compact form a core change and the operator's call. The call is now made.
- **SCOPE: prices only, by face validity.**
  - Prices reads the git-ignored store over the whole universe: 2,797 names in the committed
    points, and growing with the universe. Its full card cannot be re-derived from git at any
    commit, and it costs megabytes a day.
  - CIQ and release read the ~27 committed pages. Their latest snapshots are 116,864 and 28,648
    bytes. `tests/test_quality_ciq.py` re-derives the latest CIQ snapshot byte-for-byte from the
    pages it names. Compacting them would save little and would cost that equality.
  - The mechanism sits in the core because the command names no source
    (`test_the_core_and_the_command_name_no_source`) and the reconciliation rule is
    source-agnostic. A later large source opts in with one field.
- **Where the full card goes.** `data/data_quality_full/` is the simplest durable place: under
  `data/`, which git ignores except for what it names, and beside the store the card was read from.
  It is named by source and date like the snapshot series, so a run's pair is found by name, and
  `rows.full.sha256` ties a local file to its committed point.
- **Not-applicable names are counted, not listed.** `close_vs_tiingo` was not applicable on 2,771
  names in each committed point and `history_across_ids` on 2,793 (2026-10-28), and each such list is a
  complement of a population stated elsewhere: names without a committed page, names whose ticker
  no other security carries. The population itself stays listed in `boundary.names`.

**READERS — every one found, and what happened to it.**
- **How they were found:**
  - `git grep` for `data_quality/`, `snapshot_path`, `vinci.quality`, `audit quality`;
  - the JSON keys `by_name`, `inputs_sha256`, `items_not_run`, `items_run` and
    `failure_class_summary`;
  - `quality` and `scorecard` in `frontend/`, `scripts/`, `.github/` and `.claude/`;
  - `git log --all -S` on `data_quality/`, `snapshot_path(`, `items_not_applicable` and
    `inputs_sha256`, and `git log --all -i --grep` on `compact` and `2.1 MB`.

| reader | what it reads | disposition |
|---|---|---|
| `vinci/cli.py::_cmd_audit_quality` | writes the snapshot | CHANGED: writes the full card locally, then the exceptions form |
| `tests/test_quality_prices.py::test_command_scores_the_store_and_writes_a_dated_snapshot` | the snapshot it wrote | EXTENDED: reconciles it; the full card holds every name; `ohlc_ordering` lists BBB alone |
| `tests/test_quality_prices.py::test_the_committed_snapshot_is_counts_and_statuses_only` | the latest committed prices snapshot | CHANGED: one dated 2026-10-29 or later must be the exceptions form and reconcile; earlier ones are full |
| `tests/test_quality_core.py` (toy source) | the snapshot it wrote | unchanged: the toy source is full |
| `tests/test_quality_ciq.py`, `tests/test_quality_release.py` | their own series | unchanged: CIQ and release stay full |
| `docs/RUNBOOKS.md` §k | describes `--write` and quotes "2.1 MB" | UPDATED |
| `docs/engineering.md` glossary | the series path | one line added: "exceptions form / full card" |
| `STATE.md` §2 (the three price-quality lines) | the series path | still true; one claim added |
| the 2026-10-24, 10-27 and 10-28 records | dated snapshot files | immutable; the files they cite are not rewritten |
| the frontend | nothing | `frontend/build.py` mirrors only `ranked_queue.jsonl` and `decision_ledger.jsonl`; `data_quality` in `frontend/views/shared/dossier.js` is the anchor's own field |
| scoring's and the monitor's Tiingo reserve (#839) | nothing | `dividends.reserved_symbols` reads the ledger, `followed.json` and the monitor's assignments; `TiingoEodClient.symbols_asked` reads the HTTP cache |
| workflows, scripts, hooks | nothing | no reference to `audit quality` or `data_quality` |

**HOW VERIFIED.**
- **CORPUS FIRST.** Each committed full snapshot was compacted
  (`tests/test_quality_compact.py::test_each_committed_full_snapshot_compacts_losing_no_exception`).
  The test's own restatement of the rule, written apart from `core._listed`, gives the same rows,
  byte-equal. No confirmed row is listed, and the counts reconcile.

| committed file | checks | full bytes | exceptions bytes | rows listed |
|---|---|---|---|---|
| `2026-10-24.json` | 6 | 2,135,590 | 66,445 | 173 |
| `2026-10-26.json` | 6 | 2,135,590 | 66,201 | 171 |
| `2026-10-28.json` | 9 | 3,041,630 | 88,716 | 250 |

- **2026-10-28, check by check** (rows listed: of which differ / unchecked / excluded / not run;
  a row may carry more than one):
  - `ohlc_ordering` and `flat_close_run`: 0 listed, 2,797 counted.
  - `stale_bar`: 10 listed (10 differ).
  - `split_shaped_step`: 125 listed (95 differ, 35 excluded).
  - `series_gap`: 35 listed (35 differ).
  - `close_vs_tiingo`: 1 listed (1 differs); 25 counted, 2,771 not applicable.
  - `step_vs_tiingo`: 67 listed (13 differ, 4 unchecked, 52 not run); 58 counted.
  - `zero_volume_vs_tiingo`: 8 listed (6 differ, 1 unchecked, 1 not run); 1 counted.
  - `history_across_ids`: 4 listed (4 differ); 2,793 not applicable.
- **THE REAL RUN.**
  - **The store.** A read-only SQLite backup of the primary checkout's `data/vinci.db`, taken
    2026-10-29 00:19 IST into this session's scratchpad. The primary's file was not written; its
    mtime stayed 2026-10-28 22:04. The backup was linked into the worktree, and the primary's
    `data/cache/tiingo` (192 entries) was copied beside it.
  - **The command.** `vinci audit quality --source prices --write` at `bbd563cb`, 31 seconds.
  - **What it read.** 2,440 names; 2,572,227 bars; 1,236 market sessions 2021-09-01 → 2026-08-05
    (+43 partial); inputs sha256 `490f24d4…`.
  - **What it wrote.** The full card, 2,663,626 bytes, at
    `data/data_quality_full/prices/2026-10-29.json`; its sha256 equals `rows.full.sha256`. The
    snapshot, 73,136 bytes (2.75% of the full card), equals `core.compact` of the full card as
    re-read. 164 rows listed across nine checks; each equals its full-card row.

| check | unit | fleet units: confirmed / unexplained / unchecked / excluded | names: run / not run / n/a | listed | counted |
|---|---|---|---|---|---|
| ohlc_ordering | bar | 2,572,227: 2,572,227 / 0 / 0 / 0 | 2,440 / 0 / 0 | 0 | 2,440 |
| stale_bar | bar | 2,572,227: 2,572,152 / 75 / 0 / 0 | 2,440 / 0 / 0 | 10 | 2,430 |
| flat_close_run | bar | 2,572,227: 2,572,227 / 0 / 0 / 0 | 2,440 / 0 / 0 | 0 | 2,440 |
| split_shaped_step | step | 2,569,765: 2,569,657 / 108 / 0 / 22 | 2,439 / 0 / 1 | 98 | 2,341 |
| series_gap | step | 2,569,787: 2,569,765 / 22 / 0 / 0 | 2,439 / 0 / 1 | 7 | 2,432 |
| close_vs_tiingo | bar | 20,734: 20,733 / 1 / 0 / 0 | 18 / 0 / 2,422 | 1 | 17 |
| step_vs_tiingo | step | 70: 65 / 3 / 2 / 0 | 61 / 37 / 2,342 | 40 | 58 |
| zero_volume_vs_tiingo | bar | 42: 20 / 22 / 0 / 0 | 6 / 3 / 2,431 | 8 | 1 |
| history_across_ids | security | 60: 60 / 0 / 0 / 0 | 60 / 0 / 2,380 | 0 | 60 |

  (`differs_stated` was 0 on every check.)
  - **Tiingo, at its monthly cap until 2026-11-01.**
    - Cached windows were served from the copied cache.
    - The 18 page names' windows were not in it (this store's spans differ from the
      research-alpha copy's), so the run asked Tiingo for them, and Tiingo served all 18. Tiingo
      serves a symbol at the cap only when the key has already looked it up in the month (#839's
      `TiingoBudget`), so these added no new symbol to October's count.
    - The first new symbol after them was refused, and nothing more was asked.
    - That leaves `not_run` by name: on `step_vs_tiingo`, 32 names "not asked: monthly symbol
      limit", 1 refused, and 4 "Tiingo was not read for this name"; on `zero_volume_vs_tiingo`, 3
      "not read".
- **MUTATIONS — one per rule, each red, each restored byte-for-byte** (scratch runner over the five
  quality test files, `PYTHONDONTWRITEBYTECODE=1`):

| rule | mutation | caught by |
|---|---|---|
| an exception row is listed exactly as held | the copy drops `excluded` | the corpus test |
| an unchecked-only row is an exception | the predicate reads differs only | the corpus test (2026-10-28) |
| a confirmed row is counted, not listed | every applicable row listed | the corpus test |
| counts that do not reconcile are refused | the count comparison disabled | the tamper pins |
| not-run rows are the not-run groups | that comparison disabled | the tamper pin dropping Z |
| a listing states its own counts | that comparison disabled | the tamper pin on `listing` |
| each check says what it counts and does not list | "Counted, not listed:" dropped | the 2026-10-28 value pin |
| the card states its form | "COUNTED, NOT" dropped from `rows.statement` | the statement pin |
| only prices commits its exceptions | prices declares `full` | the scope pin |
| an unknown `committed_rows` is refused | `validate`'s check disabled | the scope pin |
| the full card goes under `data/`, git-ignored | path moved under `data/snapshots/` | the command pin |
| the snapshot names the full card's own bytes | one byte appended to the full card | the command pin (sha) |
| a card that does not reconcile writes nothing | the `continue` removed | the write-nothing pin |

- **Gate.**
  - `ruff check .` clean, and `mypy --strict vinci` clean (216 source files with the new test).
  - `tests/test_quality_prices.py` carries three `mypy --strict` errors from before this build
    (lines 28 and 446 import re-exported names). The gate runs mypy on `vinci` only; they are not
    fixed here.

**BOUNDARY.**
- **Committed sizes:** bytes on disk of the files at `e6df4691`, main before this build.
- **Corpus counts:** per check, over all 2,797 names in each committed file. "Rows listed" counts
  one row per (check, name).
- **Real-run counts:** the primary-store backup as of 2026-10-29 00:19 IST, after #842's
  re-filing and #846's restatement. Population: every security with bars, 2,440. Bars dated
  2021-09-01 → 2026-08-05. Code at `bbd563cb`.
  - **A series boundary, not a quality change.** The three earlier points read a different store:
    the research-alpha copy, 2,797 names, latest bar 2026-10-16. The 2026-10-29 point's reads line
    names its own store, and the two must not be read as one series.
- **Tiingo counts:** this run only, against the copied cache's October entries.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **ACCEPTED: a confirmed name's row for prices is no longer in git.** The public repo shows how
  many names a check confirmed, never which ones. The full card exists only in the checkout that
  ran the scorecard, and it is lost with that checkout. The sha256 still identifies a surviving
  copy, and a re-run on the same store reproduces every row while the inputs sha256 matches.
  *Falsifier:* a review that needs a confirmed name's past row on a store that no longer exists.
- **ACCEPTED: not-applicable names are counted, not listed.** Each check's reason and count stay.
- **COST: one more schema string.** A reader of `by_name` written for the full form is refused by
  `schema` rather than reading a missing name as absent.

**FOUND, NOT FIXED.** Seven `not_run` rows read "Tiingo was not read for this name" without saying
why. Each is an id with no `securities` row: a former holder re-filed by #842 (`PRIOR-CORZ-2022-12-30`,
`PRIOR-HHH-2022-07-15`, `PRIOR-WLTH-2023-06-12`), or an id that holds bars without a `securities`
row (the BBBY, LION, TRON and CALY ids). So there is no symbol to ask. The reason text predates this build.
