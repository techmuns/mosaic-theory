---
id: 2026-10-26-revenue-and-ocf-against-the-filings
status: open
date: 2026-10-26
prs: []
supersedes:
superseded-by:
---

# CIQ's annual revenue and operating cash flow are set against the filings, period by period — the scorecard's two cheapest real checks, and the seven FCF-sign differences turn out to be definition gaps

**WHAT.** Two value-level checks join the CIQ source of the data-quality scorecard
(`vinci/quality/sources/ciq.py`), both INDEPENDENT, unit = one period (a fiscal year or the LTM):

| check | CIQ figure | second figure |
|---|---|---|
| `revenue_vs_xbrl` | the financial summary's Revenue row (Income Statement 'Total Revenue') | EDGAR XBRL revenue on the first alias reporting the period |
| `ocf_vs_xbrl` | the financial summary's CFO row (Cash Flow 'Cash from Ops.') | EDGAR XBRL `NetCashProvidedByUsedInOperatingActivities` (else the continuing-operations tag) |

Both read one stored block, `mechanical.financial_summary.statement_reconciliation`
(`vinci/dossier/statement_recon.py`): one row per actual column of the annual table where CIQ
reports a figure — its period end, CIQ's figure, the filing figure, the tag, the construction, the
gap and a `different` flag (beyond 0.5% of the filing figure AND $1M). Confirmed when not
different; DIFFERS, STATED where the filings carry CIQ's figure themselves — another alias for the
same period (`other_tag`) or an earlier filing's figure for the year (`earlier_accession`);
DIFFERS, UNEXPLAINED otherwise; UNCHECKED where no alias reports the period as filed by the page's
assembly date. A block whose CIQ figures are not its own table's is NOT RUN (stale), never scored.

