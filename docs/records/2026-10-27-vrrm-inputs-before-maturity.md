---
id: 2026-10-27-vrrm-inputs-before-maturity
status: shipped
date: 2026-10-27
prs: [818]
supersedes:
superseded-by:
---

# VRRM's two unexplained scorecard units are explained in code — CIQ's EBITDA leaves out an impairment the release states in a table, and CIQ's guide was checked against a release filed after it; the wall stays unchecked by definition, and the scoring rehearses clean on a store copy

**WHAT.** VRRM's decision-ledger row (`V-VRRM-screen2-20260617`, AVOID_TERMINAL, entry $4.71 as of
2026-06-17, 180 days, IWM) is the fund's first to mature: **2026-12-14**, the harness's
`entry_price_as_of + horizon_days` (`vinci/scoring/harness.py`). Lane L4 of data-integrity wave 1
asked for every input to its page and its scoring to be confirmed or explained before then.

The committed scorecard (`data/snapshots/data_quality/ciq/2026-10-26.json`, re-run on main
`47d8ca27` with the same result) carried three VRRM units that were neither:

| check | committed | cause | fault | after this branch's code lands on the page |
|---|---|---|---|---|
| `ebitda_vs_xbrl`, quarter to 2025-12-31 | differs-unexplained (CIQ $81.279M vs $71.927M rebuilt, +$9.352M) | CIQ leaves impairments out of EBITDA; the quarter's release states "Impairment of long-lived assets and right of use assets 9,352" in its cash-flow table "($ in thousands)", in no sentence | ours: the matcher read only prose "$X million" | **differs-stated** — the header and the row quoted verbatim |
| `guide_vs_release` | differs-unexplained (CIQ 985–995 vs release 945–965) | CIQ's guide row is DATED 2026-05-26, the day of the release stating $985–995M; it was set against the 2026-08-05 release that cut the guide, after CIQ's export (Estimates, 2026-07-30) | ours: a cross-vintage comparison | **confirmed** against the release of CIQ's date; the 2026-08-05 cut is named in the line |
| `wall_vs_10q` | unchecked | the 10-Q (0001193125-26-335490) states no maturity schedule — its only 12-month figure is the balance sheet's "Current portion of debt 10,000" ($ thousands: term-loan amortization and equipment financing) — and CIQ's panel dates each instrument at its final maturity (term loan 2028-03-24, notes 2029-04-15, revolver 2030-10-17), so nothing falls in [2026-06-30, 2027-06-30) | a definition gap, not a defect: reading the current portion would compare amortization against final maturities and print a divergence neither side has | unchecked, explained here |

Every other VRRM check is confirmed or not applicable/not run with the reason the scorecard prints;
the six price checks are confirmed (1,287 bars, close against Tiingo).

- **`vinci/dossier/ebitda_recon.py`** — where no sentence matches, `_matching_row` reads a table
  row's FIRST figure under the nearest preceding "(… in thousands …)" header, within `MATCH_TOL` and
  one $1K unit — only where the column heading between that header and its first row names a year
  and its first year is the latest, so the first column is the current period (Codex, round 1: 30
  of the 258 thousands headers in the committed pages' releases list the prior period first —
  nCino's "Three Months Ended April 30, 2025 2026" among them). The quote is the header with that
  heading, and the row, verbatim, joined by an ellipsis — "($ in thousands) 2025 2024 … Impairment
  of long-lived assets and right of use assets 9,352" — so it re-matches on its own (the
  committed-corpus invariant) and passes `vinci/verbatim` as an ELIDED span. A row under a millions
  header, or under none, is never read.
- **The guide** — `mechanical._guide_verification` is now the ONE composition, called by assembly
  (`_release_lines`) and by `refresh.cross_check_transform`, which held a hand copy. It sets CIQ's
  guide against the newest guide-bearing release filed by CIQ's guide date plus
  `_GUIDE_FILING_LAG_DAYS` (3: an 8-K accepted after EDGAR's 5:30 pm cutoff is dated the next
  business day). A later release guiding something else is named, never preferred
  (`primary_source.guide_verification_read(later_release=…)`). The date rides with the numbers out
  of `ciq_sheets.revenue_guide_lohi` / `revenue_guide_from_rows` (4-tuples now), as the period did
  on 2026-08-12. An undated guide keeps the old comparison.

**WHY.** The scorecard counts a stored outcome; it cannot tell a vendor's definition from a
comparison that tested nothing. Both VRRM differences were the second kind. A gap that the quarter's
own release states to the thousand is explained, and a guide set against a release filed after it
measures management's revision, not CIQ. The scorecard source (`vinci/quality/`, lane L1) was not
touched: each unit moves because the page will state its reason.

**HOW VERIFIED.**

