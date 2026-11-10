---
status: open
date: 2026-11-09
prs: [934]
supersedes:
superseded-by:
---

# TeamNostra's fix request 2 is a tracked item: 178 IDs, one fix log on main, one lint that keeps it honest — and the coordinator's checks on committed data, re-run at 622786a2

**WHAT.** TeamNostra re-audited this repo at `622786a2` (their document 14) and sent fix request 2
(document 15, 2026-11-09), which replaces fix request 1 (document 12) as the live list. Both, with
the group notes, scripts and re-check logs, are **TeamNostra fix pack 2 (2026-11-09), held by the
operator**. Nothing from the pack is committed here, and nothing below quotes it beyond an ID or a
short phrase.

This record fixes the scope. Three surfaces carry the progress, all readable from `main` by every
agent on every machine:
- **`docs/fix-log-teamnostra-2.md`**: one row per ID, with the six columns document 15 §6 asks for
  (ID, Order, Status, Commit or PR, Test, Pages rebuilt). It is the fix log TeamNostra receives
  back, and the answer to "who has which ID". The rule sits at its top: a PR that touches an ID
  updates the row in that PR, and an agent checks the log and `gh pr list` before starting one.
- **`tests/test_fix_log.py`**, the lint. It reads this record's scope block (§1), so the scope cannot
  be edited quietly, and it rejects seven things:
  - a duplicate ID;
  - a scope ID with no row;
  - a row whose ID is outside the scope (RG-D22 among them);
  - a row whose Order is not the scope block's;
  - a status outside the five allowed;
  - a `fixed` row whose commit is not reachable from `origin/main`, or whose PR is not merged there;
  - a `fixed` row whose test node does not exist under `tests/` (a `test*` function or a
    `Test*::test*` method; a parametrize id is not checked).

  **The scope grows only by amendment.** Document 15 §6 also asks for a row for any document 11 ID
  TeamNostra marks fixed that we dispute. Such an ID enters through a dated entry under this
  record's `## Amendments` heading, carrying its own `fix-log-scope` block. The lint reads every
  block in the record.
- **STATE.md §5.0 row 60**, which points here and names the operator's items.

**WHY.** Two coordinating agents on two machines and one outside reviewer need one view of about
140 asked IDs. Chat is not a ledger. A log nobody checks rots silently, so a test reads it.

## 1. The scope: 10 orders, plus what is not asked

Document 15 §6 asks for a row for every R-ID in document 14's Appendix A, for V1-O2, V1-O3 and
V2-N1, and for every document 11 ID its Appendix A marks partly fixed or not fixed. That is
126 + 3 + 49 = **178 rows**. Of the 178 IDs:
- **143** are named in orders 1–10. E2-D10, E2-D11 and E2-D15 are in orders 1 and 3, so the
  per-order counts sum to 146.
- **30** are document 15 §4 items: not asked of mosaic-theory, because TeamNostra's own build (G0)
  makes them, though mosaic-theory may adopt any of them.
- **5** are asked but named in no order (§6, item 3).