**WHY THE PAGE CARRIES IT (decided, per the brief's item 3).** Read first, before any code: every
committed page stores CIQ's annual Revenue and CFO as structured `values` (27 of 27), but **no
period end per column** (the column labels carry a year, and a 52/53-week filer can end two fiscal
years in one calendar year) and **no EDGAR revenue or OCF figure at all** (the EBITDA block is
quarterly; `anchor.ltm_fcf` is OCF − capex; `sbc` carries one year's revenue inside a ratio). The
quarterly table carries display strings only, which the house rule forbids parsing. Fetching EDGAR
at scoring time would make the snapshot depend on what is filed on the day it is scored (a later
restatement would read as CIQ's error) and break the byte-for-byte re-derivation the scorecard pins.
So the reconciliation is written where both sides are in hand — at assembly, like the EBITDA one —
and the scorecard stays a pure function of the committed pages.

**THE BACK-FILL.** `refresh.statement_recon_transform` put the block on the 27 committed pages
(commit 2 of this PR) through `refresh_fleet`. It reads the CIQ export for ONE thing the page
lacks, the period ends, and only after PROVING the export is the page's own: every Revenue and CFO
figure the export gives must equal the page's stored value in the same column, none missing.
Measured: 27 of 27 reproduce exactly (from the primary checkout's `data/manual/ciq/`, read only).
EDGAR is read as filed by each page's assembly date. The committed companyfacts fixtures and a live
fetch build the identical block on 27 of 27.

**THE ANSWER, 2026-10-26** (the 27 committed pages after the pass; snapshot
`data/snapshots/data_quality/ciq/2026-10-26.json`):

| check | periods | pages run | confirmed | differs, stated | differs, unexplained | unchecked | not applicable |
|---|--:|--:|--:|--:|--:|--:|---|
| `revenue_vs_xbrl` | 247 | 25 | 225 | 5 (WERN) | 0 | 17 | 2 (ORKA, TECX: CIQ reports no revenue) |
| `ocf_vs_xbrl` | 256 | 27 | 237 | 0 | 2 (TECX) | 17 | 0 |

- **WERN, stated (5 periods, FY22–FY25 and the LTM).** CIQ's revenue is Werner's `Revenues`
  line, 2.3–2.6% above the ASC 606 line the alias order reads first (FY24: $3,030.258M against
  $2,955.201M, both in the 10-K). A definition difference the filing itself states; Werner's FY17–FY21
  confirm on `Revenues`, the only alias it filed for those years.
- **TECX, unexplained (FY21, FY22).** EDGAR's FY2021 and FY2022 operating cash flow ($−98.0M,
  $−97.2M) were filed in 10-Ks of 2022-03-17 and 2023-03-23 and never refiled. Every 2023 period a
  filing from 2024-08-14 on covers IS restated — the year-to-dates in the 2024 10-Qs, and FY2023
  ($−63.2M as first filed, $−40.7M in the 10-K filed 2025-03-20; CIQ carries the latter and
  confirms). That is the shape of a reverse merger: the legal registrant's history before it, the
  accounting acquirer's after. INFERRED, not measured: that CIQ's FY21–22 are the acquirer's
  history too, which no filing in companyfacts restates. The page states no reason, so the status is
  unexplained; this record is the reading.
- **Unchecked, 17 on each line.** Years before the filer's XBRL reaches them (BRBR FY17, CNXC
  FY17–18, MVST FY18, NCNO FY18–19, SMPL FY16–17, UBER FY16, VITL FY17; ORKA's FY24 OCF); FUBO's
  five periods on both lines, because no EDGAR twelve-month fact ends at any of CIQ's period ends
  (2022-10-01 … 2025-09-27, a Saturday-nearest-September calendar) as filed by its page date; Visa's
  LTM on both lines, because its companyfacts carries no fact ending after 2026-03-31 filed by
  2026-08-18 while CIQ's LTM ends 2026-06-30; and BRBR's LTM revenue, because its 10-K tags
  `Revenues` and its 10-Qs the ASC 606 line — tags are never spliced, so no one tag carries the year
  and both year-to-dates.
- **BURL** confirms on all 11 revenue periods, 0.07–0.28% from the ASC 606 figure — between that
  tag and `Revenues`. Inside the tolerance; it IS a small definition difference the tolerance does
  not resolve.

**THE TOLERANCE IS NOT LOAD-BEARING ON THIS CORPUS.** Every confirmed period with a gap of $1M or
more sits within 0.28% (BURL); the nearest difference is 2.27% (WERN FY22). Any share from
0.29% to 2.26%, with the $1M floor, gives the same verdicts; so does any floor from $0.05M to $69M
(the smallest differing gap, TECX FY22). Below the floor, the largest confirmed share is 1.39% on a
$0.024M gap (MVST's LTM OCF) — the rounding of a near-zero figure. The 0.5% was set by
face validity (CIQ keeps three decimals of $M; half a percent is far past rounding), never against
an outcome.

**THE SEVEN FCF-SIGN DIFFERENCES ARE ALL DEFINITION GAPS (item 4).** `fcf_sign_vs_edgar_ocf`
(2026-10-24: 20 confirmed, 7 differ) compares the sign of CIQ's LTM LEVERED FCF with the sign of
EDGAR's latest SINGLE-QUARTER OCF. On each of the seven, `ocf_vs_xbrl` confirms CIQ's LTM OCF
against the filings, so CIQ's cash flow is not in question. Decomposed (sign of LTM levered FCF →
sign of LTM OCF → sign of the quarter the check reads):

| name | levered FCF | LTM OCF (CIQ = EDGAR) | the quarter's OCF (EDGAR) | what flips the sign |
|---|---|---|---|---|
| AORT | − | + | + (Q1 to 2026-03-31) | measure: levered FCF against OCF |
| MVST | + | − | − (Q1 to 2026-03-31) | measure: levered FCF against OCF |
| BRBR | + | + | − (Q1 to 2025-12-31, $−3.1M) | period: the LTM against one quarter |
| CNXC | + | + | − (Q1 to 2026-02-28, $−83.2M) | period |
| EPAM | + | + | − (Q1 to 2026-03-31, $−36.4M) | period |
| PARR | + | + | − (Q1 to 2026-03-31, $−40.7M) | period |
| WLK | + | + | − (Q1 to 2026-03-31, $−94.0M) | period |

None is a real disagreement. The sign check's verdicts are left as they are; it compares what its
check states it compares.

**FOUND, NOT FIXED (out of scope): the sign check's "latest quarter" is a fiscal Q1, months old.**
A 10-Q tags cash flow year-to-date, so the only ≤100-day OCF fact a filer files is its first
quarter; `mechanical._latest_quarter_ocf_positive` therefore reads the latest fiscal Q1. Measured on
the committed fixtures as filed by each page's assembly date: a Q1 on 25 of 27 pages (AMZN and NFLX
tag a discrete Q2), and on 24 of those a later cash-flow period was already filed — NKE's is the
quarter to 2025-08-31 on a page assembled 2026-09-30. Not a CIQ question (both signs it compares
are read correctly); a follow-up for that check.

**COVERAGE.** The 25 families keep their classes (8 independent, 4 internal, 10 single-source, 3
unchecked): `financials.annual_income_statement` and `financials.cash_flow` were already
independent. What moves is what they are guarded AGAINST — both now have an independent check for
all five failure classes (were: the EBIT margin's file / cell / definition, and the sign's file /
cell).

| failure class | independent | internal only | nothing, a second source exists | nothing, single-source |
|---|--:|--:|--:|--:|
| wrong file | 7 | 1 | 7 | 10 |
| wrong cell | 7 | 3 | 5 | 10 |
| wrong unit | 8 (was 6) | 3 | 4 (was 6) | 10 |
| wrong period or vintage | 7 (was 5) | 3 | 5 (was 7) | 10 |
| different definition | 4 (was 3) | 1 | 10 (was 11) | 10 |

The classes are DECLARED per check from what it compares (face validity): a value against the
filing's for the same period can surface all five — another company's export, another row, another
scale, another year, another construction of the line.

**HOW VERIFIED.**
- **Read before built.** The page census above (27 of 27 carry structured Revenue and CFO
  values; no period end, no EDGAR figure). Then a feasibility pass against the workbooks and the
  filings, before any code: every export reproduces its page's two rows exactly, and CIQ carries the
  latest-filed figure — within $1M on 451 of the 469 periods both sides report (11 more confirm
  inside the tolerance, all BURL; 7 differ).
- **The real run.** `vinci audit quality --source ciq` on the 27 back-filled pages at 646b1fdf,
  exit 0 — the table above is its output (the 2026-10-26 snapshot); a dry run of the back-fill
  before it was written gave the same counts.
- **The back-fill moved only what it should.** Checked page by page against HEAD: 108 paths, each
  `dossier.json` gaining only the block and one `layer_refreshes` entry, each `dossier.md` that
  entry's one line, each frontend mirror byte-identical to its page.
- **Each check fires, on a committed page perturbed in memory** (AMZN, every period confirmed):
  revenue FY23 ×1,000 (unit) and FY25 set to FY24's figure (period) read 2 unexplained, the CFO row
  given FY24's revenue (cell) reads 1 unexplained — each rebuilt through the back-fill against the
  committed companyfacts — and a table moved without its block reads NOT RUN (stale). The stated path
  fires on real data (WERN, 5 periods); the earlier-filing path on a frozen pin (LLY's FY2017 as first
  filed, before its 2019 recast).
- **Pins.** `tests/test_statement_recon.py`: the producer on the REAL committed companyfacts with a
  placed CIQ figure (fiscal year, the composed LTM, a 10-Q twelve-month column, the filed-by cut, the
  tolerance edges and floor, both named reasons, the alias order, USD only, the end-date slack),
  the export reader against `financial_summary_annual` on a synthetic export (the twin), the
  back-fill's proof and refusals, the assembler's call site, and END TO END: every committed block
  is exactly what the back-fill rebuilds from its page and the committed filings.
  `tests/test_quality_ciq.py`: every status on a frozen fixture built from the real types (the
  sentinel never reaches the card), the staleness guard, the corpus counts, and the perturbation.
- **Mutation.** 28 mutants of the new production code in a scratch copy of the tree
  (`statement_recon` 19, the assembler's call site 1, the back-fill 3, the scorecard 5): 28 of 28
  killed on the first pass. The end-to-end pin killed one the unit pins could not see — dropping the
  fiscal-year guard composes FUBO's four fiscal years on both lines from a December year's
  year-to-date, eight false differences.

**BOUNDARY.** Every count: the 27 pages committed at 646b1fdf (`data/dossiers/*/dossier.json`); a
unit is one actual column of the annual table (each fiscal year and the first LTM) where CIQ reports
a figure; EDGAR as filed by each page's own assembly date (2026-08-18 … 2026-10-21); measured
2026-10-26. The FCF-sign baseline is the 2026-10-24 snapshot (`git_head` dd4eb428). The Q1 census
reads `tests/fixtures/companyfacts/` (frozen 2026-10-23) with the same filed-by dates.

**WHAT IT COSTS / WHAT IS ACCEPTED.** (1) 0.5% cannot see a period shift on a name growing under
half a percent a year; a flat-revenue name's adjacent year would confirm. Falsifier: a confirmed
period whose figure equals the adjacent year's filing. (2) The block is written once and can go
stale when a later refresh moves the table; the scorecard then reads NOT RUN, never a pass, and the
next assembly or back-fill rebuilds it. (3) The back-fill needs the licensed export for the period
ends; a page whose export is gone cannot be back-filled, only re-assembled.
