---
id: 
status: shipped
date: 2026-07-27
prs: [224]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**INCIDENT — 2026-07-27 #224 MERGED RED; ARTIFACT-PASS RULE VIOLATED BY ITS OWN AUTHOR.** The
re-assembly PR reported "1076 passed" for the whole cohort. That number came from the 3-name PILOT
run; the suite was NOT re-run after the second batch of 6, and `main` merged with
`test_next_evidence_prefers_the_calendar_then_a_trigger_then_says_unknown` RED. Cause: that test
hardcoded **AORT** as "the name that carries no calendar" — a data-STATE pin on a LIVING artifact —
and the re-assembly gave AORT a calendar (2026-08-06), so it reddened on CORRECT behaviour. Exactly
the failure mode the TEST-LAYER RULE names. FIXED ON MAIN BY #226, INDEPENDENTLY AND BETTER — this
build had swapped in a synthetic `NO_SUCH_TICKER`, but #226 re-pointed the fixture at **WERN**, which
has no dossier at all (so no calendar CAN exist for it) and added `assert not (…/dossiers/WERN)
.exists()` so the fixture POLICES ITSELF if WERN is ever covered. A structural UNKNOWN beats both a
temporary one and a name that can never exist; #226's version was taken wholesale at the merge and
this build's was discarded. The same staleness left FOUR `frontend/scenarios/*` mirrors claiming
"no scheduled evidence" while their dossiers carried calendars (AORT/EPAM/IT/NCNO — resolved to real
rows, basis `cadence-estimate`, by #226's mirror rebuild). INVARIANT: the ARTIFACT-PASS RULE was already
written and was simply not followed — the gap is compliance, not a missing rule. Recorded here rather
than papered over: a green claim sourced from a PARTIAL run is a false green, and the pilot-then-batch
shape is where that mistake is easy to make. Any future batched artifact pass re-runs the FULL suite
after the LAST batch, not after the pilot.