| Order | IDs | What is wrong (our words) | Done when (our words) |
|--:|--:|---|---|
| 1 | 7 | Fixed in code; the committed pages still carry the old figures (FUBO, VITL, VRRM, EPAM, WERN, MVST, NFLX) and WLK is on an old extraction version | The six strict-xfail pins in `tests/test_pages_await_parser_rebuild.py` pass and lose their marks; WLK is re-assembled on the current extraction version |
| 2 | 7 | Errors live on committed pages or outputs: the customer count, impairment headroom across dates, PARR's surprise block, NFLX's "confirmed by the filing", the quality coverage map, the graph judge's reasons, transcript text length | Each case is a test that fails first. AMZN, AORT, EPAM, GOOGL, LLY, MCK, NFLX, NKE, PARR, TGT, UBER and V are rebuilt, and the quality snapshot and `data/graph_coverage.json` regenerated. For RG-D19: the pages meet the rule, or the rule changes on the record |
| 3 | 26 | Residuals of document 12's fixes and the regression V2-N1: late-reported splits, the ADS reader, one instrument read as the debt wall, round-figure restatements, the SEC budget across machines, as-of reads, amendments, guidance markers, LibreOffice failures, the spreadsheet customers route, and nine partly-fixed document 11 items | Each reproduction is a passing test. A split not confirmable on one basis fails loudly everywhere, cross-checked against Tiingo's `splitFactor`. The SEC budget holds 10/s per user across machines, with redirects paced |
| 4 | 44 | Silent wrong values and omissions on live paths: release and filing parsers (17, E2-D3 among them), prices (5), the SEC client (5), the CIQ reader (4), the synthesis and driver checks (9), downstream (3) | Each constructed case is a passing test. A figure the parser cannot read is refused or flagged, never dropped. A flat stock with a 20% special dividend reads 0% total return. Random dollar figures no longer trace at ~78%. The pre-spend check compares values and periods, or says it does not |
| 5 | 19 | Latent silent defects on constructed or mutated inputs (column order, tab names, file kinds from the company name, PDF tearsheets, 6- and 9-month columns, truncated files, namespaces, partial refreshes, Tiingo adjusted bars, a 403 read as a holiday, a stale fact-layer read) | Each is a passing test; a file's kind comes from its content or an exact name rule |
| 6 | 15 | Loud failures with the wrong reason or kind, including the Stop hook blocking without ruff, `bin/commit` tied to one machine, and tests that error on a shallow clone or without node | Each failure states its real cause; the hook warns; `bin/commit` finds the interpreter; those tests skip with a reason |
| 7 | 5 | The fact layer, before anything reads it: no acceptance time, the reader trusting the manifest, two errors that look alike, no upload source check | Before the layer serves a page: acceptance time stored and used in cuts, snapshot id and rows verified, the two errors distinct. Keeping original responses is our call |
| 8 | 8 | The evaluation harness: draw-once per ledger only, unregistered paid runs, unchecked gold hashes, a candidate scoring itself, M-GAP's truth, pre-registration not checkable from `main`, a constant model, an unprotected grader | Registration and gold hashes checked before any paid draw; a fixed scorer; held-out pages named and never used to build metrics; M-GAP's truth from an independent coding |
| 9 | 10 | Instructions and docs: 13 contradictions (RG-D20), `docs/ciq_extraction_notes.md` (G-D8 to G-D15), the key check's contact-less SEC request (RE1-D17) | Each contradiction resolved one way on the record; the notes file corrected or marked superseded; the key check uses the declared User-Agent |
| 10 | 5 | Tests and CI: the stale-pin check only warns, not one gate, the edit guard's gaps, the key check passing on an unexpected error, the weekly job's push to `main` | The stale-pin check fails CI; the gates share one command; the guard covers `pyproject.toml`, `tests/conftest.py` and `validate_keys.py`. Also asked: more synthetic CIQ tabs, retiring or re-basing tests whose committed data is gone, fresh counts in the workflows |
| §4 | 30 | Not asked (G0 builds them) | — |
| — | 5 | Asked, in no order (§6, item 3) | — |

**THE SCOPE BLOCK** is what `tests/test_fix_log.py` reads. One line per order; `P-Dn..m` is the run
P-Dn through P-Dm. Runs of three or more are written that way, which also keeps two IDs whose
numbers no STATE.md entry holds out of the identifier lint's sight (§6, item 9).

