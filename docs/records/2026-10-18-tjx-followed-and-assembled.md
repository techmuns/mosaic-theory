---
id:
status: shipped
date: 2026-10-18
prs: [745]
supersedes:
superseded-by:
---

# TJX joins the followed names in the OVERSHOOT book and lands its first dossier — five draws agree, the proposal stays sealed

**WHAT.** The TJX Companies is followed and assembled for the first time, through the
followed-name intake loop (RUNBOOKS §i), artifacts only.
- **The follow entry** (`data/followed.json`): `sleeve: overshoot`, `followed_since: 2026-10-18`.
  The operator chose the book (overshoot over the quality recommendation) and approved the drafted
  reason verbatim, with OVERSHOOT filled in. Its facts are the 2026-10-16 close:
  - $147.33, 12.5% below the 52-week closing high of $168.41 (2026-06-12), 19.9% above the low of
    $122.84 (2026-09-16);
  - 12.2 points behind SPY over the same 52 weeks;
  - path segmented: +18.1% to the June high, −27.1% to the September low, +19.9% since.
- **The page** (`data/dossiers/TJX/`, mirrored to `frontend/dossiers/`). Assembled on main at
  `3f821502` (2026-10-18): `1 done · 0 error(s)`, 2 caveats, 4 QA flags.
  - **Dates:** every price-derived input is struck at the 2026-10-16 close (price, cap, TEV,
    multiple); consensus is ≥2026-10-09; the balance sheet is Q2 FY27, 2026-08-01.
  - **Synthesis:** five draws, **5/5 strongly-bullish, unanimous**, so the draw gate passes. Lean:
    "compounding absolute EBITDA, raised guidance and superior peer fundamentals, with the premium
    multiple the only genuine restraint". The machine's proposal stays **sealed until the operator's
    verdict is recorded**, as designed.
  - **The crux the page poses:** is EV/EBITDA 13.3x (peers 6.8x; NTM 18.7x vs 9.15x) an earned
    franchise premium, or does Marmaxx's slowdown (+1% comp in Q2 from +6% in Q1) mark the comp
    slowdown that de-rates it? EV/EBITDA sits at the 77th percentile of its own 9.5-year range.
  - **Valuation recipe:** R1 applies. The screening context's $88.52/share is an attention filter,
    not a value.
  - **Next print:** ~2026-11-18 (cadence estimate) — the page goes stale then.
- **The data.**
  - **CIQ:** all 10 exports in the operator's Drive folder, mirrored into
    `data/manual/ciq/TJX/` with every sha256 matching (git-ignored, never committed). The loader
    classified all 10 with no kind held twice (#706). Every required export is present, including
    the comps workbook. The optional Credit Health Panel was not pulled, so the page shows the
    comp-set panel. The two transcripts are Word files under an `.rtf` name and were read.
  - **Prices:** TJX backfilled into the shared store (499 bars, 2024-10-21..2026-10-16); SPY, TJX's
    cap-band benchmark (≥$25B), topped up to 2026-10-16.
- **Fixtures:** `tests/fixtures/companyfacts/TJX.json` (24 tags) and `tests/fixtures/prices/TJX.jsonl`
  (470 rows, 2024-12-02..2026-10-16, the same window as the committed fixtures).

**FOR THE OPERATOR'S READ — on the page, not re-rolled.**
- **Four QA flags.**
  - **Two "operating-drivers: no anchored pattern":** in the EX-99.1 releases and in the 10-Q MD&A.
  - **One covenant exhibit refused as not a debt agreement (E5):** four revolving credit agreements
    were extracted.
  - **"DIRECTIONAL language 'sell'":** the guard caught a factual line ("Insider activity is
    sell-only — 8 sells, 0 buys, $27.7M over 182d"). It stays flagged for the human.
- **A defect this page surfaced — OPEN, on STATE §5.0 row 32 (10).** A 2020 364-day revolving facility
  (`exhibit101364dayrevolv.htm`, 8-K 0000109198-20-000015) is headed **"DAY REVOLVING CREDIT
  AGREEMENT"**. The title clean-up that strips leading filing codes (`covenant_extract._LEAD_CODE`)
  took the "364". The label is wrong; the extracted terms are not. It is a code fix, not this
  artifact pass's.

**HOW VERIFIED.**
- **The page:**
  - read in full against its own sources: the dates above, the five draw labels, the QA flags in
    context;
  - the 364-day heading traced to its exhibit file name;
  - the performance chart's one repeated benchmark value (2025-10-20/21) is SPY's real closes,
    671.30 and 671.29.
- **The store reads:** the page reads the store for TJX and SPY only, both current to 10-16. Its
  cohort comparison is empty ("TJX not in graph_coverage.json"), so no other name's prices reached
  it.
- **The fixture script overreached, and was not followed.** `build_price_fixture.py` also rewrote
  all 23 other maintained names from this worktree's shared store. That store stops at 10-06 to
  10-09 for those names, while the committed fixtures run to 10-16 (#742). Those 23 files were
  restored, because committing them would have rolled the test inputs back by up to a week. Only
  TJX's fixture is committed.
- **Suite:**
  - with the shared store linked: 6,361 passed, 1 failed. The failure is
    `test_store_freshness::test_the_gated_set_includes_the_benchmark_not_only_the_dossiers`, the
    stale shared store, which CI never has.
  - the final run is on the merged branch with the store link removed, matching CI: see the PR.

**BOUNDARY.**
- **Prices:** the price facts in the reason are TJX and SPY daily closes in the shared store over
  the 52 weeks to 2026-10-16 (252 closes each).
- **The page:** "every price-derived input" is the `date_semantics` block's price, market-cap, TEV
  and multiple dates.
- **The 23 restored fixtures:** each committed file holds 470 rows to 2026-10-16; the regenerated
  ones held 462–465 rows ending 2026-10-06 to 10-09.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The follow reason's numbers are dated, and freeze.** They state the 2026-10-16 close, as ROST's,
  BURL's and TGT's state theirs.
- **The shared store this machine's worktrees link is stale for every name but TJX and SPY.** That is
  an environment state, not this page's input, and it is why the price-fixture script cannot be run
  for the fleet from here. Refresh the store before the next fleet-wide pass.
- **The 364-day heading ships as it is,** labelled wrong, until the title-normalisation fix (row 32
  (10)).
