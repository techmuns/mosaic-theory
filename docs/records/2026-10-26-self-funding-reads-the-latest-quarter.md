---
status: open
date: 2026-10-26
prs: []
supersedes:
superseded-by:
---

# The self-funding line's OCF leg reads the LATEST quarter, made discrete from the year-to-date — it read a stale fiscal Q1 on 25 of 27 pages, five pages' sign flips, and all five syntheses quote the old read

**WHAT.** `mechanical._latest_quarter_ocf` (new; `_latest_quarter_ocf_positive` is now its sign)
reads the latest cash-flow period filed and makes it DISCRETE: the 3-month fact where the filer
tags one, else the year-to-date less the prior year-to-date from the same start, through
`ebitda_recon._quarter` (Q2 = H1 − Q1, Q3 = 9M − H1, Q4 = the 10-K's year − 9M). A latest period
that cannot be differenced reads UNKNOWN — never an older quarter. `_quarter` gains a `filed_by`
cut that applies to BOTH legs of the difference, so a prior year-to-date restated later is not the
one the reader of that day had. The line's cite, written at assembly, now NAMES the quarter
(`EDGAR OCF sign, quarter to 2026-06-30 + CIQ LTM FCF sign`). The sign feeds three things: the
`self_funding` line (main body, "Leverage & survival"), the synthesis prompt (`self-funding
(two-input read)`), and the scorecard's `fcf_sign_vs_edgar_ocf` through `self_funding_check`.

**WHY.** The read took the latest fact of ≤100 days. A 10-Q tags cash flow year-to-date, so for
most filers the only such fact is the fiscal FIRST quarter (found in #805's triage,
`docs/records/2026-10-26-revenue-and-ocf-against-the-filings.md`). Re-measured here, same
boundary: a Q1 on 25 of 27 pages (AMZN and NFLX tag a discrete Q2); on 24 of those a later period
was already filed (NCNO's Q1 is its latest). NKE's page of 2026-09-30 read the quarter to
2025-08-31. Stale is half of it; the other half is direction: a first quarter is where annual
bonuses and working-capital builds land, so the read leaned negative — EPAM, WLK, PARR and CNXC
are all negative in Q1 and turn after.

**THE TWO DECISIONS.** The operator asked for the answer an expert public-markets team would give
(2026-10-26); this is that answer, acted on, not an operator ruling.
1. *Definition:* the latest discrete quarter. A line labelled "latest-Q" that reads a quarter 3–12
   months old is a period error, not a definitional choice; YTD differencing is how every analyst
   builds a discrete quarter. A single quarter is still seasonal — a tripwire for a recent turn,
   not the self-funding test (that rests on LTM FCF) — so the cite names the quarter it read. The
   cite, not the line: the line's text is what the refresh reproduces byte for byte, and the
   stale read went unseen for months behind a cite that said only "latest-Q".
2. *The five pages whose sign flips:* re-assemble them; do not patch the line under the old prose.
   Each synthesis cites the stale read, so moving the line under a KEPT synthesis would leave a
   page that contradicts itself (the refresh module's own rule: a reading the prose cites is never
   moved under it). None of the five carries a ledger decision (`decision_ledger.jsonl` holds
   GOOGL, IT, SMPL, VRRM — whose signs do not move). The re-assembly is paid and is the operator's,
   after #805 (which rewrites the same pages) and this PR merge — STATE.md §5.0 row 32 item (17).

**THE FIVE** (EDGAR as filed by each page's assembly date; $M; fixture and live EDGAR identical):

| page | assembled | read now (stale) | latest quarter | how | line now → line after | check |
|---|---|---|---|---|---|---|
| AORT | 2026-08-18 | Q1 to 2026-03-31, +1.2 | to 2026-06-30, −1.3 | H1 −0.1 − Q1 | MIXED (OCF > 0, FCF < 0) → MIXED (both < 0) | differ → agree |
| BRBR | 2026-09-28 | Q1 to 2025-12-31, −3.1 | to 2026-06-30, +79.3 | 9M 65.0 − H1 −14.3 | MIXED → YES | differ → agree |
| CNXC | 2026-08-18 | Q1 to 2026-02-28, −83.2 | to 2026-05-31, +257.9 | H1 − Q1 | MIXED → YES | differ → agree |
| PARR | 2026-09-28 | Q1 to 2026-03-31, −40.7 | to 2026-06-30, +282.6 | H1 − Q1 | MIXED → YES | differ → agree |
| WLK | 2026-09-28 | Q1 to 2026-03-31, −94.0 | to 2026-06-30, +318.0 | H1 224.0 − Q1 −94.0 | MIXED → YES | differ → agree |

Each synthesis argues from the old read — WLK's key unknown: *"latest-quarter OCF is negative"*;
BRBR's, CNXC's and PARR's say the same; AORT's says it is positive. EPAM (Q1 −36.4 → Q2 −2.4) and
MVST (−22.8 → −10.5) keep their sign and still differ from CIQ's positive LTM levered FCF. AORT's
move to *agree* is two negatives of DIFFERENT measures — CIQ's LTM levered FCF and one quarter's
OCF — while CIQ's LTM OCF is positive and confirmed against the filings (#805); the check is
sign-only of two measures, as its description says, and a match there is not a CIQ confirmation.
Read today rather than as of the page dates, four of the five read the same quarter; CNXC's newer
10-Q (filed 2026-10-07) gives the quarter to 2026-08-31, +268.2 — same sign.

**THE SCORECARD, BEFORE AND AFTER** (`fcf_sign_vs_edgar_ocf`, 27 pages, one unit per page):

| | confirmed | differs, unexplained |
|---|--:|--:|
| BEFORE — the committed pages (2026-10-24 snapshot; unchanged) | 20 | 7 |
| AFTER — each outcome re-derived by the fixed reader as filed by its page's own date, IN MEMORY | 25 | 2 (EPAM, MVST) |

The AFTER row is a projection, not a committed state: no page is written by this change. It
becomes the committed count when the five are re-assembled — and then reads EDGAR as of THAT date.

**HOW VERIFIED.**
- **Read before built.** The census above, re-measured rather than taken from #805: 25 of 27 a Q1,
  24 of 25 with a later period filed. Every derived quarter in the table checked by hand against
  the raw facts (e.g. WLK: H1 2026 224.0, Q1 −94.0, both 10-Qs; BRBR: 9M 65.0 filed 2026-08-04,
  H1 −14.3 filed 2026-05-05).
- **Live EDGAR agrees with the frozen fixtures** for AORT, BRBR, CNXC, PARR, WLK, EPAM, MVST and
  NKE as filed by each page's date (`EdgarClient.companyfacts`, 2026-10-26).
- **The refresh, real run over the 27 committed pages** (`refresh.cross_check_transform`, EDGAR
  from the committed fixtures, network refused; nothing written): 22 pages reproduce their stored
  line under the fixed reader and keep their outcome unchanged; the five above are refused by name
  ("self_funding does not reproduce from the page's stored inputs") and nothing else is. FUBO is
  sealed (`known_wrong.json`) and its sign does not move.
- **Pins fail first.** Each sign pin was run against the OLD reader: WLK False (wants True), PARR
  True (wants False), AORT False (wants True), HWM False (wants True), NKE-without-9M True (wants
  None) — five of five fail. The pins (`tests/test_cross_check.py`), all on the committed
  companyfacts fixtures (frozen 2026-10-23), values at a named filed-by date, never the living
  pages: WLK's Q2 (+318.0); PARR's FY2024 Q4 from the 10-K (−15.5, a negative quarter in a year
  whose YTD and Q1 were positive — kills a read of the YTD's own sign); AORT's Q2 2025 (+15.0
  inside a negative half — the other direction); AMZN's discrete Q2 read as tagged; HWM's Q2 2020
  differenced from the Q1 AS FIRST FILED (+31.0; the 2021 restatement would give −52.0) and HWM's
  Q3 2017 with BOTH legs later recast (+172.0 as filed, −57.0 recast); NKE's Q4 (+1,637.0), and
  UNKNOWN when its nine months are removed (the old read served the Q1 to 2025-08-31); the cite
  naming the quarter. The live assembly test (`test_primary_source_assembly_mvst_live`) asserts the
  cite names its quarter.
- **Mutation.** 10 mutants of the new code in a scratch copy of the tree, 9 killed. The first run
  killed 7: "both legs unfiltered" and "filed_by not passed to `_quarter`" survived, because HWM's
  2020 restatement moved Q1 and H1 by the same amount — the HWM 2017 pin was added for them (found
  by scanning every fixture for a restatement that moves the derived quarter itself). The
  survivor: reverting the assembly call site's cite — pinned only by the live test, which skips
  without `data/manual/ciq/`.

**BOUNDARY.** Census and projection: the 27 pages committed at main 545403de
(`data/dossiers/*/dossier.json`), one unit = one page's OCF leg, EDGAR from
`tests/fixtures/companyfacts/` (frozen 2026-10-23) as filed by each page's own `assembled_at`
(2026-08-18 … 2026-10-21), the alias `extract_points` serves; measured 2026-10-26. The BEFORE
count is the committed snapshot `data/snapshots/data_quality/ciq/2026-10-24.json` (its
`inputs_sha256` 1cd4ebfe… equals the page set at 545403de, so the pages have not moved since);
the AFTER count is in memory over those pages. Live comparison: 8 names,
2026-10-26.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
1. **The five pages state a stale read until re-assembled** — the line in the main body and the
   synthesis that quotes it; the scorecard keeps counting their old outcomes (20/7). Accepted
   because the alternative contradicts itself, and recorded as §5.0 row 32 item (17).
   Falsifier: a sixth page, assembled before this merges, whose sign the fixed reader flips.
2. **One quarter is seasonal even when current.** The line can flip between YES and MIXED quarter
   to quarter with no change in the LTM; the cite now names the quarter so a reader can judge it.
   Not changed: the two-input rule itself.
3. **UNKNOWN where the latest period cannot be differenced** (0 of 27 today) — e.g. a filer in its
   first year after a fiscal-year change, before a same-start pair exists (FUBO changed its year
   in 2025 and differences today). Falsifier: an UNKNOWN line on a page whose filings carry both
   year-to-dates of the pair — that would be a reader defect, not a filer gap.
4. **A discrete fact under 80 days is no longer a quarter** (`_quarter`'s 80–100-day window; the
   old read took anything ≤100 days). Every ≤100-day fact the old read took on the 27 pages is
   88–91 days, so no page moves on this.
5. **The assembly call site's cite is pinned only live** (the mutation survivor above).