```fix-log-scope
1: E2-D5 E2-D10 E2-D16 E2-D12 E2-D11 E2-D15 D-D1
2: RBC-D1 RD-D1 RA-D1 RBC-D8 RBC-D9 RG-D16 RG-D19
3: RF-D1 RF-D2 RF-D8 V2-N1 RE1-D6 RE1-D1 RE1-D2 RE1-D8 RE1-D9 RE1-D12 RE1-D13 RA-D3 RA-D8 RA-D11 RA-D13 RBC-D6 RE2-D16 A-D2 BC-D7 BC-D10 D-D3 E1-D7 E2-D10 E2-D11 E2-D15 E2-D19
4: RE2-D1..4 E2-D3 RE2-D5..14 RE2-D17 RE2-D18 RE2-D20 RF-D3 RF-D4 RF-D7 RF-D9 RF-D13 RE1-D7 RE1-D10 RE1-D11 RE1-D14 RE1-D16 RA-D2 RA-D4 RA-D9 RA-D14 RG-D1..8 RG-D21 RD-D2..4
5: RA-D5 RA-D7 RA-D10 A-D15 RA-D12 RA-D17 V1-O2 V1-O3 RBC-D3 RBC-D7 BC-D1 BC-D2 RE1-D15 RE2-D15 RF-D5 RF-D10..12 RFL-D1
6: RA-D15 RA-D16 RBC-D2 RBC-D5 RBC-D10 RE2-D19 RFL-D7..10 RH-D2 H-D1 RH-D3 RH-D5 RH-D6
7: RFL-D2..6
8: RG-D9..15 RG-D18
9: RG-D20 G-D8..15 RE1-D17
10: RH-D1 RH-D4 RH-D7 RH-D8 RH-D10
§4: RA-D6 RA-D18..21 RBC-D4 RBC-D11 RBC-D12 RE1-D3..5 RF-D6 A-D17..24 BC-D4 BC-D8 BC-D12 E1-D2..4 E2-D20 F-S1 F-S2 F-S3
—: A-D13 A-D16 BC-D3 BC-D5 BC-D6
```

Four document 11 IDs are placed by document 15's own "=" notes: E2-D3 with RE2-D4 (order 4), A-D15
with RA-D10 (5), BC-D1 and BC-D2 with RBC-D7 (5), and H-D1 with RH-D2 (6). Each has its own row, as
§6 asks, so a PR that fixes one updates both. RE2-D18 sits in order 4 for its unbounded-read half;
its other half (acceptance times) is §4.

**Starting statuses.** Every row is `open`, with two exceptions:
- **E2-D15**: `disagree` (§3).
- **RE2-D18**: `disagree` on its unbounded-read half (§6, item 6). The brief this build was given
  had it `in progress (#932)`. #932 merged mid-build (`cb8139ee`), and the row was settled on
  evidence instead.

Order 2 is being worked by a session with no PR yet. Its seven rows stay `open` until that PR
updates them.

## 2. The coordinator's checks on committed data, re-run at 622786a2 (2026-11-09)

Each was re-run in this build on the committed files, not taken from the brief.

- **RBC-D1, live.** `render._fmt_customers` counts `;`-separated pieces of the capped roster, and
  the cap's "…(+N more)" tail is one more piece. So any roster over 30 prints **31**. True counts
  (30 listed + N) on the eight pages it hits: AMZN 726, EPAM 181, GOOGL 653, LLY 54, NFLX 49,
  NKE 34, UBER 36, V 351. NCNO also prints 31 and is right by coincidence (30 + 1). Read from
  `frontend/dossiers/*.md` and `mechanical.concentration.customers` on the 27 pages that carry a
  roster.
- **RD-D1, live.** MCK's impairment headroom of **$12,950.0M** is goodwill $11,272.0M as at
  2026-09-30 plus intangibles $1,678.0M as at **2012-06-30**, read from
  `mechanical.capital_allocation`. Across all 28 pages, five pair the two balances at different
  dates: AMZN, AORT, MCK, TGT and BURL. Document 14 names four because it leaves out the six
  extractor-test companies, BURL among them.
- **RA-D1, live.** PARR's page prints "GAAP-EPS surprise: FY2006 +0%, FY2007 +0%, FY2008 +0%,
  FY2009 +0%, FY2010 +0%" (`frontend/dossiers/PARR.md`, and the same line in
  `data/dossiers/PARR/dossier.md`).
