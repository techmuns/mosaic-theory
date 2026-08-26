---
id: 
status: recorded
date: 2026-07-24
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-24 SMPL INPUT-STALENESS DISPOSITION EXECUTED (C3 data, branch
`data/smpl-staleness-disposition`; operator ratified the plan + wording in chat same day).**
The incident (verified): the committed dossier (assembled 2026-07-23) and the scenario facts
rode CIQ panels predating the 2026-07-09 FQ3 print (multiples as-of 2026-06-03, TEV as-of
2026-06-25, reference 2026-07-06) — the 2026-07-21 BUY read a pre-Q3 P&L. EXECUTED, in order:
(1) CLOSE ROW `C-SMPL-screen2-20260706` closes `V-SMPL-screen2-20260706` at 10.53 (2026-07-22
point-in-time freeze; entry 10.92/2026-07-20; realized −3.5714% before costs, derived never
stored; register-clean stated reason). Appended via the model + the guarded exporter — the
committed snapshot IS the ledger of record (both working DBs carry 0 ledger rows; #121 guard);
file re-canonicalized to the exporter's PK order, which corrected the IT card's close-blind
last-row-wins ledger join in passing (join fix spun off as its own task). (2) SEAL-LEGAL
amendment tag + `status confirmed → watch` (IT transition, PR #191); seal check_all CLEAN ×7;
the dated September trigger untouched. (3) FULL RE-ASSEMBLY on the fresh 2026-07-24 export
(tev_as_of 2026-07-24, multiples_as_of 2026-07-21, summary floor ≥2026-07-21; P/LTM caveat
re-fired on the fresh shape — LTM GAAP dil EPS still −2.08 — so the #208 artifact pin stays
armed) + MACHINE REFRESH of the record's stale-layer facts: ltm_revenue 1416.208 → 1392.235
(the only stale-layer fact — net debt / D&A / diluted shares were filing-derived and already
current), spot 10.92 → 10.53; legs untouched (analyst's), per-leg vps unchanged, ratio
4.0299 → 4.5785 (PASS vs 2.0), engine==stored verified; second amendment tag documents it.
CALENDAR NOTE (honest miss): the fresh driver phase surfaced a NEW dated event (Target
exclusive launch → `2027-01 [stated]`, year-rollover correct) but did NOT surface the September
price-increase sentence this run — the LLM driver tier picks its verbatims (weather); the
September falsifier still rides the calendar as the analyst's dated-trigger row. Data-coupled
test restorations shipped with the close (no open BUY / no confirmed record is now a legitimate
book state; synthetic fallbacks per TEST-LAYER).

**ANALYST / OPERATOR — SMPL RE-VERDICT PENDING (the disposition's step 4, open).** The record
sits at `watch` with refreshed arithmetic (4.58:1 at 10.53); the re-verdict is the analyst's,
on a NEW candidate row (one decision row per candidate, by construction — the next screen
vintage or an operator-created candidate). INVARIANT: the assembly-freshness gate — **SHIPPED
2026-07-24** (see build record below); the incident is closed per the INVARIANT RULE.
**SUPERSEDED IN PART 2026-07-26 by the Q3 re-verification (below): the record stays at `watch`
by operator decision, its assumptions re-set on Q3 data. Re-entry remains a new decision on a
new row.**
