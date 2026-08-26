---
id: 
status: recorded
date: 2026-08-12
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**THE DECISION CHAIN WAS THREE PIECES THAT NEVER TOUCHED (2026-08-12, operator-reported). Each
worked; nothing joined them.** Diagnosed on a copy of the committed tree, measured not read:
1. **`log-verdict` wrote to the working DB and stopped.** The DB is a CACHE — the durable record is
   `data/snapshots/decision_ledger.jsonl`, which is what `vinci monitor`, the frontend mirror and
   every fresh clone read (`_cmd_monitor`'s own docstring says so). **After a ledger write the DB
   held 7 rows and the committed snapshot still held 6, byte-identical.** A logged verdict reached
   no reader until somebody happened to run the weekly screen or the monthly score — both of which
   export only as a SIDE EFFECT of doing something else. No data was lost (`rebuild_from_snapshots`
   is INSERT-OR-REPLACE, so a local row survives a rebuild) but it never left that machine.
2. **There was no close command at all.** `4f34c11` shipped the close-row SCHEMA, the readers
   (`monitor.close_rows` / `pair_closes`), the display and the id helper — everything except a
   writer. **Both committed closes were therefore hand-authored JSON**: rows that reached an
   append-only record without passing one guard.
3. **Nothing rebuilt the frontend.** `frontend/` is derived from committed data by
   `frontend/build.py`, and Cloudflare Pages serves it AS COMMITTED — so a stale mirror IS the
   product. It stayed correct only because whoever changed data remembered to rebuild.
**FIXED:** every ledger-writing command now flushes the ledger table to the committed snapshot
(`_export_ledger`, ledger-table-only so a half-populated working DB cannot rewrite the universe
snapshots); `vinci close-position` is the missing writer, with the guards the hand path never had
(unknown candidate · second close · exit-before-entry · blank reason, each pinned and each writing
nothing on refusal); and the CI gate now fails a PR whose `frontend/` is stale — a CHECK, not an
auto-commit, because CI holds `contents: read` and a workflow pushing generated files back would
make main move under review. The class rule is AST-pinned: a `_cmd_*` that reaches a ledger writer
without `_export_ledger` fails the suite.
**THE FIX'S OWN P1 — A POISON ROW COULD ENTER THE APPEND-ONLY RECORD (operator review on #417).**
`model_copy(update=…)` runs NO model validators and `Store.append_ledger` only serialized, so
`close-position --exit-price -1` passed every guard, **printed success (exit 0), wrote the row, and
made the next `iter_ledger()` RAISE** — one flag rendering the whole decision ledger unreadable, in
a record from which nothing can be deleted. Reproduced before fixing: snapshot 6→7 rows, then
`ValidationError` on read. **Two layers now:** `close_position` re-validates the built row and
refuses at the command, and **`Store.append_ledger` re-validates on the way in as the backstop for
every writer, including ones not yet written** — a `LedgerEntry` argument looks like proof of
validity and is not. INVARIANT: no unvalidated row reaches the append-only ledger; machine-checked
at the store, so it holds for callers this file has never seen.
**ONE TEST IN THIS BUILD PROVED NOTHING AND WAS CAUGHT BY MUTATION.** `assert close.facts == {}`
ran against a corpus where **no decision carries a fact at all** (all six rows: zero), so deleting
the writer's clear left it green. Re-pinned on a seeded fact-bearing decision. This is the
CORPUS-BEFORE-SYNTHETIC rule biting in the direction it usually does not — the corpus was too thin
to exercise the guard, and only the mutation said so.

43. **IC RESPONSE MEMO — THE NEXT ARTIFACT.** The external review's closing fact is the exit; the
    memo answers the review with what was verified, what was refuted, what changed, and what the
    exit realized. Everything it needs is now committed.
44. **BEAR-STATE PULL → REUSABLE RUNBOOK STEP.** The 2026-07-22 cross-section pull (admission test,
    per-name admit/reject with numbers, TEV basis stated, margin-retention-through-decline) becomes
    a standing runbook step for any name whose own history lacks a bear-state precedent.
45. **EXTENDED OWN-HISTORY CIQ PULL (~2006) — OPTIONAL DEPTH.** IT's committed multiple window
    opens 2017Q1, so pre-2015 and the 2008-09 trough are unobservable. A pull back to ~2006 would
    let a slower-growth Gartner be priced from its own record rather than the cross-section. Not
    blocking — the cross-check convention (above) covers the gap.

46. **MVST BEAR_BASIS UNRESOLVED — the one backfill withheld.** Its multiple method says the exit
    is *"set AT the closest economic analogue - a levered auto-parts maker"* (BorgWarner, 7.9x
    reference; bear 6.0x), which reads `peer-reference`; the brief expected `analyst`. Prose does
    not determine the enum, so it was NOT guessed. MVST stays at schema 1.1 with both labels
    absent until the operator rules. One line to close.
47. **PEER MARGIN FRAMES MIX EBITDA WITH EBIT (AORT, MVST) — BASIS-MISTRANSLATION CLASS, SIXTH
    SIGHTING.** The running tally: EBITDAR-vs-EBITDA (VITL), LTM-vs-same-period (NCNO), a display
    string re-parsed thousands-blind, EBITDA-margin-vs-EBIT-margin in an advisory brief, the
    $72.24 EBITDA cell under an EBIT label, and now peer reference frames quoted on a different
    line from the legs they anchor. Six sightings across four surfaces is not a run of bad luck;
    it is the defect this book produces when a number travels without its basis. Both records cite peer margins on an
    EBITDA basis (Boston Scientific 26.7%, LeMaitre 30.7%, BorgWarner 13.9%) beside their own legs
    stated on the operating line. AORT's margin method ADDRESSES this explicitly and adjusts;
    MVST's does not. Not a defect in either cell — the engine adds D&A — but it is the exact
    cross-basis comparison `margin_basis` exists to make visible, and the reference frames should
    carry the label too.
48. **ENTITY GATE — NCI / SHARE-CLASS CHECK (gates any FUBO record).** The audit's entity check
    reads the diluted-vs-outstanding gap but has no NCI or multi-class detector beyond a text
    scan, and a pre-combination dossier defeats a text scan by construction.