- **RG-D16, live.** `data/graph_coverage.json` (last written 2026-06-26, `be4268e6`) holds **27**
  edges judged `unsupported` of 339. **No edge carries a reason field at all**, so a judge failure
  cannot be told from a real "unsupported".
- **RG-D19, live — and the two counts measure different things.**
  - **The coordinator's count reproduces:** **944** `verbatim` fields over 40 words, on all 28
    pages. But **853** of them quote CIQ **Key Developments**, **49** quote 10-Q filings, and only
    **42** (on 14 pages) quote a transcript.
  - **The transcript text lies elsewhere:** **384** `following_context` fields over 40 words, all
    from transcript rows, on 26 pages.
  - **Document 14's count reproduces exactly on its own boundary:** **848** transcript rows on
    **25** pages, with BURL excluded as a test company. Those are Tier-B (`llm-fenced`) rows
    sourced "CIQ transcript"; there are 881 with BURL.

  So the ruling RG-D19 needs (§5.0 row 60) has two parts:
  - **Transcript text:** the following-context passages, plus 42 long quotes.
  - **Key Developments text** is CIQ content, and a question of its own. The CLAUDE.md rule names
    "an article's or transcript's text".
- **The six strict xfail pins** in `tests/test_pages_await_parser_rebuild.py` all still **XFAIL**:
  E2-D5 (FUBO), E2-D10 (VITL), E2-D12 (VRRM), E2-D11 (EPAM, WERN, MVST), E2-D15 (WERN, NFLX) and
  E2-D16 (VITL). Run: `pytest tests/test_pages_await_parser_rebuild.py -rxXs` gave 6 xfailed.
- **D-D1's live case.** WLK's page is at extraction version **`2026-10-09.3`** (assembled
  2026-10-26). Main's current version is `2026-11-07.gap-test`.

## 3. The dispute: E2-D15's NFLX half is fixed

Document 15 marks E2-D15 partly fixed, saying in part that the WERN and NFLX pages were not
rebuilt. **NFLX's was.** The page was assembled 2026-11-05T11:58Z and committed in #918
(`4634df3d`). Its 10-Q `0001065280-26-000291` reads `maturity_wall` = `located`,
`within_12m_total` = **3194.0**, `basis` = **"principal and interest"**. Those are exactly the three
values the strict pin asserts for NFLX.

The evidence is the test's own helper: `_filing("NFLX", "0001065280-26-000291")` returns them on
the committed JSON. The pin still xfails only because of **WERN**: `_filing("WERN",
"0000793074-26-000140")` reads `not_stated`, total None. Three things remain open under the row:
- WERN's half;
- the tranche and commitment readers that read millions only;
- the V2-N1 regression.

Our status is `disagree` for the NFLX half only.

## 4. RF-D7 is live on GOOGL — an operator decision, recorded here, not fixed

Document 14 lists RF-D7 as not determined (it did not check committed rows). The committed ledger
settles it. GOOGL's BUY (`V-GOOGL`) was decided **2026-08-28** on an entry close dated
**2026-08-14**, 14 days earlier, and `vinci/scoring/harness.py:247` starts the forward clock at
`entry.entry_price_as_of`: the close's date, not the decision's.

**Boundary:** `data/snapshots/decision_ledger.jsonl` at `622786a2`, 7 rows. The 5 decision rows
have close-to-decision gaps of 1 (IT), 1 (SMPL, 07-21), 1 (SMPL, 08-05), 4 (VRRM) and 14 (GOOGL)
days; the 2 others are closes.

Whether a sealed row's clock moves, and how a stale close is refused at sealing, touch the ledger
and the scorer: both are decision-path files, and the choice is the operator's. **No code changes
here.**

## 5. The live checks document 15 §5 asks for

