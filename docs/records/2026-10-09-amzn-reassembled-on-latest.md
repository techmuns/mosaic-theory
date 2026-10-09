---
id:
status: shipped
date: 2026-10-09
prs: [700]
supersedes:
superseded-by:
---

# AMZN re-assembled on the latest code — the non-operating count lands, the machine's own read agrees with the R4 tag, and the stale R3 caveat is gone

**WHAT.** AMZN was re-assembled on main @9dfede17, before any R4 scenario record. That build
carries every change since #692's:
- the refresh record (`2026-10-09.1`, #694/#696);
- the machine's R4 proposal and its structured non-operating count (`2026-10-09.2`, #697);
- the R4 card render (#693) and the Method row fix (#699), which are render-only.

**Inputs were the same as #692's:**
- **Prices:** through the 2026-10-08 close, already the latest finished session (the 10-09 US
  session was open at build time, 19:06 IST). No refresh was run.
- **CIQ:** the 11 exports in the Drive folder and in `data/manual/ciq/AMZN` are byte-identical, and
  their hashes match the page's (Financials `e5abf9d69d`, Estimates `e10ed62223`).

**Only artifacts changed:** AMZN's page and its mirror, `frontend/dossiers/index.json`, and STATE
row 10. Both fixtures rebuilt byte-identically.

**WHY.** Operator instruction, 2026-10-09: the latest AMZN dossier on the latest fixes first,
without scenarios, before the first R4 record.

**WHAT MOVED** (against main's page, #692 plus the #698 re-tag and #699 render):

    extraction stamp      2026-10-08.4                       ->  2026-10-09.2
    non-operating count   absent                             ->  3 of the trailing 4 (window end 2026-06-30)
    machine's R4 read     2 met + 1 unknown                  ->  all 3 met — proposes R4, agrees with the tag
    recipe                R4_forward_ev_ebit (hand tag)      ->  R4_forward_ev_ebit
    caveats / qa          9 / 5                              ->  7 / 5
    draws                 strongly-bullish 3 / mixed 2       ->  strongly-bullish 4 / mixed 1 — proposal withheld both times

**Unchanged, equal to main:**
- `forward_consensus`, `forward_multiple_history`, `historical_forecast_error`, `ev_bridge`;
- `midcycle`, `reference_date` (2026-09-22), `qa_flags`, the price;
- the non-operating sentence. Only its endnote number moved ([15] → [14]), because a removed caveat
  renumbered the sources.

**The caveats that left:**
- **"Recipe kept from the committed dossier: R3_forward_pe … proposes R1_midcycle_margin_evebitda".**
  It was stale on both counts: the page is R4, and the machine now proposes R4. Its removal is the
  agreement, not a suppression.
- **"Possible false balance"** did not fire on this draw: 8 bull points against 5 bear.
- The draw tally, the GAAP-EPS caveat and the fetch line were rewritten with this build's values.

**⚠ THE ANCHOR'S REASON IS NOW THE MACHINE'S.** #698 wrote the operator's re-tag text, "OPERATOR
RE-TAG 2026-10-09. R3 -> R4 …". Where the build's proposal equals the committed recipe,
`_keep_committed_recipe` keeps the fresh anchor, reason included. So the page now reads "EV/NTM EBIT
(R4) — all three ratified conditions hold: …".
- The conditions and values are the same.
- The page no longer says who made the tag. The re-tag record
  (`docs/records/2026-10-09-amzn-uber-re-tagged-r4.md`) and git history still do.
- Flagged to the operator, not hand-edited here.

**Redrawn by the LLM-fenced phases:**
- **The synthesis:** the lean is still strongly-bullish. Bull points went 7 → 8 and bear points
  stayed at 5. The +71% FY26 GAAP-EPS bull point was drawn again, and #678's caveat fired on it
  again (normalized +10%). The written assessment now cites a trailing P/E of 20.6x where the last
  draw cited 19.8x.
- **The covenant digest:** 4 rows, reworded.
- **The operating-driver rows:** 270 → 270. 16 were dropped and 16 added, keyed on kind, metric and
  value.

**HOW VERIFIED.**
- **CIQ inputs:** Drive against `data/manual/ciq/AMZN`, sha256 on 11 of 11 files, all equal and
  equal to the page's hashes.
- **Prices:** the store's frontier is 2026-10-08 for AMZN, SPY, MDY and IWM.
- **Assembly:** `dossier --ticker AMZN` exited 0 with `1 done · 0 error(s)`, 2026-10-09
  19:06–19:14 IST.
- **The page diffed against main's key by key.** Every moved key is itemized above.
- **The machine's own R4 read off the new page:** all three conditions are met (NTM TEV/EBIT 23.3x;
  EBITDA basis divergent at 3.14×; GAAP-struck FY P/E with 3 of 4 quarters material).
- **Mirror:** `frontend/dossiers/AMZN.{json,md}` are byte-identical to the page.
- **Fixtures:** `build_companyfacts_fixture.py AMZN` and `build_price_fixture.py` both rebuilt
  byte-identically.
- **Suite:** `pytest -m "not network"` on the freshly-committed artifacts. Counts are in the PR.
  - The first run failed one test, `test_a_re_assembly_shows_the_proposal_and_keeps_the_committed_recipe`.
    It copies a committed page with the tag set back to its pre-re-tag recipe, and expects the
    "Recipe kept" caveat to carry this build's reason. The caveat appends that reason only where it
    differs from the kept one (`assemble.py`), and AMZN's committed reason is now this build's own.
    So the copy simulated a state that never existed: an R3 tag beside an R4 reason.
  - **Fixed test-only, in a separate commit.** The copy now carries a reason of its own recipe, and
    the invariant is unchanged. A mutant that drops the reason from the caveat still fails it.

**BOUNDARY.**
- **Scope:** one page, AMZN, 2026-10-09.
- **Prices:** through the 2026-10-08 close.
- **CIQ:** the exports on disk, unchanged since #680.
- **Draw counts:** five draws, one build.
- **Driver-row count:** keyed on (kind, metric, value).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The synthesis is fully rewritten,** as every full assembly does, and is still blind to
  EV/NTM EBIT, the multiple history, the forecast error and the bridge (§5.0 row 30, the operator's
  decision).
- **The lean has now drawn strongly-bullish/mixed on four builds over the same CIQ exports.** The
  gate withholds the proposal each time. One build cannot separate input change from draw variance,
  and none was re-rolled.
- **The Q3 report** (not yet announced; estimated around 10-29) will stale this page.
- **Next:** the first R4 record (`scenario-propose` → the analyst's six inputs → `scenario-create`),
  on this page.
