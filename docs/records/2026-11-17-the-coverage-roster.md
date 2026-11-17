---
id:
status: shipped
date: 2026-11-17
prs: []
supersedes:
superseded-by:
---

# THE COVERAGE ROSTER (W27): which names the fund covers is one dated file, `data/coverage_roster.jsonl`, and every reader that walks the covered names reads it, the pages checked against it; retiring MVST or AORT the roster's way is one roster line + the page's own 9 files + 0 pin sites (#1044 touched 32 files, #942 30), and a retirement today still carries the pin sites that read that name's living page, measured per name (211 value pins and 239 invariant reads at `4336b542`); nothing rendered moves ($0)

**WHAT.**
- **The roster.** `data/coverage_roster.jsonl` holds one move per line: a `date`, a `ticker`, the
  `status` it moves to (`active`, `watch` or `retired`), the operator's `ruling` in their own words,
  the `source` that carries it, and the `record` that explains it (or null). A name's status is
  its latest line. A move is appended, never edited, so a dated line is history. The file holds 28
  moves:
  - AORT, retired 2026-11-09 ("retire AORT fully", #942);
  - MVST, retired 2026-11-12 ("we want to drop/remove MVST altogether from our list for future as
    well", #1044);
  - the operator's marking of 2026-11-13 ("go ahead", issue #1004 comment 6847554747, accepting
    B's table unchanged; `docs/records/2026-11-13-fix2-bookkeeping-batch-8.md`): 11 active (BRBR,
    EPAM, GOOGL, IT, LLY, NCNO, SMPL, TJX, VITL, VRRM, WERN) and 15 watch (AMZN, BURL, CNXC, FUBO,
    MCK, NFLX, NKE, ORKA, PARR, ROST, TECX, TGT, UBER, V, WLK).
- **The reader.** `vinci/coverage_roster.py` reads the file strictly, refusing:
  - an absent or empty file;
  - a line not in its one canonical form, or with a missing or extra field;
  - an unknown status, a blank ruling or source, a non-upper-case ticker, or a record that is not
    a `docs/records/*.md` path;
  - a date earlier than the line above it, two moves for one name on one day, or a move that
    repeats the name's status.

  `covered_pages` returns the covered names only once the committed pages agree with them, and
  otherwise raises naming every disagreement:
  - a page with no line;
  - a covered name with no page;
  - a retired name that still has a page.

  A page is its `dossier.json`, never its folder, since a git-ignored `llm_call.log` outlives a
  retired page in a checkout that held it.
- **The readers now walk the roster** (the audit below lists every site):
  - `frontend/build.py`: the mirror and `frontend/dossiers/index.json`, through a stdlib twin, as
    the build fence requires;
  - `refresh.refresh_fleet`: the $0 fleet refresh;
  - `vinci driver-facts-pass` and `vinci transcript-run-cut` with no `--tickers`, and
    `vinci dossier inputs-backfill --all`;
  - the fact layer's `pages` scope, `vinci/facts/scope.py`, whose stated `RULE` is restated to
    say so.
- **Assembly is the work an active name gets.** `vinci dossier`, for `--ticker` and `--top` alike,
  refuses every finalist whose roster status is not `active`. A watch page stays as committed, a
  retired name has no page, and a name with no line was never taken into coverage. The check runs
  before any model client exists, so a refusal costs nothing, and one refused name refuses the
  run.
- **The monitor reads no roster, and agrees with it by a pin.** The monitor marks decisions and
  records: its freshness set is the live ledger decisions plus the `watch` and `pending_analyst`
  records. B's design keeps coverage apart from verdicts and positions, and a live decision on a
  retired name is still scored to its horizon. So coverage must not be what takes a name out of
  the monitor. The one door coverage could close, a retired name's watch record, is closed by
  the retirement archiving that record, and the suite now refuses a roster-retired name that
  still has a live record. The freshness pin checks the committed book against the roster's
  retired names. A first cut read the roster in `_watch_tickers`. `/code-review` found that a
  re-cut of a past day then applied a retirement dated after it, and that 32 synthetic-book
  monitor tests in 11 files would need a roster. That cut is reverted, and `vinci/cli.py`'s
  monitor code is main's.
- **The test-side lists a retirement used to edit now derive:**
  - `test_record_legibility`'s hand list of retired archives comes from the roster;
  - eight record-count pins compare their walk with the seal manifest's live records
    (`tests/sealed_corpus.py`), which every archive already rewrites;
  - the page-count floor compares with the roster.

**WHY.** The code held no list of the names the fund covers. Coverage was whichever page was
committed, so every reader used a directory listing as its definition. A retirement then had to
change everything that had used it that way: MVST's retirement (#1044) touched 32 files, 22 of them
under `tests/`, and AORT's (#942) 30, 19 under `tests/`. B's design on issue #1004 (comment 6847522000,
item 6, agreed by A in comment 6847633111) asks for one dated roster that the rebuild, the
monitor, the desk and `frontend/build.py` read, with value pins on frozen pages. It also asks for
three states kept apart: coverage state, verdict and position. Every move is to be dated with a
reason, never deleted, and AVOID is never a parking bucket. B's note of 2026-11-16 (comment
6911284520) put this build before row 11's monitor work, as both were expected to write
`vinci/monitor.py`. This PR does not touch that file: the freshness set is built in
`vinci/cli.py`.

