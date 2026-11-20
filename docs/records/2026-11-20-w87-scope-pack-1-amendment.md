---
status: open
date: 2026-11-20
prs: [1154]
---

# W87: scope pack 1 amended — DVN's quarterly re-export and DAC's pack are built at $0 (both pass the precheck; DVN's R1 value withheld under W73, DAC's R1 declining), SP-D22 added, and what was found since listed (docs only)

**WHAT.** `docs/scope-pack-archetypes-1.md` (committed by #1145, record
`docs/records/2026-11-19-archetype-scope-pack-1.md`) is amended:
- **§0:** the 2026-11-20 builds' boundary.
- **§1 and §2:** DVN's mislabel refusal is cleared, and its R1 value is withheld; DAC's pack landed and passes. AQN is unchanged.
- **§3:** **SP-D22**, coined here in plain words: *a lessor with no CIQ rent row is treated as having material rent, so R1 declines on the form of its statements.*
- **Orders:** SP-D22 joins Order 2 beside SP-D17. Order 5's DVN is no longer pending. Order 6 says what DAC does and does not test.
- **§6:** one retired line.
- **§5:** SP-R4 is ruled. Asked "Rule SP-R4: keep MLPs (K-1 issuers) out of scope for stage 1?", the operator answered, verbatim, "Yes, keep them out" (2026-11-20, ~07:55Z, relayed by B). G15 is out of scope for stage 1 and refused at intake; all nine rulings are now made. §1, SP-S1 and Order 1 follow (Order 1 no longer depends on SP-R4).
- **§7:** SP-D22 at Order 2; 39 IDs, every one `open`. SP-R4's row stays `open` like its eight ruled siblings, because the log records TeamNostra's reply.
- **§8 (new):** "Found since the pack, not in its orders" (W84, W85, W86), with each owner and status as of 2026-11-20. The cover note carries their statuses at send time.

`docs/scope-pack-archetypes-1-findings.md` gains §11f addendum 4, D22 in §9, and the G05 and G17
grid cells. STATE.md §5.0 row 4's pointer is restated. The merged record carries an `## Amendments`
entry naming #1145.

**WHY.** The pack went to TeamNostra with two exports pending: DVN's quarterly Financials and DAC's
pack, DAC being the substitute G17 test name for AQN, which has no US listing in CIQ. Both landed on
2026-11-20. Building them found SP-D22. This is the W87 amendment that the operator's TeamNostra
plan already includes; coordinator B asked for it ("Please open the scope-pack amendment you
offered").

**HOW VERIFIED.** All runs were real, at $0, on main `6c22b222`: the probe's `fresh5a.py`, run
against that checkout, with every CIQ copy sha-checked equal to its original and deleted after.
- **DVN** (quarterly `a532e1a269`, "Period Type: Quarterly"):
  - precheck PASS, exit 0, 0 post-spend refusals;
  - own-history EV/EBITDA band of 33 quarterly closes; bridge built;
  - R1 applies, with its value withheld by W73, because the band's newest close (2026-09-30) predates DVN's 8-K item 2.02 0001193125-26-449884 of 2026-11-05.
- **DAC** (11 files; quarterly `943da1a0b0`, annual `91d3245a0b`):
  - precheck PASS, exit 0, 0 refusals; every money panel USD;
  - a fresh EDGAR submissions read (2026-11-20T06:50Z) shows no Q3 2026 results 6-K. The event rule read 0 events against the export-dated panels, so the pass is correct;
  - R1 declines on SP-D22.
- **SP-D22's evidence:**
  - DAC's companyfacts carry no lessee lease cost or operating-lease liability, against FY2025 operating income of $498.8M and D&A of $163.4M (20-F 0001104659-26-021574);
  - PLD takes the same path;
  - `lease_basis._materiality` returns "treated as material" when CIQ's annual income statement has no 'Net Rental Exp.' row (checked by B on main `cd082d0b`).
- **Re-checks:** AWK and MORN were re-run on `6c22b222` and still price R1 as at `6e03501f`.
- **The scope block and the log agree on 39 IDs.** The full diff scans clean for paths, emails and secrets.

**BOUNDARY.**
- **Builds:** main `6c22b222`, assembled 2026-11-20T06:43–06:47Z, scratch data dir as the pack's §0; page reference date 2026-10-16.
- **Prices:** DAC's 500 bars, 2024-11-20 to 2026-11-18, came from one Polygon aggs call.
- **CIQ:** DVN's quarterly and DAC's pack, knowable from their export date, 2026-11-20.
- **Live-page count:** SP-D22's text on 0 of the 26 committed pages at `6c22b222`.
- **§8 statuses** are as of 2026-11-20, read from STATE.md §5.0 row 10 and GitHub: W84 open (A), W85 open (B), W86 PR #1152 open (A).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Nothing is owed by the operator for the pack now.** DVN's R1 value waits on an export carrying a close after 2026-11-05: optional, not owed.
- **SP-D22 is reported, not fixed.** It is a refusal, so it fails closed, and it is on no live page.
- **The pack's IDs stay `open`** for TeamNostra's reply.
