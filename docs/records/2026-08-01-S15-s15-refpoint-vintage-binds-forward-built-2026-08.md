---
id: S15
status: recorded
date: 2026-08-01
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**S15. `RefPoint.vintage` — BINDS FORWARD, built 2026-08-01. P3 pt1 DOES NOT CLOSE ON CODE.**
*(Renumbered from S10 on 2026-08-01: #302 reused a number already held by Batch A, above. The OLDER entry keeps S10 — renumbering it would break existing citations — so the interloper moved. Found by enumerating the record for a handoff, which is the only reason a duplicate identifier surfaces at all.*
*CITATION SWEEP RUN BEFORE THE RENUMBER MERGED, across three surfaces: tracked files (zero hits outside this file), all commit messages (zero), and **300 GitHub PR bodies plus every comment on #299–#306**. **ONE stale citation exists and it is OUTSIDE the repo: PR #302's body says "STATE.md §S10" and means THIS entry, now S15.** It is left as written — a merged PR body is a record of what was said at the time — and corrected here instead, because the record is what a handoff reads. #304 cites S12 and is unaffected.)*
A reference's `source` names WHERE a value came from and never WHEN: `CIQ Estimates->Trends`,
`EDGAR RevenueFromContractWithCustomerExcludingAssessedTax`, `EDGAR OperatingIncomeLoss / revenue`
name a source and a concept, no period. Census over **all 119 committed references** (7 records):
**49 (41%) carry a date/period token in `source`; 70 (59%) carry none.**

`RefPoint.vintage: str | None` added, gated by `VINTAGE_REQUIRED_FROM = "1.4"` on the record's OWN
`schema_version` — the `BASIS_REQUIRED_FROM` precedent. `SCHEMA_VERSION` 1.3 -> 1.4. Free text, not
a `date`: the honest answer is a fiscal period (`FY2025`) at least as often as a day, and typing it
as a `date` would make an analyst invent one.

**THE 70 ARE NOT BACKFILLED, and this is the entry that says why.** Their vintage is not in the
record and is not recoverable from it — it lives in the analyst's source material (the CIQ export
date, the filing period behind each concept). A backfill is a manual pass over 119 references
against that material: an OPERATOR DECISION, not a queued build. So the field stops the next
reference from being unstamped and repairs none of the ones that already are — **audit P3 pt1
stays OPEN and does not close on code.** All 7 committed records verified at schema 1.3, i.e.
below the gate, so nothing in the tree is silently in violation; a pin walks them and reddens the
day one is bumped to 1.4 without its references being stamped, which is the day the backfill
stops being optional.

MUTATIONS, both directions (a forward-binding rule that also fires backward is an unauthorised
migration; one that fires in neither is decoration): gate removed -> RED; gate stripped of its
version key so it fires retroactively -> RED. Whitespace-only vintage refused. Raising
`FIELDED_REFS_FROM` above 1.4 also reddens — the vintage check sits inside `require_fielded_refs`
and rides its early return, so the coupling is pinned rather than merely noted.

**ARTIFACT DRIFT — MEASURED, and the first cut of this entry under-reported it.** `write_record`
uses `model_dump_json` with no `exclude_none`, so the NEXT re-render of the 7 committed records
writes **119 new `"vintage": null` keys**, one per reference (AORT 24, MVST 21, NCNO 16, IT 15,
SMPL 15, EPAM 14, WERN 14). `schema_version` correctly stays 1.3 on all seven, so the gate does
not fire and the writes succeed. The nulls are the honest record — "this reference has no vintage"
stated rather than implied — but the diff is real and belongs here, not discovered at the next
artifact pass. The **seal is unaffected**: `vinci/seal.py` digests the rationale text only, never
the record body.

**REVIEW FINDING (#302), FIXED IN-PR — the field would have been invisible to the human.**
`frontend/build.py`'s reference builder is an explicit key ALLOWLIST, so a stamped `vintage` was
dropped on the way to the card: required by the backend, unreachable by the reader. A provenance
field the human never sees is not provenance. Now rides the card in the allowlist's own idiom —
emitted only when set, so all 7 committed 1.3 records stay byte-identical (verified by re-running
`frontend/build.py`: empty diff). Pinned both ways, and the fix mutates RED.

**INCIDENT (this build, in the guard shipped for this exact class).** `test_record_hygiene`'s
`QUOTE_ESCAPE` documented itself as a regex "over that shape so a variant nobody has seen yet is
still caught" — it was an alternation of TWO LITERALS. It ran green over **six** three-apostrophe
possessives sitting in this file (the backslash form of the POSIX escape, with its backslash eaten).
NAMED IN WORDS, NOT WRITTEN: the guard catches the idiom, so the record that documents the incident
cannot spell it — the cost this guard's own note predicted for the speculative heredoc pattern,
now paid for real by the pattern that earned its place. Third shape added on observation,
tree re-scanned clean, and the comment corrected to describe what the pattern does. INVARIANT: the
pattern now enumerates three; the note no longer claims a generality it lacks.

**NOT DONE — the spot-divergence measurement.** The seven `spot_source` strings name three fetch
routes (per-symbol `daily_bars`, `grouped_daily`, a store read), so the seven spots are not
strictly comparable. Measuring the divergence per name, and what it does to each reward:risk
(IT sits at 1.52 against a 2:1 bar), was the second half of this task and was NOT reached.
Unblocked — it is a read, no decision pending.
