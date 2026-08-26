---
id: 
status: shipped
date: 2026-07-29
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**ITEM 1 — BUILT 2026-07-29. THE BLOCKED-BY WAS STALE, AND THE DEFECT WAS LIVE ON ALL ELEVEN.**
The stamp said "do not merge until price freshness can meet panel arrival"; the same item also said
the re-spec "no longer depends on ingestion cadence". Measured: a fresher instance of the close
exists on **1 of 11** names, so the contract does not fail builds by design. **But 1-of-11 was a
WARNING, not a green light (operator).** The ten pass because a July price correctly beats a June
comps close — and then the page renders JUNE caps, TEVs and peer multiples beside that July price.
**EVERY committed dossier fails cap÷shares vs its own spot**: SMPL −2.4% (the audited name, the
SMALLEST), NCNO +3.3%, IT −7.1%, VRRM +8.6%, CNXC +8.9%, AORT −12.9%, BRBR −13.0%, VITL −14.1%,
EPAM −14.4%, MVST +17.6%, FUBO −91.0%. Cap feeds TEV feeds every EV multiple and the FCF yield.
**A MEASUREMENT ERROR, MADE TWICE, INVERTED THE RANKING.** Mixing dates that TRAVEL WITH A VALUE
(an own-history band's observation date — item 20's own fix) with dates that describe an ARRIVAL
(a panel export) put SMPL at 115d, top of the staleness list. Panel-only, SMPL is **3d — the
TIGHTEST in the fleet**. Real distribution 3–71d, median 36d, not 15–205d. Rule now in
docs/engineering.md.
**TWO GUARDS, BECAUSE NEITHER PREDICTS THE OTHER** (BRBR worst spread 71d with a middling gap;
MVST 54d with the worst drift gap): a 45d SPREAD CEILING for staleness and a RECONCILIATION for
incoherence. **CEILING SET AT 45, NOT 60 (operator):** at 60 only BRBR fails, and CNXC — cleared
under 16c this week — passes silently on comps 49 days old whose peer multiples drive the
cross-sectional leg.
**DRIFT IS NOT FATAL, BY DESIGN.** At any tolerance the reconciliation fails 11/11, which is a
freeze wearing a guard's name. A June cap is not WRONG, it is UNLABELLED — clause (e). So the cap
now RENDERS ITS OWN VINTAGE on both twins (`cap $1.3B (2026-05-14)` beside `CMP $12.95
(2026-07-24)`), and the panel spread renders on EVERY dossier, passing or failing.
**THE RATIO DIAGNOSES (operator's design).** Near-integer = corporate action; fractional = drift.
**FUBO 11.13× is a ~1-for-11 REVERSE SPLIT straddling the panels** — EDGAR's pre-split 342.4M
shares against CIQ's post-split $256.4M cap and $8.33 close. Sole instance; every other name sits
0.85–1.17. Half of it was recorded in STATE item 4 ("an 11x gap; reverse split?") and left open.
**PER-NAME GATE (the standing rule): FIRES ON 4/11, QUIET ON 7.** BRBR 71d, MVST 54d, CNXC 49d fail
the ceiling; FUBO fails the share basis (its 42d is inside the ceiling). The seven quiet names are
quiet because they DRIFT — pinned, so a name that later reconciles moves the assertion rather than
weakening it silently. VRRM sits at exactly 45d and passes: the ceiling is `>`, pinned.
