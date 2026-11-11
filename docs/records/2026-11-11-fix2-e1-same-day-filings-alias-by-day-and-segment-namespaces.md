---
status: open
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# Fix request 2, SEC client (RE1-D7 and RE1-D10, order 4; RE1-D15, order 5): a same-day 10-K and 10-K/A resolve by a stated precedence and name the figure they restate, a past bar reads the EPS alias of its own day, and segment profit reads namespaces by URI. No page moves

**WHAT.**
- **RE1-D7** (`concepts.filing_precedence`, used by `latest_annual`, `annual_by_period`,
  `latest_instant`, `superseded`, `annual_line`'s summed legs, the P/E's own EPS pick
  (`screens.assemble.annual_eps_point_as_of`, found in review round 0), and net debt's `_at`,
  `latest` and stale reading).
  - **The defect.** companyfacts dates a filing to the day. Two filings of one period on one day
    tied on `filed`, and `max` served whichever row the response listed first. On TeamNostra's
    constructed blob, the same rows in reverse order served 90,000,000 instead of 150,000,000 and
    moved EBITDA from 185,000,000 to 125,000,000. `superseded` compared with a strict `<`, so it
    named no restatement either way.
  - **The fix.** On one day, a periodic report (10-K, 10-Q, 20-F, 40-F, or an amendment of one) is
    served over any other form, an amendment over the report it amends, then the greater
    accession. That is the fact layer's naming rule too. `superseded` counts a same-day filing the
    served one outranks as earlier, so the provenance line names the figure the amendment
    restates. Its "first filing" is the earliest day's, and on that day the original periodic
    report.
- **RE1-D10** (`concepts.served_series`, `ServedSeries`; `pe_current_and_percentile(history=)`;
  its two callers, `screens.assemble.enrich_with_fundamentals` and
  `dossier.mechanical._at_latest_close`).
  - **The defect.** The P/E range chose its EPS alias once, on the blob as of its reference date,
    and read every past bar through it. A filer re-tagging diluted EPS in a later 10-K left every
    bar before that filing with no EPS, though the EPS known that day stood under the old alias.
    On the constructed re-tag, the range read 2 points and was refused as too short.
  - **The fix.** `served_series` runs the alias walk as of every day a row of the concept's
    aliases was filed. On each day it equals the walk on the blob cut at that day. One difference
    is on purpose: the currency is judged once, at the reader's date. A range ranks one series
    against itself and must not change currency at a filer's switch. Each bar reads the alias
    served on its day. A range read under two aliases says so in the percentile's note, run by run
    with each run's first and last bar, so an alias the walk leaves and returns to reads as three
    runs (review round 0). The share-basis check runs on each alias the range can read, one at a
    time. `_at_latest_close` also stops walking aliases on rows filed after its
    close.
- **RE1-D15** (`segment_facts._canonical_prefix`, `_resolve_qname`).
  - **The defect.** Segment axes, members and elements were matched on the prefix the instance
    wrote. An instance binding the us-gaap namespace to `gaap` (valid XBRL) read as a
    single-segment filer, silently.
  - **The fix.** us-gaap, srt and dei are named by their URI under the prefix the constants use,
    the 2009-2010 releases at `xbrl.us` included (review round 0: matched on fasb.org and
    xbrl.sec.gov alone, such an instance lost its `dei:DocumentPeriodEndDate`).
    A dimension or member written as text is resolved through the instance's own bindings. A
    filer's own namespace keeps its prefix. A standard prefix bound to another URI matches
    nothing. A prefix bound to two URIs and used in a QName is refused, never guessed between.
- **Version row** `2026-11-11.same-day-filings-and-alias-by-day`, in both tables, re-pinned. The
  FPI1a source-scan guard (`test_every_reader_that_ranks_a_pe_reads_eps_in_the_filers_own_currency`)
  accepts `served_series` as the EPS read, with the same `currency=REPORTING` and `as_of`.

**WHY.** TeamNostra's done-when for order 4 is "each E1 case is a passing test". RE1-D7 is not
latent on the corpus. On this machine's 714 cached companyfacts responses, 152 same-day groups
state different values on the period's latest filing day, and 103 of them involve an amendment.
Stratasys's 6-K and 6-K/A of 2021-05-05 flip the sign of a dozen cash-flow lines. On the committed
fixtures one is live: ROST's cover count for 2010-11-18, filed 2010-12-08 as 19,084,540 in a 10-Q
and as 119,084,540 in its 10-Q/A. The fixture lists the 10-Q first, so row order served the typo.
RE1-D10 and RE1-D15 are latent on the corpus.

