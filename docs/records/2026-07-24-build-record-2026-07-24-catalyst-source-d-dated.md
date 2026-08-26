---
id: 
status: recorded
date: 2026-07-24
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD RECORD — 2026-07-24 CATALYST SOURCE D (dated operating events) + SMPL's FIRST DATED
TRIGGER (branch `feat/catalyst-source-d`, stacked on `feat/catalyst-calendar`; BOTH operator-
ratified same day in plain-language form).** ORIGIN: the operator asked whether SMPL's
management-stated "high single-digit price increase … effective in September" (Q3-2026 call,
transcript uploaded to the manual store same day, pipeline-read verified at 57,530 chars) is a
catalyst — it is the SHARPEST kind for SMPL (the decisive question is literally pricing power),
and v1's calendar could not see it (the #209 disposition was amended: source C shipped
maturities-only). SHIPPED (source D): `_dated_operating_events` — an ANCHORED forward-action
pattern over the already-extracted driver verbatims (effective/launch/open/begin/start/roll
out/ship/transition/commence … MonthName): month-granular `YYYY-MM` dates (a fabricated day would
be a guessed date; CatalystRow docstring updated; lexicographic sort keeps YYYY-MM ahead of its
month's days); year resolution = the NEXT occurrence of the month on/after the reference (explicit
year honored); PAST-tense excluded by the verb alternation itself, backward references
("last September") rejected post-match, past-resolved months dropped; event text = the CLAUSE
carrying the match (a blind 120-cap was cutting the event out of a long sentence's lead-in);
dedup by (month, clause). No-match → no row, silently (no event stated is normal; only an
unreadable DATE flags). REAL RUN on the actual Q3 sentence → `2026-09 [stated]` with the clause
and the transcript source_ref; negatives (past-tense / "last September" / dateless) all zero;
rollover March@Jul→2027-03; explicit 2028-01 honored. Pins: the frozen real-sentence fixture +
all negatives + year rules + dedup + month-sort.
DATA (separate commit, operator-authorized wording 2026-07-24): SMPL `verdict.dated_triggers` +=
{trigger: "September portfolio-wide price increase fails to stick (elasticity / share loss)",
deadline: 2027-01-07, basis: "second print after the September action — the Q1-FY27 print
reveals elasticity; operator-confirmed 2026-07-24"} — written via the model, rationale
byte-identical, seal re-verified CLEAN. The calendar renders it TRIGGER-DEADLINE; the monitor
starts the clock at the next snapshot. FOLLOW-ON (operator, standing): the Q2+Q3 transcripts now
in the store mean SMPL's next re-assembly extracts the September driver row itself (the gated
transcript phase sees all three calls).
