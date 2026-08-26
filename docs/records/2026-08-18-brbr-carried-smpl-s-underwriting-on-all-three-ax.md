---
id: 
status: shipped
date: 2026-08-18
prs: [469]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BRBR CARRIED SMPL'S UNDERWRITING ON ALL THREE AXES — CLOSED 2026-08-18 (#469).** The
2026-08-17 fix withdrew the MULTIPLE axis only (7/7 references) and I deleted the
`KNOWN_FOREIGN` allowlist on the strength of it. That was 1/3 of the defect, and the partial
fix is exactly what hid the rest: withdrawing one axis stopped guard 1 hashing BRBR's
assumptions block to SMPL's, so the REVENUE (3/3) and MARGIN (5/5) references — still
byte-identical to SMPL's — became both unguarded AND unrecorded. BRBR's page printed
`FY2025 reported revenue $1,450.9M` against BellRing's own 2,316.6. **NOW WITHDRAWN: 15/15
across all three axes**, each with its reason inline on the rendered surface; the bear/base/bull
legs are BellRing's own (2,250 / 2,385.47 / 2,500) and did not move.
**THE SECOND SURFACE — `facts.ltm_revenue`:** it read `1392.235`, SMPL's LTM to the last
decimal, cited to *BellRing's* anchor block, rendering as a TIER-1 DECISION VALUE. Every guard
in `tests/test_scenario_reference_binding.py` missed it because they hash `assumptions` and
`facts` is its sibling. Corrected to **2,354.6** through `scenarios.refresh_record` — the one
path for machine inputs, which refused nothing (it touches no analyst-owned surface) and logged
value and source as separate `refresh_log` entries. The number was not chosen: `anchor.
_ltm_revenue_from_fs` derives 2354.6 from BRBR's own financial summary and 1392.235 from SMPL's.
**INVARIANT SHIPPED (INVARIANT RULE):** `test_no_two_records_share_a_name_specific_fact_value`
flags two records sharing a name-specific MAGNITUDE fact (ratios excluded — a shared 0.21 tax
rate is not a paste). Mutation-verified against the LIVE corpus: restoring the real 1392.235
turns it RED naming `('ltm_revenue', 1392.235): ['BRBR', 'SMPL']`.
**RESIDUE — ANALYST, OPEN:** BRBR's `notes` prose still argues from SMPL's figures. The machine
must not rewrite it; the withdrawal marks say so on the page. BRBR is NOT decision-ready until
the analyst re-derives the three axes and the prose.
**THE LESSON:** a partial fix that disables the guard covering the unfixed remainder is worse
than no fix — it converts a detected defect into an undetected one. Withdraw the whole axis set
or none, and never delete an allowlist entry on evidence produced by the same partial change.
