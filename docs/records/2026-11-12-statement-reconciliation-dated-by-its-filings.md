---
id: 2026-11-12-statement-reconciliation-dated-by-its-filings
status: shipped
date: 2026-11-12
prs: [1031]
supersedes:
superseded-by:
---

# The statement reconciliation is dated by the filings it read, never by the day it was built (operator ruling 2, 2026-11-12) — the same code on the same inputs now sends the same synthesis request on any day, as far as this block goes; a second build-day value, the price-staleness note, still reaches the request and is found, not fixed

**WHAT.** Operator ruling 2 of 2026-11-12, relayed by A on #1004 at 09:51Z, verbatim "Fix now, by
B (Recommended)": keep the build date out of what is sent to the synthesis, using the filing's own
date, behind a test that fails first.

The defect. Assembly called `statement_recon.attach(mech, bundle, facts,
filed_by=datetime.now(UTC).date())` (`vinci/dossier/mechanical.py`). So
`financial_summary.statement_reconciliation.as_filed_by` held the build's own UTC day, and a row
with no filing figure read "no revenue fact for this period on any alias tag, as filed by <that
day>". Both are in the synthesis request's facts (`synthesis.synthesize` dumps the layer minus
`NOT_SENT`). A's impact sweep found the move on BURL and CNXC, panel pages, through #984. The facts
were already cut at the page's price date (`AsOfEdgar`), so that day was not even the cut the block
was read at.