- **No split in any ledger window** (settled). Polygon's splits reference, read 2026-11-09 through
  `vinci.eod.splits.default_splits`, shows none in (entry close, 2026-11-09] for VRRM (from
  2026-06-17), GOOGL (from 2026-08-14), SMPL (from 2026-07-20, which covers its 2026-08-04 entry)
  or IT (from 2026-07-20). The most recent recorded splits are GOOGL 2022-07-18 and IT 1996-04-01;
  VRRM and SMPL have none on record.
- **The weekly job's push to `main` would be refused** (settled from settings, not tried). Read
  2026-11-09 through `gh api …/branches/main/protection` (no rulesets):
  - `main` requires a pull request, but with **0** approving reviews: "a PR", not "a reviewed PR".
  - It requires the `gate` status check, and blocks force-pushes.
  - Admins are not enforced, and there are no bypass allowances.

  `.github/workflows/weekly-screen.yml` pushes with the workflow's own token (`contents: write`),
  so the push would be refused. The job last ran 2026-09-23 (failure) and last succeeded
  2026-08-25. This bears on RH-D10.
- **Still open:** whether the R2 bucket is private, and how SEC treats two machines at 8 requests
  a second each. Both need live access the operator holds. Neither may be tested by probing the
  limit.

## 6. What does not reconcile (or reconciles only on a stated boundary)

1. **126, not 127.** Document 14's Appendix A has 126 R-IDs. The pack's master list has 127,
   because it keeps RG-D22, which document 14 folds into RH-D5 as one defect. RG-D22 therefore has
   no row of its own.
2. **RG-D19:** the 944-against-848 split above. These are two populations, not one count that
   disagrees with itself.
3. **RD-D1:** five pages on our corpus against document 14's four; BURL is the fifth.
4. **RBC-D1:** document 14 says eight pages. A ninth, NCNO, prints the same figure correctly.
5. **Five asked IDs are named in no order:** A-D13, A-D16, BC-D3, BC-D5 and BC-D6. Document 15's
   Appendix A marks all five not fixed, and each is "no production caller: fix or remove".
   BC-D3, BC-D5 and BC-D6 sit in `vinci/ciq/relationships.py` with RBC-D7 (order 5), so removing
   that module would close them together.
6. **RE2-D18's unbounded-read half was already bounded at `622786a2`, so we disagree.** Document
   14 reads it from `mechanical.py`'s two call sites, which apply no date. But the bound sits one
   layer down: since #884 (`ae016a68`, 2026-11-03), assembly reads EDGAR through `AsOfEdgar`,
   whose `recent_filings` drops every filing dated after the page's price date.
   - **Shown at `622786a2`**, in a throwaway checkout. LLY was assembled with its 2026-10-16 price
     date, using #884's pin harness (`tests/test_asof_cut.py::_assemble_lly`). It fetched neither
     the 2026-10-29 results 8-K (`0000059478-26-000104`) nor the 10-Q filed with it
     (`0000059478-26-000108`).
   - **With the cut removed**, `recent_filings` returning every row, both are fetched and the
     probe fails. The 10-Q was checked on its own as well.
   - #884's pin covered the 8-K. #932 (`cb8139ee`) added the 10-Q to it, and names what the cut
     leaves out.
   - The other half, acceptance times and undated filing extracts, is §4.
7. **RF-D7** is "not determined" in document 14 and live on GOOGL (§4).
8. **Branch protection:** the brief this build was given said "a reviewed PR". The setting is a PR
   with 0 approvals (§5).
9. **The STATE.md identifier lint misreads audit IDs.** Its pattern matches `[SD]\d{1,3}` after any
   hyphen. Today 248 audit-ID tokens (`A-…`, `E2-…`, `G-…`) in STATE.md and the records pass only
   because their numbers happen to match an entry. An audit ID numbered past the last entry — two of
   document 11's G0 IDs, written here as `A-D17..24` — would red it. Reported, not changed: this
   build does not touch that test.

