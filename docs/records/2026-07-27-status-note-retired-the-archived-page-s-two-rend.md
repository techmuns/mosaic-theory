---
id: 
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md governance log
---

24. **`status_note` RETIRED + the archived page's two render defects — 2026-07-27 (operator).**
   Three decisions, one PR.
   **(a) THE HEADER IS THE RATING ALONE.** `VERDICT watch`, nothing beside it. The holding word
   and caption were a third statement of a fact the band already carries: the ENTRY cell reads
   *"— no position"* for a record holding nothing, and a closed position states its close inside
   the verdict chip. `.uw-hold` / `.uw-hold-note` deleted with them.
   **(b) `verdict.status_note` RETIRED OUTRIGHT** (schema, validator, 25-word cap, the
   `frontend/build.py` emit, and the value in BOTH records). It was added at #15 for the
   current-state block; #22 folded that block into the masthead and (a) removed its last renderer,
   leaving a card key nothing reads — the kind that gets read again by mistake. Shortening the
   caption twice (13 words → 6) and still finding it redundant was the evidence that the SLOT was
   wrong, not the wording. **The archived record was edited this time** — a reversal of #23's
   "history is not edited", and the distinction is the point: #23 changed the *words of a caption*
   (a judgment, which history owns), this deletes a *retired field* (a schema migration, which
   history does not). The seal is unaffected either way: it digests `base_text(rationale)` only —
   swept all 7 live+archived records, **INTACT**.
   **INVARIANT SHIPPED:** pydantic defaults to `extra="ignore"`, so every stale record would have
   loaded CLEAN and lost the analyst's sentence on the next write — a silent drop, the one failure
   this repo never takes. `RETIRED_VERDICT_FIELDS` + a `mode="before"` validator now RAISE, naming
   the key. Demonstrated against git's own pre-change `scenarios/SMPL.json`: refused.
   **(c) THE ARCHIVED PAGE HAD TWO DEFECTS**, found only by opening it — neither was visible to
   the suite. (i) The record-only path looked its ledger row up with `e.ticker === ticker`, but on
   that path `ticker` is the ROUTE key (`SMPL-2026-07-21`), so nothing matched: the page printed
   *"no verdict logged yet for SMPL-2026-07-21"* directly beneath a masthead correctly reading
   *"BUY — closed 2026-07-22 at $10.53"*, and offered a CLI recipe on a FABRICATED candidate id.
   It now takes `build.py`'s `_ledger_for_record` answer and resolves by entry id — one authority
   for which record owns a row. (ii) `loggedVerdict` was the **FIFTH** close-awareness surface
   (#21 fixed four and missed this one): SMPL's exited position read as a live *"BUY ·
   unresolved"*. `resolved` stays untouched by design — a call is scored at its horizon whatever
   happened to the position, so exits never launder the track record — and the close is stated
   additively with its realized return and reason.
   **LESSON, third time this week:** the browser served CACHED ES modules and showed a CLOSE row
   masquerading as the decision row. That looked exactly like a loader bug and was not one. A
   render verification is only valid against force-refetched modules.
