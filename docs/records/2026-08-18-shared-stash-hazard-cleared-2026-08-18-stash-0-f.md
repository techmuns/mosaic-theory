---
id: 
status: recorded
date: 2026-08-18
prs: [472, 473]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**SHARED-STASH HAZARD CLEARED 2026-08-18:** `stash@{0}` (`fleet-batch-5-names-UNCOMMITTED`) held STALE re-assembled artifacts for AORT/EPAM/IT/NCNO/VITL from an older batch — fully superseded by #472/#473 (its AORT P/E 119.33 vs committed 120.38). DROPPED at operator instruction: a pop would have smashed five current dossiers with stale ones. `stash@{1}` (2026-07-23 WIP) remains, untouched.

**~~⚠ LIVE UNGUARDED HAZARD — `scenario-refresh diluted_shares` SILENTLY REVERTS ITEM 24, AND ON
SMPL IT FLIPS A GATE UNDER AN OPEN BUY~~ — GUARDED 2026-08-21 (`fix/quantity-kind-guard`).**
(Measured read-only 2026-08-18; the diagnosis below stands unedited.)

**THE UNLOCK THIS ENTRY NAMED WAS BUILT AS NAMED.** `Fact.quantity_kind` carries the structured
half of `basis` (`QUANTITY_KINDS` = outstanding | weighted_average), and `refresh_record` refuses
a swap on any `QUANTITY_SENSITIVE_FACTS` member — today `diluted_shares` alone, deliberately,
because demanding a declaration everywhere trains the operator to type past it.
**THREE DOORS, ALL CLOSED — and the first is the one the incident walks through.** The CLI could
only ever send a BARE FLOAT (`facts[k] = float(v)`), so the value moved while the basis kept
naming a quantity the number no longer was; a bare float is now REFUSED on a sensitive fact. A
declared swap (outstanding → weighted_average) is refused AS a swap. An UNSTAMPED record refuses
rather than guessing, because guessing means reading the prose. `--fact-kind KEY=KIND` was added
so the guard is actionable rather than a wall, and a same-quantity re-read still passes.
**THE CORPUS IS STAMPED, AND ONE RECORD DISAGREES WITH ITS SUCCESSOR ON PURPOSE.** Ten carry
`outstanding`; the archived `SMPL-2026-07-21` carries `weighted_average` — the pre-item-24 state,
kept as evidence rather than normalised to match the present. That disagreement IS item 24, and
it is the corpus proof the swap is real rather than theoretical.
**THE PROSE-PARSE TRAP CAUGHT THE BUILD ITSELF, which is the strongest argument for the field.**
A substring classifier over the real corpus stamped all eight `outstanding` records as
`weighted_average`: every basis MENTIONS the weighted average while explaining the quantity it is
NOT — EPAM's says outright that "the latest-quarter diluted weighted average of 52,267,000 is NOT
used". The stamps were then read one record at a time from an explicit map, never derived.
**A guard against prose comparison, nearly built by comparing prose.**
**INVARIANT (INVARIANT RULE):** `tests/test_quantity_kind_guard.py`, 21 pins — the incident
reproduced on the live SMPL record, the stake pinned as a number (its gate still reads PASS while
the swap is refused), the legitimate re-read still open, corpus stamps checked, and the archive's
deliberate disagreement pinned. Mutation-verified 7/7: each door reopened, the sensitive set
emptied, an unlisted kind admitted, a record's stamp cleared, the archive normalised — all killed.
Four pins in `test_dilution_denominator` used `diluted_shares` only as a VEHICLE for general
refresh-log mechanics and were re-pointed to `net_debt`, so they keep testing what they were
written to test; the one genuinely about the swap kept the fact and declares the quantity.
**ACCEPTED RESIDUE:** the unit strings on AORT/MVST/NCNO read `shares` while their values are in
MILLIONS (the engine assumes millions regardless). Pre-existing, untouched here, and NOT reachable
by this guard — a merely mislabelled unit is a different defect from two quantities sharing one.**

THE MECHANISM, not just the conclusion. The two sides carry DIFFERENT QUANTITIES, uniformly:
  * the RECORD's `facts.diluted_shares` is **diluted shares OUTSTANDING** — basic outstanding +
    dilutive increment, a point-in-time count (item 24's denominator work);
  * the DOSSIER ANCHOR's is **diluted WEIGHTED-AVERAGE (latest 10-Q)**, from
    `EDGAR WeightedAverageNumberOfDilutedSharesOutstanding`.
Both bases are uniform across all SEVEN records carrying the fact. **So every `diluted_shares`
divergence in a record-vs-anchor sweep is the CONVENTION WORKING, never staleness** — and a
refresh replaces the analyst's denominator with the quantity item 24 was built to remove.

**MEASURED CONSEQUENCE (in-memory recompute, nothing written):** SMPL record 88.460545M vs anchor
89.940680M (−1.65%). Refreshing that one fact moves **ratio 2.0952 → 1.9540** (bar 2.0) and
**gate PASS → FAIL** — headroom was +4.76%. SMPL is the fund's ONLY open position and the ledger
carries a BUY at $11.33 struck on the passing number. `refresh_record` RECOMPUTES THE RESULT
through the engine, so the stored ratio does NOT stand while its inputs move underneath.

**WHY NOTHING WARNS — and why the obvious guard cannot be built as specified.** `refresh_record`
already REFUSES a unit change, on the stated reasoning that *"basis is prose about the same
quantity; unit is the quantity's scale"*. **That assumption is exactly what fails here:**
outstanding-plus-increment and weighted-average are DIFFERENT QUANTITIES wearing the SAME unit
(`M shares`), so the unit guard is structurally blind to the swap. And `Fact.basis` is a free
`str` — a basis-comparison guard would be a TEXT comparison of prose, which is the shape this repo
refuses outright (parsers consume structured values, never rendered strings). **DESIGN FINDING: the
guard is not buildable until `basis` carries a structured quantity-kind** (e.g. `outstanding` vs
`weighted_average`) beside its prose. Recorded as ACCEPTED RISK with that unlock; nothing built.

**THE METHOD LESSON (beside the guard-scope ladder):** a divergence table without the BASIS ON BOTH
SIDES cannot tell a defect from a convention. Fourteen divergent cells were measured; **seven were
the convention working, one was a documented deliberate deviation (EPAM `net_debt`, FINANCIAL-ONLY
by its own basis string), two were real vintage staleness (AORT, IT `net_debt`), one ambiguous
(BRBR, a CARRIED value whose basis never says lease-inclusive).** The alarm inverted on reading the
second side: SMPL's PASS is sound and the REFRESH would have been the error.
