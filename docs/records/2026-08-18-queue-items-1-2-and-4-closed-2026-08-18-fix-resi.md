---
id: 
status: shipped
date: 2026-08-18
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**QUEUE ITEMS 1, 2 AND 4 CLOSED 2026-08-18 (`fix/residue-and-brbr`) — ONE ANALYST ACTION SURVIVES.**
- **THE PRICE-MATCH RESIDUE WAS RECURRENCE, NOT MISSING DATA (item 4).** FUBO 9.70, MVST 0.92,
  UBER 68.18, VRRM 4.18 — all LOW-PRICED names whose close simply repeats across the history, so
  "exactly one match" refused four of nineteen. **Rule sharpened to the LATEST match STRICTLY
  BEFORE the stamp**, where two independent signals agree: the price identifies the bar, and
  "strictly before" is CIQ's measured convention (the panel carries the PRIOR trading close). On
  all four the answer lands exactly where the offset method predicts. **Fleet-wide: 13 unchanged,
  4 resolved, 0 moved** — and NIKE, whose printed close matches NO bar, still correctly refuses.
  **FUBO is why STRICTLY matters:** its 9.70 sits on both 2026-08-11 and the 2026-08-12 stamp, so
  admitting the same-day bar would publish an export date as an observation date.
- **ZERO NEGATIVE PANEL AGES FLEET-WIDE (item 2).** MVST −1 → +2; NFLX 0. A panel dated LATER than
  the page reading it no longer exists anywhere in the corpus.
- **BRBR's FOREIGN FIGURES WITHDRAWN, NOT REWRITTEN (item 1) — and the line is deliberate.** All
  SEVEN multiple-axis references are marked `excluded` + `excluded_reason`, the mechanism that
  renders them DIMMED WITH THE REASON rather than vanishing; it now says so 7× on both the PDF and
  the web page. **The ratified legs (6.0 / 8.5 / 12.0) are untouched** — the decision was always
  BellRing's; only the audit trail pointed at Simply Good Foods.
  **WHY NOT SWAP IN BRBR's OWN FIGURES:** the whole block is SMPL's — band statistics, the
  entry-boundary cells (1,100 × 8% is SMPL-scale revenue against BellRing's ~2,300), AND the notes
  prose reasoning from SMPL's $10.53 close. Replacing only the values would leave BellRing's own
  band contradicting prose still arguing SMPL's legs — one inconsistency traded for another.
- **⚠ ANALYST ACTION, STILL OPEN — BRBR's `assumptions.multiple.notes`.** The prose still reasons
  from SMPL's figures. **The machine must not rewrite it**: which reference justifies which leg is
  an underwriting argument, and free-writing it is the line the 2026-07-13 pivot draws. Restate it
  against BellRing's own band (low 4.29 / median 19.76 / current 9.18), then the withdrawn
  references can be re-derived and un-excluded.
- **GUARD 3 FIRED AND WAS RIGHT — the exemptions are RETIRED.** Withdrawing the references changed
  BRBR's digest, so it no longer matches SMPL's, and guard 2 now sees ZERO live references on the
  name. Both `KNOWN_FOREIGN` and `KNOWN_SHARED_GROUPS` are empty. **Deleting them RESTORES
  protection rather than dropping it, mutation-verified both ways:** re-paste SMPL's block → guard
  1 fires; un-exclude the references → guard 1 fires. An exemption is earned only while the defect
  it names is live, which is exactly what that guard exists to notice.
- **A FOURTH TEST WAS PINNED TO A MOVING MARKET.** `test_ubers_drift_is_stated_on_the_page` pinned
  `-13.2%` and `$78.54`, both functions of the LIVE CMP, so it broke on a routine bar refresh
  (−9.1% against a $74.99 close) rather than on the page going quiet. Re-pointed to assert a
  magnitude IS STATED, which is what it owns; mutation-verified by stripping the magnitude from the
  renderer. **That is four this session** — V's share basis, two dilution pins, and this — all
  BORROWING a property from live data instead of CONSTRUCTING it. Each would have stayed green
  through the defect it was written to catch.
