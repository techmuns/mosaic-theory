---
id:
status: shipped
date: 2026-10-19
prs: [750]
supersedes:
superseded-by:
---

# R1 prices on one lease basis: TEV less operating leases over reported EBITDA, with net debt to match, wherever rent is material

**WHAT.** R1 used to price reported EBITDA at the median of CIQ's TEV/LTM EBITDA history, then
subtract lease-inclusive net debt. Where rent is material, it now uses an **ex-lease history**
instead: TEV less operating leases, over reported EBITDA, every quarter. The bridge leaves the
operating leases out to match.
- **New:** `vinci/dossier/lease_basis.py`, stored as `mechanical.valuation.lease_basis`.
  - **Materiality:** CIQ's annual "Net Rental Exp." ÷ "EBITDA" on the latest fiscal year that
    reports both; material at ≥5%. Rent that cannot be measured counts as material.
  - **The history:** CIQ's quarterly Historical Capitalization TEV, priced at each filing date. The
    operating leases inside it are CIQ's lease rows less EDGAR's finance leases.
  - **The check:** on every date EDGAR tags a complete operating figure, that split must match it
    within 2%. Where CIQ files finance leases outside its lease rows (UBER), the rows alone must
    match. A quarter EDGAR does not check takes the split of the nearest reconciled quarter, on
    either side.
  - **Pre-adoption, by filing date:** a short CIQ lease row counts as "CIQ's balance sheet
    predates the standard" only where EDGAR's figure for that date was first filed more than 100
    days later (an opening balance or a restated comparative: TJX 2019-02-02, TGT's 2017 quarters).
    Anywhere else it is a gap.
  - **The refusals:** a quarter that matches neither split is left out of the band. The band
    itself is refused when more than 10% of checkable quarters fail, when fewer than 4 reconcile,
    when it has fewer than 8 quarters, or when its LATEST quarter is unpriced (no older quarter
    stands in as current).
  - **Rent cross-check:** EDGAR's own `LeaseCost` (else `OperatingLeaseCost`) for the same fiscal
    year is recorded beside CIQ's rent, and the materiality sentence says DISAGREE past 1.5×. It
    does not decide materiality.
- **One selector, `anchor.r1_multiple_band`,** for the anchor, the tagger and the R1 audit. The
  scenario template, the page's basis line and the valuation-basis block key off the ANCHOR's own
  basis instead, and `anchor.lease_basis_mismatch` names any disagreement between the anchor and
  the page.
  - **Immaterial rent:** CIQ's history and the lease-inclusive bridge, field for field as before.
  - **Material rent with an ex-lease band:** the ex-lease median with `NET_DEBT_EX_LEASE`. CIQ's
    net debt is not used as a fallback, because it carries the leases.
  - **Material rent without an ex-lease band:** R1 refuses with `lease_basis_unresolved`. It never
    falls back to the mixed series.
- **The page:** for a lease-material name, the "Multiple basis" line names the ex-lease median and
  its bridge. The "same TEV over REPORTED EBITDA is nearer N×" restatement is gone for those names,
  because it is neither basis. The screening table says "ex-lease" in both renderers.
- **The basis block:** it states the anchor's pair, and lists a conflict when the multiple and
  net debt sit on different lease bases, when the anchor predates the page's lease basis, or when
  the page's lease basis refuses R1 while the anchor still prices it. The scenario template
  refuses in the same states.
- **The R4 cross-check stays lease-inclusive.** `ev_bridge`'s EDGAR figure sits beside CIQ's TEV
  claims, which carry the leases, so assembly and `ev_bridge_transform` take it from
  `lease_inclusive_net_debt`, not from the anchor.
- **Writers:** `refresh.lease_basis_transform` (only from the export the page's history was built
  from). `own-history-refresh` now moves `lease_basis` with the rest of the multiples cluster.

**WHY.** An IC review of TJX and BURL flagged the restated multiple. Measured on the fleet's CIQ
exports, CIQ's post-842 TEV/LTM EBITDA is struck on EBITDA plus rent for most names, and on
reported EBITDA before 842.
- **Two consistent pairs exist:** TEV with leases over EBITDA plus rent, or TEV without operating
  leases over reported EBITDA. R1's numerator is reported EBITDA, so the operator chose the second
  ("Ex-lease basis", 2026-10-19).
- **The 2026-07-22 convention changes for lease-material names.** It made the bridge
  lease-inclusive to match CIQ's TEV. For those names the bridge now follows the ex-lease multiple
  instead. Immaterial names keep it.

**HOW VERIFIED.** All runs were on real data: main `c4ebdc37`, the CIQ copy
(`mosaic-theory-ta/data/manual/ciq`, 27 names) and EDGAR companyfacts, on 2026-10-19.
- **The rebuild reproduces CIQ where the bases agree.** On pre-842 quarters, the ex-lease multiple
  ÷ CIQ's multiple at the nearest close (within 46 days) has a median of 0.92–1.08 on every name
  with pre-842 quarters: TJX 0.987, BURL 0.974, ROST 0.981, NKE 1.011, TGT 0.984, V 0.991, GOOGL
  0.995. After 842, the same TEV over reported EBITDA ÷ CIQ's multiple is TJX 1.536, BURL 1.829,
  ROST 1.343 and VITL 5.13, against V 0.993 and GOOGL 1.059. That is the rent add-back, and only
  where rent is large.
- **The anchor, old and new, through the backfill's own path** (same EDGAR facts and CIQ bridge;
  nothing written):

  | name | rent ÷ EBITDA | multiple | net debt $M | R1 $/share |
  |---|---:|---|---|---|
  | TJX | 45.3% | 12.04 → 15.85 | 8,313 → −3,133 | 88.52 → 129.10 |
  | BURL | 77.4% | 12.82 → 16.37 | 5,338 → 1,346 | 183.42 → 319.93 |
  | ROST | 34.3% | 12.72 → 14.84 | 451 → −3,270 | 132.16 → 166.18 |
  | CNXC | 35.1% | 6.89 → 7.46 | 5,036 → 4,131 | 65.98 → 93.27 |
  | PARR | 22.3% | 6.91 → 7.71 | 949 → 567 | 34.01 → 47.86 |
  | NKE | 23.3% | 21.14 → 23.54 | 4,169 → 990 | 88.50 → 101.02 |
  | TGT | 8.3% | 8.44 → 8.95 | 14,804 → 11,100 | 137.57 → 155.94 |
  | EPAM | 9.2% | 22.41 → 25.30 | −637 → −764 | 352.35 → 398.58 |
  | WLK | 15.3% | 7.73 → 7.91 | 4,024 → 3,215 | 105.98 → 115.51 |
  | WERN | 8.1% | 6.68 → 6.65 | 897 → 793 | 30.82 → 32.39 |
  | SMPL | 5.0% | 17.85 → 17.92 | 325 → 273 | 43.33 → 44.10 |
  | AMZN (R4 tag) | 11.5% | 24.39 → 26.12 | 119,007 → 22,687 | 249.57 → 276.81 |
  | AORT (R2 tag) | 14.0% | 32.11 → 37.98 | 331 → 290 | 19.79 → 25.50 |

  - **Unchanged, field for field:** BRBR, GOOGL, IT, LLY, V and VRRM, all immaterial.
  - **No base value either way:** FUBO, ORKA and TECX (no CIQ history); MVST and NCNO (margin);
    UBER (refused, 4 of 30 checkable quarters unreconciled).
