---
id:
status: open
date: 2026-09-10
prs: []
supersedes:
superseded-by:
---

# ORKA is followed, and cannot be assembled: the dossier's market cap has ONE source, and it is the CIQ workbook

**WHAT.** Oruka Therapeutics (ORKA, CIK 0000907654) is recorded in `data/followed.json` under the
QUALITY book by operator decision 2026-09-10. The mechanical layer assembles cleanly. The FULL
build — the one that writes a committed dossier and runs synthesis — **refuses**, and correctly:

```
FreshnessError: ORKA: the build is missing market cap — every ratio on the page rests on the
spot, and a dossier without one is not underwritable.
```

No artifact is committed by this build. Only the follow decision and this record are.

**WHY.** `StockInfo.market_cap` is `implied_val.market_cap` → `ciq_sheets.comps_market_cap(bundle)`,
which reads column 3 of the **Company Comparable Analysis** workbook. There is no second source.
`data/manual/ciq/ORKA/` does not exist, so the cap is absent, and `absent_cap_inputs` fails the
build loud rather than letting the reconciliation report a clean pass it never made.

This is NOT an implementation gap to route around. `vinci dossier requirements --ticker ORKA`
states the rule in the repo's own words:

> **Company Comparable Analysis (peer comps) — REQUIRED for: quality** — optional for the fund at
> large, but this book's decision rests on it; a verdict without it has no evidence for its own
> claim.

ORKA is a `quality` name. The workbook that supplies the cap IS the workbook its sleeve requires.
The guard and the sleeve agree.

**A DERIVED CAP WAS CONSIDERED AND REJECTED.** `vinci/universe.py:392` already computes
`market_cap = close * shares_used` at tier `DERIVED` — that is how ORKA entered the cap band at all
($6.93bn, 2026-08-12). Wiring that into the dossier would have unblocked this build in a few lines.
It was not done, for two reasons:

1. **It would disable a live guard fleet-wide.** `reconcile_cap` asks whether `cap ÷ shares` agrees
   with the rendered spot — the check that caught FUBO's ~11x pre/post-split share-basis mismatch.
   A cap DEFINED as `spot × shares` makes that quotient identically the spot: ratio 1.0, gap 0, on
   every name that took the fallback. That is the guard-that-cannot-fire class the freshness module
   itself was written to close.
2. **It would seat a quality-sleeve verdict on absent evidence** — precisely what the requirements
   text above forbids.

**HOW VERIFIED.** Real runs against the live corpus, at `origin/main c656190`:

- `vinci dossier --ticker ORKA --no-llm` → succeeds; 5 caveats, 4 QA flags.
- `vinci dossier --ticker ORKA` (full) → `FreshnessError`, quoted above.
- **The corpus refuses the mechanical-only artifact, in 13 places.** With
  `data/dossiers/ORKA/` present, `pytest -m "not network"` fails 13 tests, every one an
  "every committed name" invariant — `test_freshness::test_every_committed_name_has_the_inputs_the_gate_requires`,
  `test_staleness_split::test_every_committed_page_carries_both_ages`,
  `test_consensus_transform::test_every_dossier_carries_levels_except_the_standing_rule_exemptions`,
  `test_capital_structure_vintage`, `test_dilution_denominator`, `test_ev_gap_routing`,
  `test_maintenance_path` (×4), `test_refresh_path`, and two more. Removing the artifact returns
  the suite to green. The suite states the same rule the guard does: a CIQ-less dossier is not a
  valid fleet member.
- **All 18 committed names carry a CIQ export** (`data/manual/ciq/<T>/`, 8–11 files each). ORKA
  would have been the first with none.

**BOUNDARY.** Every count above measured 2026-09-10 at `origin/main c656190`, in the worktree
`mosaic-theory-ta`. POPULATION for "18 committed names" = `data/dossiers/*/dossier.json` excluding
ORKA. The 13 failing tests are the offline set only (`-m "not network"`); network tests were not
run. ORKA's gate figures (−9% from the 52w high; +178pp vs IWM over 180d) are computed at the
FLEET REFERENCE DATE 2026-08-24 over bars filtered `<= 2026-08-24`, UNIT percent; the snapshot
price ($91.50, −20.8% from the $115.52 high) is the LATEST CLOSE 2026-09-09 and is a DIFFERENT
as-of by design — CMP is the latest close on every committed page.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **ORKA has no page until the operator exports its CIQ workbooks.** Required for the quality book:
  Financials — Annual, Financials — Quarterly, Estimates Report, Business Relationships, and
  **Company Comparable Analysis** (the cap). Into `data/manual/ciq/ORKA/`, git-ignored, never
  committed. Tracked as STATE.md §5.0 row 25.
- **ACCEPTED RISK — the dossier's cap remains single-sourced.** A name whose comps workbook is
  absent cannot be assembled at all, however good its EDGAR coverage. That is deliberate for the
  quality book; whether it should hold for every sleeve is UNSETTLED and not decided here.
  FALSIFIER: a sleeve whose requirements do NOT list Company Comparable Analysis nevertheless
  failing this gate — at which point the cap needs a second source and the reconciliation needs an
  explicit "derived, not reconciled" state rather than a silent pass.
- **NOT A DEFECT HERE, recorded because it was suspected as one.** At proposal time (2026-09-01)
  this build predicted ORKA's page would understate liquidity ~4×: our `cash` concept reads
  `CashAndCashEquivalentsAtCarryingValue` ($268.5M at 2026-06-30) and never `MarketableSecurities`
  ($857.1M), against the company's own $1.1bn. **The prediction was wrong FOR ORKA.** Both consumers
  of the concept — `anchor._lease_inclusive_net_debt` and `client.compute_fundamental_snapshot` —
  gate on the presence of DEBT tags, and ORKA is debt-free, so both return UNKNOWN. The page prints
  no cash figure at all rather than a wrong one; verified on the assembled mechanical layer.
  **The underlying basis split is real, and on a name that DOES carry debt it is a live defect —
  see `docs/records/2026-09-10-anchor-net-debt-basis-split.md`, written from this investigation.**