## THE AUDIT — every place that enumerated the covered names at main `4336b542`

Searched in two vocabularies, the house words (`covered`, `coverage`, `followed`, `watch`,
`active`, `retire`, `roster`) and the plain ones (`glob`, `iterdir`, `listdir`, `rglob` near
`dossiers`, and `dossier.json`), over `vinci/`, `frontend/`, `scripts/`, `tests/` and
`.github/workflows/`. The history checks were `git log --all -i --grep=roster` (it hits only the
follow-list and peer-set senses of the word), `git log -S"retired.json"` (only as an unbuilt
proposal, in #942 and #1044), `git log -S"RETIRED_ARCHIVES"` and `git log -S"def _watch_tickers"`.
No roster existed.

**Readers that decided which names get work — now read the roster:**

| site | read | now |
|---|---|---|
| `frontend/build.py` main loop | folders under `data/dossiers/` holding `dossier.json` → the mirror and `index.json` (`tickers`, `labels`, `reads`, `sleeves`) | `_covered_pages()`, a stdlib twin pinned to `vinci.coverage_roster` |
| `vinci/dossier/refresh.py` `refresh_fleet` | `data/dossiers/` folders | `roster.covered_pages` |
| `vinci/cli.py` `_cmd_driver_facts_pass` (no `--tickers`) | `data/dossiers/` folders | `roster.covered_pages` |
| `vinci/cli.py` `_cmd_transcript_run_cut` (no `--tickers`) | `data/dossiers/` folders | `roster.covered_pages` |
| `vinci/dossier/inputs_backfill.py` `run` (`--all`) | `data/dossiers/*/dossier.json` | `roster.covered_pages` |
| `vinci/facts/scope.py` `scope_names` | `data/dossiers/*/dossier.json` ∪ followed names | the roster's covered names ∪ followed names; `RULE` restated |
| `vinci/cli.py` `_watch_tickers` (the monitor's freshness set) | `scenarios/*.json` at `watch` / `pending_analyst` | unchanged; pinned against the roster's retired names, with the record guard refusing a retired name's live record |
| `vinci/cli.py` `_cmd_dossier` (assembly, the rebuild) | the ranked queue or `--ticker`, with no coverage check | refuses a name not `active`, before any model client |
| `tests/test_record_legibility.py` `RETIRED_ARCHIVES` | a hand list of retired archive keys | derived from the roster |

**Readers of the pages as facts — left walking `data/dossiers/`.** Their question is what every
committed page says, so a page the roster does not know must not escape them. The roster check,
pinned in `tests/test_coverage_roster.py`, holds that walk equal to the roster.
- **`vinci/labels.py:68` `committed_gics_index(root)`.** It takes a root: tests point it at frozen
  directories, and it has no production caller. Its build twin now walks the roster.
- **The data-quality sources:** `vinci/quality/sources/release.py:538`, `ciq.py:876`, `:888` and
  `:904`, and `prices.py:677`. Each audits and hashes every committed page.
- **`vinci/audit_r1.py:377`.** The R1 audit matrix over every page.
- **The impact harness:** `vinci/impact/run.py:1121` and `vinci/impact/store.py:76`. It builds
  every committed page at both refs.
- **Seven `scripts/`:** `debt_maturity_moves`, `build_sec_reference_fixture`,
  `build_companyfacts_fixture`, `build_price_fixture`, `cohort_anchoring_falsifier`,
  `audit_verbatim_corpus` and `verbatim_key_flips`. These are one-off audits and fixture
  builders over the committed pages.
- **The corpus-wide tests.** 197 `glob`/`iterdir` lines over `data/dossiers` in `tests/`.

**Not enumerators:**
- **The desk.** `vinci/theme_intelligence/market.py:562` reads one company's page for its
  consensus, by name, and lists no names. MVST's record found no desk file naming MVST.
- **`vinci/monitor.py`** holds no name list. The freshness set is built in `vinci/cli.py`.
- **Explicit-list commands:** `vinci financials-backfill` and `peerset-backfill` (`--tickers`
  only), and `vinci/evals/report.py` `living_drift(tickers)`.
- **`frontend/dossiers/index.json`** is `frontend/build.py`'s output. The web's `dossier.js` reads
  it, and its `tickers` equal the roster's covered names (pinned).
- **The watch/active distinction** lived in prose only: STATE row 41,
  `docs/records/2026-11-12-rebuild-prep-prechecks-on-all-27-pages.md`'s 2026-11-13 amendment and
  issue #1004. No code read it. It is now the roster's lines.
- **`data/followed.json`** is the follow route: each followed name's book and reason, 17 names.
  It is not coverage. MNST is followed and has no page, which a follow may do before its first
  assembly. The fact scope still unions it, as before.

**No inconsistency found.** The 26 committed pages are exactly the marking's 26 covered names, and
neither retired name has a page. So nothing was stopped for.

## HOW VERIFIED

- **Fail first.** `tests/test_coverage_roster.py` (48 tests) was run against BASE code, with only
  the roster file, the new test file, its helper and the new module copied into a checkout of
  `4336b542`. 23 of the 48 failed:
  - all 18 refusal cases (six readers × three shapes), since base readers walk whatever is on
    disk;
  - the build twin's two pins;
  - the three assembly refusals (MVST retired, FUBO watch, ZZZZ unlisted).

  The 25 that pass at base are the roster's own form pins (the module was copied in), five
  readers' positive walks (base globs the same 26 pages) and the assembly control (SMPL). On the
  branch, 48 of 48 pass.
- **Nothing rendered moves.** `python frontend/build.py` on clean `4336b542`, twice, then on the
  branch. All 87 files it writes under `frontend/dossiers`, `frontend/scenarios`,
  `frontend/monitor` and `frontend/snapshots` were hashed. The two base runs are identical. The
  branch run is identical to them, and its stdout is identical, but for
  `frontend/snapshots/manifest.json`. That file is git-ignored and differs only in its
  minute-stamped `generated_at`. `git status` is clean after each build. No page file is touched.
- **The proof on MVST and AORT** ran in scratch worktrees of this branch, with nothing committed
  from them.
  - *BEFORE:* the name put back as it stood before its retirement. Its roster line became `watch`;
    its page came back from the retirement's parent commit (MVST `dad8f441`, AORT `f491d155`); its
    record moved back live; its seal key went back to the ticker; and the mirrors were rebuilt.
  - *AFTER:* retired the roster's way. One line was appended, the page deleted, the record
    archived, the seal key renamed, and `frontend/build.py` run.
  - *The count:* `git diff --stat -M` from BEFORE to AFTER is, for each name, **one roster line +
    the page's own 9 files + 0 pin sites still naming it.** The 9 files are the page's two files,
    the two web mirrors, the dossier index, the record's archive move, its seal key, its card
    mirror and the card index. #1044 touched 32 files and #942 30.
  - *N = 0, measured, because #1044 and #942 had already re-pointed those names' pins.* The static
    scan below flags 14 MVST and 9 AORT test functions on the BEFORE trees. All 18 distinct ones
    (51 cases) pass on the AFTER tree with no test edited and none skipped: each reaches the
    frozen copy through a ticker-conditional helper the scan cannot follow. One network pin
    outside the offline suite, `test_primary_source_assembly_mvst_live`, reads MVST's living page
    and has always skipped since #1044, which reported it. A name retired today carries its N
    from the table below, not 0.
  - *The control:* the AFTER tree equals this branch's tree but for the roster file.
  - *The tests in each state.* 13 test files for MVST and 17 for AORT were run.
    - BEFORE fails only pins that hold the name as retired: its dated line, the retired-paged
      refusals, the retired-archive guard and the freshness pin. One AORT failure is outside the
      roster: AORT's record as of `f491d155` fails an IRR rule added after #942.
    - AFTER fails only the history pin, because the scratch dates the move 2026-11-17, not the
      real line.
  - *A defect the proof found and this PR fixes.* The retired-archive guard demanded a record file
    for a retirement whose move gives `record: null`. It now checks a record only when the move
    names one. Three mutation cases had depended on the first line's exact text and were rebuilt
    from the parsed move.
- **The remainder, measured: the pin sites a retirement still carries.** A retirement must still
  re-point every test that reads that name's LIVING page by name. These come in two kinds, which
  the TEST-LAYER RULE treats differently:
  - **(a) value pins** — a figure, a date or a phrase read off the re-drawn page. The rule puts
    these on frozen fixtures, so they violate it today;
  - **(b) invariant reads that name a ticker** — presence and citation, ordering, guard
    behaviour. The rule allows these on a living page, and they still break when the name
    leaves.

  At `4336b542` there are **450 (test function, name) pairs: 211 value and 239 invariant**, in
  385 distinct test functions in 98 files. The count is printed by `scripts/named_page_pins.py
  4336b542`, run read-only. A (test, name) pair is one site; `files` counts distinct files.

  | name | value (a) | invariant (b) | files |
  |---|---|---|---|
  | SMPL | 44 | 39 | 26 |
  | AMZN | 33 | 37 | 25 |
  | GOOGL | 11 | 24 | 15 |
  | TJX | 14 | 13 | 8 |
  | BRBR | 12 | 12 | 6 |
  | IT | 14 | 10 | 6 |
  | UBER | 10 | 10 | 7 |
  | LLY | 4 | 14 | 10 |
  | BURL | 8 | 9 | 10 |
  | TECX | 3 | 14 | 5 |
  | VRRM | 8 | 7 | 8 |
  | CNXC | 5 | 9 | 6 |
  | NFLX | 6 | 7 | 9 |
  | EPAM | 9 | 2 | 10 |
  | NCNO | 5 | 6 | 5 |
  | VITL | 8 | 3 | 8 |
  | MCK | 3 | 5 | 5 |
  | WERN | 5 | 3 | 6 |
  | FUBO | 2 | 5 | 7 |
  | NKE | 3 | 4 | 4 |
  | PARR | 1 | 2 | 1 |
  | V | 1 | 2 | 3 |
  | TGT | 1 | 1 | 2 |
  | WLK | 1 | 1 | 2 |
  | ORKA | 0 | 0 | 0 |
  | ROST | 0 | 0 | 0 |

  **The scan was validated on the two known answers.**
  - At `dad8f441`, #1044's parent, it finds 20 MVST functions in 10 files: 17 of the 18 pins #1044
    re-pointed, plus the 3 other MVST test sites #1044 changed (the `test_guidance_vintage` skip,
    the deleted strict xfail, the network pin). It misses one: `test_dossier`'s cited EX-99.1
    bear point.
  - At `f491d155`, #942's parent, it finds 12 AORT functions in 8 files. Of the 8 test files #942
    changed that read AORT's page, it finds 7 (it misses `test_dilution_denominator`), and it adds
    `test_known_wrong_marker`.

  Neither kind is moved in this PR (WHAT IT COSTS, item 1). No frozen fixture is added.

**BOUNDARY.**
- **Counts:** at main `4336b542` (2026-11-16), on the committed tree, unless another commit is
  named.
- **"Pages":** `data/dossiers/*/dossier.json`, 26.
- **"Files touched":** `git show --stat` for #1044 (`12764514`) and #942 (`fd123ada`), and
  `git diff --stat -M` between the scratch states.
- **The remainder:** `scripts/named_page_pins.py` at `4336b542`, an AST scan of the 529
  `tests/**/*.py` files (less `tests/fixtures/`), for the 26 names with a page there. Its
  docstring gives the rules. A read is one of:
  - a path literal naming `dossiers/<T>`;
  - `<dossiers> / "<T>"`;
  - `<dossiers> / name` or an f-string, with the name bound to literal tickers by a `for`, a
    `parametrize`, or a helper parameter (helpers followed within the module);
  - a literal ticker used as a subscript key in a page-reading function.

  The kind:
  - VALUE when an `assert` compares against a number literal other than 0 or 1, a
    `pytest.approx`, or a string literal holding a digit or a space;
  - INVARIANT otherwise.

  It is a lower bound: a read through another module's helper, or a ticker built at run time, is
  not seen. It over-counts a helper that switches a retired name to its frozen copy (see N = 0
  above). The kind rule is mechanical, so the follow-up reads each site.
- **The 197 corpus lines:** `glob`/`iterdir`/`rglob`/`listdir` lines near `dossier` in `tests/`.
- **The fail-first run:** the 48 nodes of `tests/test_coverage_roster.py` at the branch's
  WIP commit `943a44a5`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **The pin sites on living pages are not moved.** Moving 450 (test, name) pairs in 98 test
   files would collide with every open PR that edits those tests, so it is a follow-up (STATE row
   41, open item (a)), proposed by A after this merges. Its scope:
   - **(a)** moves each value pin to a frozen fixture, cut from the real committed page through
     the real decode path (`tests/fixtures/frozen_pages/`), never hand-rolled;
   - **(b)** makes each invariant read iterate the roster's covered names instead of naming a
     ticker.

   Until then, retiring a name re-points its N sites from the table, as #1044 did. Falsifier: a
   retirement after the follow-up still edits a test that reads the retired page by name.
2. **A paid or `--no-llm` build of a watch or unlisted name is refused.** That includes a `--top N`
   run of screen finalists not yet on the roster. Building one means appending its move to
   `active` first, with the ruling. This is what B's three statuses mean: the status decides the
   work. Falsifier: a build the operator asked for is refused while its name is active.
3. **A synthetic tree with pages needs a roster.** Six test files gained one.
4. **Two pins changed shape.**
   - `test_scenarios`'s two EXACT record counts now take their number from the seal manifest. A
     record added with its seal entry no longer edits that test, and the seal diff carries the
     add.
   - `test_spot_as_of_gate`'s floor of five stamped records became three checks: the walk sees
     every sealed live record, every record at or past schema 1.5 carries a stamp, and at least
     one stamp is checked. A pre-1.5 record losing its stamp is no longer caught there; nothing
     else that pin checked is lost.

   Falsifier for both: a record walk that misses a live record still passes.
5. **The screen can still rank a retired name.** The queue holds no exclusion, by the operator's
   2026-11-05 ruling, but assembly now refuses one. That closes #942's and #1044's falsifier, "an
   assembly of MVST started without the operator asking".
6. **A watch page carries no dated "frozen" line.** B's design gave each one such a line, naming
   its known defects. That is a render change, under the PREVIEW RULE, and is not built here
   (STATE row 41, open item (b)).
7. **A new name's line and its first page land together.** An `active` line with no page is
   refused by every reader, as the brief's pin requires, and `vinci dossier` builds only an
   active name. So between appending a new name's line and committing its first page, the mirror
   and the fleet passes refuse loud. If that first assembly fails after its spend inside a
   `--top` cohort that wrote another page, the closing mirror raises naming the name. The written
   pages stay on disk and a $0 re-run of the mirror publishes them (found by `/code-review`).
   Falsifier: a new name's line and page are committed apart, or an operator is blocked from a
   first build.
8. **$0.** No model call and no vendor call, and no page is rebuilt or re-rendered.