- **Two names change state.**
  - **VITL becomes applicable** (weak → firm; it stays R2-tagged). Its CIQ band tripped the
    coherence guards because CIQ adds its $288M of rent back to about $103M of EBITDA (implied ÷
    reported ≈ 3.6×). That rent is VITL's own reported total lease cost (EDGAR `LeaseCost` $293.0M,
    FY2025), not a vendor defect. The ex-lease history does not use CIQ's ratios and reconciles to
    the market; the anchor states CIQ's band flag beside it. VITL's operator re-tag reason (kept
    verbatim) still calls it a "vendor data defect"; whether to revise it is the operator's call.
  - **NFLX loses its vendor-filled net debt.** Its rent is 5.2% of EBITDA, so CIQ's
    lease-inclusive net debt is no longer substituted. It is inapplicable either way, as committed.
- **Pins:** `tests/test_lease_basis.py`, 49 tests (parametrized cases counted).
  - **The per-date split, on real quarters:** TJX's 2019-02-02 adoption boundary, IT's short row,
    BURL's finance leases inside the rows, UBER's outside them, UBER's mismatch, NKE's zero.
  - **The anchor, template, basis block and both renderers,** on the committed pages with lease
    bases captured from production.
  - **The refusal and its precedence,** VITL's guard behaviour, and the writers:
    `lease_basis_transform` (written only from the page's own export) and `own-history-refresh`
    (written with EDGAR, skipped without it), each driven end to end.
  - **The web twin, rendered** through `dossier.js` in node.
  - **A local corpus pass** asserting the pre-842 agreement (±15%). It skips in CI.
  - **An end-to-end pin** that no committed page prices R1 across lease bases.
- **Mutation: 30 of 30 killed** after the review round: 12 of the first set (still applicable to
  the revised code) and 18 covering the review's fixes. The first run had left two survivors, the
  shortfall after a reconciled quarter and the LTM window's lower bound, and both pins were
  strengthened.

**THE REVIEW, BEFORE MERGE (`/code-review xhigh 750`, 15 findings).** All checked on real data.
- **Fixed as found:** the template pairing an ex-lease multiple with a stale anchor's
  lease-inclusive net debt (#1); a refused lease basis beside a still-priced anchor not flagged
  (#2); an unpriced latest quarter back-filled as current (#3); a failed EDGAR fetch committing a
  refusal (#4); the page line asserting pricing the anchor did not do (#5); the tagger and R1 audit
  reading CIQ's band only (#7, #8); the R4 cross-check label/value split (#9, fixed at the root:
  the cross-check is lease-inclusive by construction); the two-sided split (#12); the pricing date
  read as a number (#13); untested writers (#14); the dead band helper (#15).
- **Fixed differently than proposed (#11):** bounding pre-adoption to the first EDGAR date would
  have refused TGT, an early adopter whose 2017 quarters EDGAR carries as comparatives first filed
  in 2018. The rule keys on filing date instead.
- **Checked, then addressed as visibility (#10):** CIQ's rent equals the filer's EDGAR
  `LeaseCost` on most names (TJX 3,814 = 3,814; ROST 1,104.7; CNXC 444; NFLX 711; SMPL 13.186;
  VITL 288 beside 293). EDGAR's figure is now recorded beside it, with DISAGREE past 1.5× (WLK 128
  against 306).
- **Partly (#6):** the anchor now states CIQ's own band flag. A value guard on thin-EBITDA
  quarters was NOT added: CIQ reports those multiples itself (VITL 172.5×, NCNO 221×, NFLX 157.7×
  on CIQ's own closes), so any cap is a new threshold for a separate decision.
- **The real run after the fixes is identical** for every name: same medians, currents, net debt
  and R1 values. The fixes change guards, not today's numbers.

**BOUNDARY.**
- **Population:** the 27 committed dossiers, measured 2026-10-19 on main `c4ebdc37`. Their CIQ
  exports are the copy above.
- **Rent ÷ EBITDA:** the latest fiscal year reporting both. That is FY2022 for LLY, whose later
  years carry "NA".
- **"Checkable quarters":** those with an EDGAR complete operating figure (the total tag, or
  current plus noncurrent both tagged) within 7 days.
- **Matching windows:** finance leases are taken from the nearest filing within 200 days. The
  pre-842 comparison matches the filing date to CIQ's nearest quarter-end close within 46 days.
- **The anchor table:** each row is computed on that day's EDGAR facts, so "before" can differ from
  the committed anchor where facts moved since its backfill.
- **The review probes:** "CIQ's rent equals EDGAR's LeaseCost" compares the latest fiscal year
  with both, annual points within 7 days of its end, on the 27 names (2026-10-19, the EDGAR cache).
  "CIQ reports the thin-EBITDA multiples itself" compares each rebuilt quarter above 40× with CIQ's
  nearest close on the five names printed (VITL, BURL, NFLX, AORT, NCNO). "Comparative" means first
  filed more than 100 days after the period end.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Committed R1 records were struck on the old basis:** EPAM (9.2%), WERN (8.1%) and SMPL (5.0%,
  at the line). Their multiples were read off CIQ's history, and their net debt is lease-inclusive.
  Records are sealed and this does not touch them. Re-underwriting is the operator's call. A
  `scenario-refresh` of their `net_debt` from a re-derived anchor would mix the bases, so it must
  not be run as a bare number.
- **SMPL and NFLX sit at 5.0% and 5.2%:** a year's rent moves them across the line. The threshold
  was set by face validity (the understatement is about the multiple × rent), not to place any
  name.
- **The page's displayed band stays CIQ's.** The percentile the reader sees is CIQ's series, and the
  basis line names the ex-lease median and its own percentile beside it. Replacing the displayed
  band would move the percentile on every lease-material page, so it is left as a separate call.
- **The forward EV/NTM EBIT history (R4) is not touched.** Its own pre/post-842 consistency is
  unchecked here.
- **Nothing on the committed pages moves until the artifact pass:** `lease_basis_transform`, then
  `anchor-backfill`, then the full suite. That is a separate PR. The basis block refuses an anchor
  derived before its page's lease basis, so a half-done pass is visible.