Now:
1. **Assembly passes the page's price-date cut** (`filed_by=cut`) instead of a clock read.
2. **`as_filed_by` is the latest filing date of the filings the rows name** (each row's
   `accession`; a composed LTM names its year-to-date's), and None when no row names one
   (`StatementReconciliation.as_filed_by: str | None`). It is never the cut and never the build's
   day.
3. **A row with no filing figure says "as filed by <the page's price date>"**: the cut it was
   read at, which S3's #1014 record named as the real cause (its "DEFERRED (PR round 2)" item).
4. **The refresh back-fill builds the same block** (`refresh.statement_recon_transform`): as filed
   by the page's price date, dated by its filings. It no longer reads `assembled_at`, and a page
   that states none is no longer refused for it.

**WHO BUILT IT.** Two builds were made in parallel. S3 built the fix first, uncommitted, in its
own scratchpad, on branch `claude/s3-asfiled-build-date`, which was never pushed. The coordinator
moved the task to S2 before that build was known, and S2 built it independently. The coordinator
then handed S3's patch over (`tracked.patch`, 13 files; it applies clean on `53e5f26e`). The two
code changes are the same in behaviour, hunk for hunk: the cut passed by assembly, `_row`
returning its filing's date, `max` of those dates or None, `str | None`, and the dropped
`assembled_at` refusal. This PR is S2's branch, which was further along: already reviewed, with
its suite and impact check running. S3's distinct findings are credited and reproduced here:
FUBO's block reads no filing, so its date becomes null. S2 did not take two of S3's tests:
- S3's two-day test fakes `mechanical`'s two clock names only, on LLY's harness with the
  synthetic exports, whose periods match no LLY filing. Every row is a note, so no real filing
  date crosses assembly in it.
- Its BURL, CNXC and FUBO pins are value pins on living committed pages, which the TEST-LAYER
  rule keeps for frozen fixtures.

**WHY.** Identical code on identical inputs sent different requests on different days, so a base
and a candidate captured on different UTC days differed with no code change. Until this lands,
every panel measurement must capture both sides on one UTC day (A's 09:51Z comment).

**HOW VERIFIED.** All at $0.
- **Fail first:** 13 of the 45 tests in the three changed files fail with main's `vinci/`
  (a throwaway worktree of `53e5f26e`) and pass here. In `tests/test_statement_recon_build_date.py`,
  6 of its 7 fail at main, and the 7th is the control that proves the clock fake reaches the
  clock. It uses NIKE's committed companyfacts and bars against the committed synthetic CIQ
  exports (both years end May 31; the synthetic LTM ends 2026-08-31, NIKE's Q1 FY27), assembled
  offline through `assemble_mechanical`:
  - **Two faked UTC days, byte-identical requests,** at two price dates. The request is captured
    as the impact check captures it (`vinci.evals.capture_child.capture_calls`, nothing sent).
    The fake rebinds `datetime` in every loaded vinci module and on the `datetime` module, and
    moves `time.time`, which `date.today()` reads. At main, priced 2026-10-16, the requests built
    two and five days later differ in one line, `"as_filed_by"`. Priced 2026-09-30, the LTM rows'
    notes differ as well. Here both are equal.
  - **The control:** the fake reaches `date.today()` too. Built on 2026-11-01, the page prints
    "16 calendar days before assembly".
  - **A real filing date still reaches the field:** NIKE's Q1 FY27 10-Q, 0000320187-26-000193,
    filed 2026-10-02. Priced 2026-09-30, before it, the LTM rows say "as filed by 2026-09-30" and
    the block is dated 2026-07-15, by the FY26 10-K 0000320187-26-000088.
  - **`reconcile` itself:** None when no row read a filing (TJX, as filed by 2026-03-30), and the
    latest of the rows' filings rather than the cut (TJX's 10-Q, 2026-08-28, read as filed by
    2026-10-21).
- **Six pins held the old date and change on purpose:** five in `tests/test_statement_recon.py`,
  and `test_refresh_price_date_cut.py`'s, which S3's record named. The committed-pages pin now
  accepts exactly two vintages. The new one is the back-fill's block exactly. The old one states
  the assembly date and is exactly what `reconcile` builds when handed that date, with every other
  field equal to the new rows. A page stamped with this vintage must be the new one (review round
  0; a mutant page stamped so and carrying the old date fails it).
- **Mutants, 6 of 6 killed** (each in a throwaway worktree, against the three changed files):
  - the block dated by the cut again (7 tests fail);
  - assembly's clock read restored (3, the two-day test among them);
  - the earliest filing instead of the latest (5);
  - a block that read nothing stating the cut (1);
  - the back-fill reading the assembly date again (3);
  - a no-figure row's note naming no date (4).

  Two first versions of the two-day test let a mutant through, and both were fixed in review
  round 0. Priced where every row reads a filing, the clock's only remaining output (a no-figure
  row's note) never appears, so the test now also builds a page priced before NIKE's 10-Q. And a
  function-local `from datetime import datetime` read the real class, so the fake now replaces
  the `datetime` module's attribute too.
- **The impact check** (`python -m vinci.impact run`, rebased onto main `964cd104` as the
  coordinator asked, so main's #1025 tool ran; head `aa7a39e6`; VALID against main `8b4b35f6`):
  - **Built 27 of 27; 27 of 27 pages move, 82 field changes, all in the block:** 27
    `as_filed_by` (the build's 2026-11-12 → each page's latest filing read; FUBO → null) and 55
    no-figure rows' notes (the build's day → the page's price date). No other field moves. 0
    responses fetched live, and 0 read with different bytes at the two refs.
  - **Requests: 27 of 27 differ, in the facts only.** The system prompt, the tool schema and the
    digests are unchanged, and the frozen panel replay differs on 0 of 6 pages. Per request, 1
    USER line moves on 10 pages (BURL, IT, MCK, NFLX, NKE, PARR, ROST, TGT, TJX, WERN), 2 to 8 on
    16, and 11 on FUBO (its date and its ten notes).
  - **Fail first:** 14 of the 53 tests in the four changed test files fail with base's code; 0
    fail with head's.
  - **#1025 met this ruling, and this PR fixes that too.** The first run with main's tool set 26
    of 27 pages apart as "still on two days … run noise", and compared FUBO alone.
    `run.build_days` read a page's `as_filed_by` as a day the build ran on. That was true while it
    was the build's date, and is never true once it is a filing date. A side with a `clock.json`
    (every build since #1025) is now dated by it alone. A side kept from before still falls back to
    the page's dates, as #984's run needs. `tests/test_impact_days.py` pins BURL's two sides from
    that run: base stamped 2026-11-12, head 2026-08-27, both clocked 2026-11-12. The pin failed with
    #1025's code. The report's sentence "a build stamps today's date on the page (`as_filed_by`)"
    now reads "a build can stamp its day".
- **Head on two days, real pages.** The six panel pages were built through the impact check's
  own child and sandbox layout, with every vinci clock binding, the `datetime` module's class and
  `time.time` faked (scratchpad `day_child.py` and `two_day.py`, `--no-network`). Each page was
  built on two UTC days, 2 and 5 days after its own last stored close. Head's requests are
  **byte-identical on 6 of 6** (BURL, CNXC, LLY, MCK, ROST, SMPL). Base's **differ on 6 of 6**, and
  only in `as_filed_by` and the no-figure notes: 1 line per request on BURL, MCK and ROST, 3 on LLY,
  5 on CNXC and 8 on SMPL. These are the same counts the impact check moves, which shows the defect
  on the panel's real pages and that it is gone.

**BOUNDARY.**
- **The impact check's counts** are over all 27 committed pages at head `aa7a39e6` (data ref),
  base `964cd104`. The price store is `mosaic-theory-ta/data/vinci.db` (file `9afc57d8669a`,
  frontier 2026-11-04), snapshotted read-only. CIQ is 285 exports, and the HTTP cache was served
  frozen. The run was 2026-11-12 11:38Z.
- **"Lines" are USER-message lines** of one request.
- **The two-day check** covers the six panel pages, on the same inputs, with base and head code at
  `964cd104` and `b9a5ca12`; `vinci/dossier` is identical at `aa7a39e6`.
- **The committed-page counts** (27 pages, 34 rows with a note, FUBO's 10) are over
  `data/dossiers/*/dossier.json` at `53e5f26e`, rebuilt from `tests/fixtures/companyfacts/`.
  The impact check reads the SEC cache instead, so its dates can differ from them.
- **The suite:** `pytest -m "not network"` at `b9a5ca12`, plus every `tests/test_impact*.py` at
  `aa7a39e6`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **No committed page moves in this PR.** All 27 committed pages are the old vintage (at
  `53e5f26e`), and the back-fill never overwrites a stored block that differs, so each moves at
  its next build. FUBO's block reads no filing at all (10 of its rows have no filing figure), so
  its date becomes null.
- **A composed LTM names its year-to-date's filing only.** Its fiscal year and prior year-to-date
  come from filings that are normally earlier, but a 10-K/A filed after the 10-Q would be read and
  not dated. The field says "the filings the rows name", not "every filing read".
- **The paid panel check: none proposed here.** SYSTEM and the tool schema are untouched; the move
  is in facts (one date, and the date in rows that have no figure). That is the FACTS-only ruling
  recorded in `docs/records/2026-11-11-fix2-bookkeeping-batch-3.md` (item 2). Stated for the
  operator to overrule: `vinci/dossier/mechanical.py` and `vinci/dossier/schemas.py` are in
  `compare.SCORER_FILES`, so the scorer fingerprint changes, and `score_run` refuses a registration
  made before this merges at any other code. The impact check prints its row-53 line as ASK THE
  OPERATOR, the FACTS-only case.

**FOUND, NOT FIXED (hold scope).**
- **The price-staleness note is a second build-day value in the request.**
  `mechanical._price_stale_note` compares the page's last close with `date.today()`, and a close
  more than 7 days old (`_ASSEMBLY_PRICE_STALE_DAYS`) prints "PRICE STALE AT ASSEMBLY: last stored
  close <date> is <N> calendar days before assembly" on `stock_info.price.note`, which the request
  carries. Every page the impact check builds on a store more than 7 days old carries
  it, with N moving by one each day. CNXC's request captured on 2026-11-11, on a store whose
  closes end 2026-08-05, reads "98 calendar days". On the impact check's run of
  2026-11-12, 27 of 27 head requests carried it, at 8 to 37 days, on a store whose closes end
  2026-10-06 to 2026-11-04. So the same-UTC-day rule for panel captures still holds after this
  lands, unless the store is fresh or the note is kept out of the request. The guard is fail-loud
  by design, so whether its text belongs in the request is a decision, not a fix.