**HOW VERIFIED.**
- **TeamNostra's constructed inputs** (fix pack 2, `notes/E1_work`), at main `2b9b766c` and at
  this branch:
  - RE1-D7: base gives 150,000,000 as written and 90,000,000 reversed, `superseded()` None.
    Here it gives 90,000,000 both ways, naming 150,000,000 (0000999999-25-000004).
  - RE1-D10: base gives "only 2 P/E points (< 5)". Here it reads 105 observations, "EPS read
    under EarningsPerShareDiluted (2024-03-01..2026-02-13), then
    IncomeLossFromContinuingOperationsPerDilutedShare (2026-02-20..2026-02-27)".
  - RE1-D15: the prefix `gaap` gives None at base. Here it gives the same two segments as
    `us-gaap`.
- **`tests/test_fix2_e1_concepts.py`, 24 tests written first.** On main 20 fail. The 4 that pass
  are the later-day negative pin, the plain `us-gaap` prefix case, the committed-instance prefix
  check, and one row order that happened to win. Review round 0 added 3, each failing before its
  fix: the P/E's EPS pick on a same-day amendment (in both row orders), a 2009 taxonomy, and an
  alias left and returned to. 28 cases in all.
- **The series is the walk on the cut blob, measured on all 31 committed companyfacts fixtures.**
  Every multi-alias concept, every day a row of its aliases was filed: 14,167 of 14,167 days
  agree, in every currency and in USD. The served alias moves 73 times over those fixtures'
  histories (revenue, D&A, debt, pre-tax income). It never moves for diluted EPS.
- **The 27 committed pages at $0, main's code against this branch's**
  (`measure_pr1.py`, cache only, nothing fetched for companyfacts):
  - **What was read.** Each page's companyfacts came from the freshest copy any local SEC cache
    held: 16 from the primary's cache and 11 from one worktree's, all fetched 2026-11-11 (re-run
    after review round 0 on this state; the first run, on copies fetched 2026-11-10..11, gave the
    same result). Each was
    cut at the page's own price date.
  - **What was compared.** The EDGAR fundamental snapshot; net debt on every basis; every
    concept's annual-by-period point with its provenance line (2,701 points, 184 naming a
    restatement); every concept's latest instant; the P/E pair at the page's own EPS reading
    date, with bars read-only from one worktree's store (18 levels, 14 percentiles); and segment
    profit from each page's cited instance (10 of 10 blocks).
  - **Result.** 13,986 values, **0 move**. Every segment block re-reads to the committed page's
    rows, MCK's refusal included. All 12 committed instance fixtures (10 segment, 2 FPI) parse
    identically at base and here.
  - Four instances (NKE, PARR, TJX, UBER) were fetched once through the paced client, 8 requests.

**BOUNDARY.**
- **Cache scan.** 714 companyfacts responses and 9 XBRL instances in the primary checkout's SEC
  cache on 2026-11-11, every taxonomy, tag and unit in us-gaap and dei. A "same-day
  disagreement" is two or more accessions on a period's latest filing day whose values differ
  past `_same_figure`.
- **Fixture checks.** The 31 files under `tests/fixtures/companyfacts` at `2b9b766c`.
- **Page compare.** `data/dossiers/*/dossier.json` at `2b9b766c` (27 pages).
- **P/E bars.** One local store's bars (newest 2026-11-03). They reproduce the committed P/E
  level on 15 of the 21 pages that carry one. MCK has no bars there.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Two same-day originals are served by accession.** 49 of the 152 cached disagreements involve
  no amendment, and no rule can say which figure is right (Tilray's two 10-Qs of 2024-10-10). The
  served one is deterministic, and the other is named as the figure it restates.
  - The fact layer refuses such a day instead (`FactAmbiguousError`). The page readers cannot
    refuse without a new UNKNOWN on every reader of the period.
  - Falsifier: a committed page that prints a same-day 10-Q pair's greater-accession figure where
    the filer's own later filing states the other.
- **A range read under two aliases mixes two measures** (total and continuing-operations EPS) where
  the filer re-tagged. It is said in the note. Before, it read only the bars after the re-tag.
- **Not in this PR.** About 20 other `max(..., key=filed)` selectors under `vinci/dossier/` (e.g.
  `anchor.py`, `capital_allocation.py`, `ebitda_recon.py`, `cover_count.py`) keep breaking a
  same-day tie by row order. The theme-intelligence desk's P/E (`theme_intelligence.market`)
  still reads one alias for every date. Both are reported as follow-ups.
