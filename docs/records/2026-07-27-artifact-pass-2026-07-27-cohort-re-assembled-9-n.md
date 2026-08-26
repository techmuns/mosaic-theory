---
id: 
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**ARTIFACT PASS — 2026-07-27 COHORT RE-ASSEMBLED (9 names) onto current engine code.** The
re-structure PRs (#219–#222) were RENDER work, but the cohort had drifted behind the ASSEMBLY
engine: 9 of 11 dossiers were assembled 2026-07-23 ~12:0x, BEFORE the catalyst calendar (#209/#211),
the benchmark cap-band fallback (#200), the P/LTM caveat (#201) and the assembly-freshness gate
(#213) merged. Consequence found by audit: **the catalyst calendar was ABSENT from 10 of 11
dossiers** — the section #216 fixed the web render for, and #221 promoted to slot 4, rendered for
exactly ONE name. Run as a PILOT of 3 then the remaining 6 (operator-directed), the pilot chosen to
test #200 in BOTH directions: NCNO (basis was the blind "cap UNKNOWN → default IWM") and IT (the
name that actually flipped MDY→IWM, sitting near the $4B boundary — the stop-gate). RESULTS: **zero
benchmark flips across the whole cohort**; every re-assembled name gained a calendar (1–4 rows);
synthesis PRESENT on all 9 (no null-overwrite incident); the #213 freshness gate fired for real on
CNXC ("2 CIQ valuation panel(s) predate the latest earnings print, the oldest by 24d"). NOT
re-assembled: **SMPL** (already current at 07-24 with its calendar, and carrying the operator's
#212/#217 work — re-assembly would have regenerated its synthesis for no gain) and **MVST** (the
deliberate back-compat case, screen question unresolved). HONEST NOTE ON #200: its ranker fallback
did NOT fire anywhere — NCNO's fix came from the CIQ cap RESOLVING once `data/manual` was linked in
this worktree (the basis reads the CIQ format, not "(screen-time, ranker)"). That confirms the
original defect's cause was environment-sensitivity exactly as diagnosed, but leaves #200's fallback
UNEXERCISED in production — insurance not yet called on. WEATHER, material: **3 of 9 leans flipped
`mixed` → `strongly-bearish` on re-assembly with NO prompt change** (BRBR, FUBO, VRRM). Leans feed
`derive_proposal`, so the machine PROPOSAL for those three moves from "none" (mixed proposes
nothing) to AVOID_TERMINAL. VRRM's new proposal AGREES with its recorded ledger verdict
(AVOID_TERMINAL); BRBR and FUBO carry no logged verdict, so nothing of record is contradicted. This
quantifies synthesis instability at ~33% of leans per re-draw — consistent with the 2026-07-23
weather-baseline experiment, and the reason that experiment's prompt "fix" was REJECTED rather than
shipped. Gate on the fresh artifacts: ruff + `mypy --strict` clean · 1076 passed. One test fix was
required and committed SEPARATELY (never bundled into an artifact commit): a py/js apostrophe-
escaping mismatch that reddened on correct output once the LLM wrote "Gartner's".