- *Fail first.* `tests/test_ebitda_recon.py` (three tests: VRRM's, SMPL's and nCino's real
  release text and VRRM's companyfacts points, frozen) and `tests/test_guide_check_vintage.py` (five
  tests, VRRM's four releases' guidance and CIQ's row, frozen from the committed page) were red
  before the code and green after. Negative pins: the prior-year column "9,349"; one unit off; a
  millions header; no header; a heading without a year; nCino's prior-period-first heading; a prose
  amount still winning; a same-vintage vendor misread still differing; a release one day past the
  lag; an undated guide; a later release restating the same guide.
- *Corpus before synthetic — the table reader* (27 committed pages, 34 quarters flagged
  `different`, main `47d8ca27` plus this branch): the 4 stored prose quotes reproduce byte for byte;
  2 quarters gain a table quote (VRRM 2025-12-31 impairment 9,352; SMPL 2025-11-29 integration
  expense 5,918, both items CIQ normalises out); 1 hit in 544 shifted-gap trials (each quarter's
  gap moved by ±3 to ±307 thousand-units, the table reader alone): VITL's $1.359M quarter shifted
  to $1.382M meets "(Amounts in thousands) … Principal payments under finance lease obligations
  (1,381". The prototype without the first-figure rule also hit VRRM's prepaid-expenses prior-year
  column, which is why the rule exists. The review widened the header to "(Dollars in millions)"
  forms — missed, the rows under such a header inherited an earlier thousands header, 1,000x off —
  and that wider read is what exposed VITL's table.
- *Corpus before synthetic — the guide* (same 27 pages): 16 of 16 pages with both dates have CIQ's
  guide date equal to a release's filing date to the day. Rebuilt with the new composition, 26 guide
  lines are byte-identical to the old composition's and 1 moves: VRRM, differ → agree.
- *Landing preview on real inputs* (writes nothing): VRRM's reconciliation rebuilt from the
  assembler's CIQ copy (`mosaic-theory-ta`, read-only; its quarterly export's sha is the page's band
  stamp), EDGAR and the release — every figure as stored, the quote added — and the guide line
  rebuilt from the page's rows; scored by the scorecard's own check functions:
  `ebitda_vs_xbrl` {confirmed 3, differs-unexplained 1} → {confirmed 3, differs-stated 1};
  `guide_vs_release` {differs-unexplained 1} → {confirmed 1}; `wall_vs_10q` {unchecked 1} unchanged.
- *The scoring rehearsal* — RUNBOOKS §l on a COPY of the primary's store (`data/vinci.db`, bars
  through 2026-08-05), every write in a scratch data dir: `orchestrator.run_monthly(as_of=
  2026-10-26)` with `TIINGO_API_KEY` and `POLYGON_API_KEY` set (the primary's `data/cache` linked;
  ~30 minutes, the price refresh at the plan's rate). The store copy held no ledger rows, so the
  run seeded the 7 committed ones; `decision_ledger.jsonl` hashed `43d77c50…` before and after, in
  the repo and in the scratch copy, and the repo's `data/snapshots` is untouched. The report's
  basis line reads TOTAL return with price return beside it; 0 resolved, 4 pending (screen
  origin). VRRM's inputs, on the refreshed copy:
  - entry $4.71 as of 2026-06-17, the stored close of that session exactly; horizon 180 days →
    matures **2026-12-14**, 49 days after the run; not closed; benchmark sealed IWM = the one the
    harness applies, so `BenchmarkMismatchError` cannot fire for it;
  - 91 VRRM bars in [2026-06-17, 2026-10-26] and 91 IWM bars, the same sessions, no gap;
  - Tiingo dividends: VRRM none in the window (it pays none), IWM one (2026-09-15, 0.2632%) —
    neither raises, so `TotalReturnUnknownError` would not stop the row at maturity;
  - interim mark as of 2026-10-26 (not resolved, feeds no number): total −34.39% (price −34.39%),
    IWM total −4.20% (price −4.45%).

  Scored again with the date set to 2026-12-14 on the same store (bars end 2026-10-26), VRRM
  RESOLVES and its exit is the 2026-10-26 close ($3.09) — FOUND item 2 below. And with only
  the AVOID leg resolved the BUY−AVOID spread stays n/a: the first BUY legs (IT, SMPL) resolve
  2027-01-16, so VRRM is the first outcome the ledger resolves, and the spread's first VALUE
  lands then.

**WHAT IS NOT DONE, AND WHY.**

- **The page is not re-assembled** (wave-1 rule: no page re-assembly inside code PRs). VRRM refuses
  re-assembly anyway: its CIQ TEV is dated 2026-07-28, past the 45-day ceiling (§5.0 row 28), and no
  newer export exists — the assembler's copy (`mosaic-theory-ta/data/manual/ciq/VRRM`) and the Drive
  mirror hold the same files (financials 2026-06-19, comps 2026-07-29, estimates 2026-07-30). The
  units move at the one paid pass after the operator re-exports VRRM's full set following its Q3
  10-Q (§5.0 row 32 item (20)).
- **After that re-export, one unit will probably differ again, and this branch does not explain it.**
  The LTM will then include the quarter to 2026-06-30 (operating loss $32.779M), which carries TWO
  impairments its release states separately — goodwill $64.037M and intangibles $40.354M. If CIQ
  leaves both out, the gap is their sum (~$104.4M), and no single stated amount matches. Composing
  sums of stated amounts multiplies the coincidences the precision rule keeps out; whether to do it
  is a decision for when CIQ's figure exists, not a guess now.
- **IT and SMPL** (both mature 2027-01-16) are not worked: IT has 3 open units (the EBITDA quarter
  to 2025-09-30 at +$154.049M, guide and wall unchecked) and SMPL 10 (4 EBITDA quarters — this
  branch explains the one to 2025-11-29 — revenue and OCF 2 unchecked each, guide unchecked on a
  quarter-vs-year period mismatch, wall unchecked). Recorded in row 32 item (20).
- **Row 27 item (1)**, VRRM's route-A "net debt / FY26 adj-EBITDA": it touches the PAGE, never the
  scoring (`score_ledger` reads the ledger row, stored prices and Tiingo dividends — no page field).
  On the page three lines print "~2.6x fwd-adj (net debt $985M / FY26 adj-EBITDA $380–$385M)"; the
  builder's figure today is $979.9M (EDGAR, filed 2026-08-05), so the dollar figure moves $5M and the
  ratio prints ~2.6x either way (2.58x vs 2.56x). The larger drift is the denominator, by the design
  of `_revised_guidance` (drawdown vintage): it divides by the 2026-05-26 guide; on the current
  2026-08-05 guide ($360–370M) the ratio is 2.68x. Reported, not changed.

**FOUND, NOT FIXED.**

1. **CIQ's capital panel names a refinanced loan by its old maturity.** It lists "2021 Term Loan Due
   2028" (2028-03-24, $687.1M). The 10-Q says the October 2025 refinancing produced the "Amended Term
   Loan" maturing 2032-10-15 (its balance at 2025-12-31, $687,082K, is CIQ's principal). VRRM's page
   prints the 2028 date in its catalyst calendar ("2021 Term Loan Due 2028 $687.1M matures"), its
   liquidity line, and a synthesis key-unknown about "the 2028 term-loan wall". No scorecard check
   compares panel maturities with the filings. The operator item: confirm the November re-export
   carries 2032; if it does not, it is a vendor error to flag before the pass.
2. **A resolved row reads whatever bar is last on or before its horizon, however old.**
   `score_ledger` has no exit-bar freshness guard (`baseline.bar_on_or_before`). `run-monthly`
   refreshes prices first, but `ingest_prices` reads an empty grouped-daily as a holiday, so a run on
   2026-12-14 IST — before the US close — finds no 2026-12-14 bar and resolves VRRM on Friday
   2026-12-11's close. Run it on 2026-12-15 IST or later and check the exit session. A guard is a
   scoring change (decision path), proposed separately.

**BOUNDARY.** Scorecard counts: `data/snapshots/data_quality/ciq/2026-10-26.json` (27 committed
pages, `inputs_sha256` e6e09ad9…), re-run on main `47d8ca27`, unit = quarter for `ebitda_vs_xbrl`,
page for the rest. Prices: `data/snapshots/data_quality/prices/2026-10-26.json` (a store of 1,287
sessions 2021-09-01 → 2026-10-16). Table-reader corpus: 27 committed pages at `47d8ca27`, the 34
quarters each page flags `different`, the releases filed within 80 days after each quarter end,
read through the primary checkout's SEC cache on 2026-10-27. Guide corpus: the same 27 pages, CIQ's
revenue row of each page's guidance bridge, the releases each page stores. Route A: VRRM's committed
page and `fundamental_snapshot` on 2026-10-27. Rehearsal: the primary's store copied 2026-10-27, refreshed through 2026-10-26, the 7 committed ledger rows; bar counts are sessions in [entry, 2026-10-26].

**WHAT IT COSTS / WHAT IS ACCEPTED.** A table row is quoted as evidence, not attribution, exactly as
a sentence is; the precision rule ($1K, the first figure only) is what keeps coincidences out —
measured at 1 coincidence in 544 shifted trials, all on a small gap; falsified as adequate if a
later corpus shows a real gap quoted against an unrelated row.
The filing lag of 3 days could pair CIQ's guide with a revision filed within 3 days of it; no such
pair exists on the corpus.