**HOW VERIFIED.**
- **The checks** in §2 to §5 were each re-run in this build: committed JSON through the repo's own
  readers (`render._fmt_customers`, the pin file's `_filing()`), `pytest` on the pin file, the live
  Polygon read, and the GitHub settings read.
- **The 178 rows** were generated from document 14's Appendix A and document 15's §3, §4 and
  Appendix A by a scratch script that is not committed. It asserts 126 R-IDs and 49 document 11 IDs
  and no ID outside them.
- **The lint** runs on the live log, and against one planted bad row for each thing it rejects.
  - Each check was disabled in a scratch copy of the test, one at a time. All **14** mutants turn a
    pin red. Among them: no duplicate check, an unexpanded run, any status allowed, every commit
    "reachable", every PR "merged", only the first scope block read, and a helper counted as a
    test.
  - Its git checks use real failure shapes: `4449189d`, #923's squashed branch head that #928 found
    unreachable from main, and #917, closed unmerged on 2026-11-05.
  - Its good row names real merged work: `622786a2`, #927 and an existing test node.

**BOUNDARY.**
- **Page counts** are over the 28 committed `data/dossiers/*/dossier.json` at `622786a2`, all names
  included unless stated.
- **"Over 40 words"** is a whitespace split of the stored field.
- **Ledger counts** are over the 7 committed rows.
- **Graph counts** are over the 339 edges in `data/graph_coverage.json`.
- **Live reads** were made 2026-11-09.
- **ID counts** come from document 14's Appendix A and document 15's Appendix A, as held by the
  operator.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A `fixed` row lands one step after its fix.** The lint can verify only what `origin/main`
  already holds, so a fix PR sets its rows `in progress (#N)`. After #N merges, the next PR that
  touches the log, or the coordinator's sweep, flips them to `fixed`. A merged-but-unflipped row
  reads `in progress` while it is done.
  - Accepted, because the alternative is a lint that cannot tell a merged PR from a hoped-for one.
  - Falsifier: an `in progress (#N)` row whose #N merged more than a week earlier.
- **"Merged" is read from `main`, offline, not from GitHub.** A PR counts as merged when a
  first-parent commit on `origin/main` ends its subject `(#N)`, or reads `Merge pull request #N`.
  One known case differs from GitHub: #579's work landed as `f7248d33` while GitHub shows #579
  closed. The lint's reading is the one that matters here, since the work is on `main`.
  - A rebase-merged PR with no `(#N)` cannot be named by number; name its commit instead.
  - A test node's parametrize id is not checked. Doing so needs `pytest --collect-only`, which
    imports every module.
- **Two rows for one defect** (the "=" pairs, and RA-D10 with RBC-D2) can drift apart. The lint
  does not check that they agree; the log's header names the pairs.
- $0. No model call, no page rebuilt, no product code changed.
## Amendments

**2026-11-09 — AORT is retired (operator, verbatim: "retire AORT fully").** Order 2's done-when in §1
names AORT among the twelve pages to rebuild; it is eleven now. AORT's page left the corpus, so its
part of RBC-D1 (no count until re-assembled) and of RD-D1 (its goodwill and intangibles at
different dates) reads `not fixing: name retired (operator 2026-11-09)` in each row's page column.
Each row's status is unchanged for its other pages. The §2 counts were measured on 28 pages at
`622786a2` and stand on that boundary. `docs/records/2026-11-09-aort-retired.md`.

### 2026-11-10: R2 bucket privacy settled

R2 bucket privacy settled: private (operator, 2026-11-09).
- This closes §5's "Still open: whether the R2 bucket is private". It is settled by the
  operator's statement, not by a probe; none was made.
- It is recorded by the RG-D19 / RG-D8 stream (`docs/records/2026-11-10-driver-facts-not-quotes.md`),
  whose private evidence store relies on it.
- How SEC treats two machines was settled separately, from SEC's own pages (#939).
