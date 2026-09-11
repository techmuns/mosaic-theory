---
id:
status: shipped
date: 2026-09-10
prs: [602]
supersedes:
superseded-by:
---

# ORKA onboarded — the CIQ gate held for half a day, and the export cleared it

> **RESOLVED 2026-09-10, same day.** The operator exported the eight workbooks and the name
> assembled with synthesis. The diagnosis below is kept in full because the REASONING is the
> durable part — a derived market cap was available and was refused, and the corpus agreed in
> 13 places. See **WHAT THE EXPORT UNBLOCKED** at the end.

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
  committed. **NO §5.0 ROW EXISTS FOR THIS**, deliberately: it was opened and closed inside one
  PR — the operator supplied the workbooks the same day — so it never became "what is next"
  for anyone reading main, and §5.0 is only that. (A draft of this record claimed row 25 and
  said 25 would join the empty numbers; while this PR sat unmerged another build took 25 for
  the Polygon anchor-snapshot, which is exactly why a number is not a name.) The GOOGL
  net-debt finding below IS carried, as row 27. See WHAT THE EXPORT UNBLOCKED below.
- **THE FOLLOW ENTRY IS NOT INERT — it joins the QUALITY BOOK'S PASSIVE COMPARATOR, and that was
  not stated when the decision was recorded.** `resolve_baskets` / `Basket.members_as_of`
  (`vinci/scoring/baseline.py`) build the quality sleeve's kill-test basket from `followed.json`
  AS OF each verdict's entry date, so from `followed_since` 2026-09-10 every quality verdict
  entered on or after that date is measured against a 5-name equal-weight basket that now
  includes ORKA — a name this record says cannot be assembled at all. TWO consequences, both by
  design and neither previously written down: (1) the comparator gains a high-variance member
  (+190% over six months on this record's own figures) whose weight is 1/5; (2) `basket_return`
  REFUSES the whole comparator — `vs_basket` prints "unavailable" for EVERY quality verdict in the
  window — if ORKA lacks a close at either end of it, and ORKA's bars live only in the git-ignored
  store. Verdicts entered before 2026-09-10 are unaffected (the roster is as-of, per #409).
  ACCEPTED: no quality verdict has been entered on or after 2026-09-10, so nothing is measured
  against it yet. FALSIFIER: a quality-book scoring run reporting `vs_basket` unavailable, or a
  basket line naming ORKA, before its CIQ export lands.
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

---

## WHAT THE EXPORT UNBLOCKED (2026-09-10, same day)

**The eight workbooks landed** in `data/manual/ciq/ORKA/` (git-ignored, verified by
`git check-ignore` before the copy) and `vinci dossier --ticker ORKA` ran: **1 done · 0 errors ·
synth · 4 caveats · 3 qa**, model `claude-opus-4-8`, reference date 2026-08-24.

**THE SYNTHESIS LEANS `mixed`, SO THE MACHINE PROPOSES NOTHING** — "evidence two-sided — the human's
call", which is the designed behaviour for a two-sided read. Its crux: *will the ORKA-001/002
program convert early read-outs into confirmatory efficacy before the ~$1.1B cushion is exhausted by
an accelerating burn — is the priced-in optimism earned by the data?* 6 bull / 8 bear / 7 unknowns /
5 twins; **59 of 59 citations resolve in both directions**, and every synthesis point carries a
`source_ref`.

**THE LIQUIDITY READS CORRECTLY, AND THE PAGE CAUGHT ITS OWN BASIS SPLIT.** Net cash **−$1,123M**
against $2.5M total debt, and a bull point states outright that "survival is a cash-burn question,
not a solvency one" — the shared going-concern detector (#575) holding on its second name; the only
"going concern" string on the page is a section heading. `anchor.net_debt` is honestly `UNKNOWN`
("no debt/cash tag"), so **ORKA does not reproduce the GOOGL defect** this build's sibling record
describes. Better: the page FLAGGED a basis disagreement of its own —
*"net-debt disagrees with the cash/debt bridge (−$1,123.0M simple-TEV vs −$871.1M bridge)"* — and
that $252.0M gap is exactly `MarketableSecuritiesNoncurrent`, which CIQ's Net Debt counts and its
"cash & ST inv" does not. **That is direct evidence for the sibling record's claim**: the machinery
detects this bug class when both figures reach one comparison, and GOOGL's escapes only because its
two live on paths (EDGAR anchor vs CIQ quality) that nothing compares.

**WHAT THE MACHINE ADDED THAT THE OPERATOR'S FOLLOW REASON DID NOT KNOW** — the point of assembling
rather than deciding from research: share count rose **34.99M → 66.21M (+89.2%)** in ~1.7 years;
insiders sold **$329.45M across 76 sells by 7 insiders in 182 days with ZERO open-market buys**,
including a single $300.01M director sale; FY26 EPS revisions run **1 up / 6 down**. Against 11 Buy
ratings and a $155.00 mean target on a $91.50 price. The bear case is materially stronger than the
follow reason implied, which is the funnel working.

**FOUR FLEET REGISTRATIONS A NEW NAME REQUIRES** — each demanded by a pin, none optional:

1. `tests/fixtures/prices/ORKA.jsonl` — rebuilt ALL 12 series to one vintage (443 bars,
   2024-12-02..2026-09-09). The script is deliberately all-or-nothing: its own comment records that
   a partial write once left six names at 2026-08-07 and the BENCHMARK older than the names
   compared against it, which is "the exact shape of corruption `rel_ret_vs_market` cannot survive".
2. `tests/fixtures/companyfacts/ORKA.json` — rebuilt, 19 names, 20 tags for ORKA.
3. `test_consensus_transform` exemption — ORKA carries NO `consensus_levels`, for TECX's reason and
   with its own evidence: 12 analysts, mean target $155.00, 11 Buy / 2 Outperform, while `eps_trend`
   and `revision_history` populate from the same export. That is what distinguishes absent COVERAGE
   from a failed EXTRACTION. Self-clearing.
4. `UNROUTED_BY_DESIGN` in `test_ev_gap_routing` — same property, one pin further along. **TECX was
   a one-off; ORKA makes it a class**, which is why both entries now say so.

**A REAL FINDING, NOT BOOKKEEPING — THE ASSEMBLER AND THE REFRESHER DISAGREE ON CANONICAL FORM.**
`test_a_noop_refresh_is_byte_identical` failed on ORKA. Cause: the assembler writes
`"consensus_levels": null`; `refresh_dossier` DROPS it (`_DROP_WHEN_NONE`). So a freshly assembled
dossier is **not** in the canonical committed form, and the first no-op refresh rewrites it.
Census over the 19 committed names: 17 carry a real dict, **TECX alone had the key absent** (its
artifact had been through a refresh) and ORKA had the explicit null — which is why one name was
never enough to surface this. Remedied by running `refresh_dossier` on the artifact (verified
idempotent: a second call returns `False`), then rebuilding the mirror AFTER the data change.
**NO STATE ROW OPENED:** per the INVARIANT RULE the machine check already exists and already fired —
the no-op pin cannot be missed by a future build, so this is guarded, not accepted.

**AN ENVIRONMENT TRAP, recorded because the weekly job runs one of these scripts unattended.**
`python scripts/build_price_fixture.py` resolved `vinci` to `/Users/work/Documents/GitHub/`
`mosaic-theory/` — a DIFFERENT checkout — because Python puts the SCRIPT'S directory on `sys.path`,
not the cwd; the worktree's package is reached only via `python -m vinci` or an explicit
`PYTHONPATH`. Both fixture builds were re-run pinned. The dossier itself was never exposed: the
assembly, the suite, ruff and mypy all run through `-m`, verified by printing `vinci.__file__`.

**VERIFIED.** `pytest -m "not network"` **0 failures, exit 0** on the freshly committed artifacts
(the ARTIFACT-PASS RULE's requirement, run after the commit contents were final); frontend mirror
byte-identical to `data/` for both files; no licensed CIQ content in the committed artifact — the
only workbook references are FILENAMES inside absence messages plus the label "NTM Revenue
(Capital IQ)", the same shape as TECX's approved artifact, and `llm_call.log` (which holds the full
prompt) is git-ignored at `.gitignore:32`.
