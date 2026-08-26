---
id: D18
status: recorded
date: 2026-07-31
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**D18. THE `tail` BOUND, and the FIXTURE DESIGN that retires D17** (operator 2026-07-31).

**HOW FAR THE UNGATED-PUSH PATTERN REACHES — bounded, not unknown.** The general form of D16 is
*any command whose exit status is consumed by a pipe is not a gate* (`tail` exits 0 whatever it
read). How many past commits ran that way is not reconstructable. But the bound is stronger than
"unknown": **a persistent red would have surfaced** — main verifies green at HEAD with each
command run separately, and subsequent sessions ran the suite and reported. **REPEATED INDEPENDENT
GREEN RUNS ACROSS SESSIONS are the evidence, not growth** — so anything merged broken was transient or was fixed
later without anyone noticing which. Weaker than a verified history, stronger than "unknown", and
stated deliberately: **"unknown" invites someone to re-audit history that cannot be re-audited.**
**CORRECTED AT REVIEW, because the bound's own evidence was two unchecked claims.** The first
draft argued from "the suite has grown MONOTONICALLY from ~1,130 to 1,394". Neither half survives:
~1,130 is a number nobody measured, and monotonic is FALSE on this session's own observations —
1397 passed became 1394 when #286 turned three corpus pins into skips. Total collected did not
shrink, but the figure quoted as evidence did. **An argument for a bound must not rest on a
statistic asserted from memory** — that is the defect class this whole run keeps finding, appearing
inside the record written to bound another one (D15, again).

**THE THREE CORPUS PINS HAVE NEVER GATED IN CI.** `data/cache` is git-ignored, so CI is always the
cold case: before #283 they hit the network or skipped silently; after #283 they skipped cold; after
#286 they skip on any attempted fetch. Honest at each step, useless at the end. **FIX, ahead of
retention: commit a FROZEN companyfacts subset for the eleven names** — the pattern `test_anchor`
and `test_band_guards` already use, and these were the only pins reaching for a real client. Then
they run offline every time and **D17's accepted risk dissolves instead of being carried.**
Three constraints, all operator, all recorded before the build:
1. **SUBSET BY CONCEPT, NOT BY BLOB.** Full companyfacts responses run to megabytes; eleven of them
   would be a large permanent addition. Freeze only the tags the pins actually read.
2. **VERSION THE FIXTURE WITH THE ARTIFACTS.** The corpus pins check committed artifacts against a
   recompute, so a fixture frozen at one vintage reddens when a name is later re-assembled from
   fresher EDGAR data — for a reason unrelated to the code. **The fixture updates in the SAME PR
   that re-assembles a name**, the `ANCHORS_AWAITING_BACKFILL` discipline: the pin TRACKS the
   artifacts rather than describing them.
3. **VERIFY BOTH DIRECTIONS**, as the offline fixture was: fixture present → pins run and pass;
   fixture mutated → pins red. **A fixture that cannot fail is the same defect one layer along.**
