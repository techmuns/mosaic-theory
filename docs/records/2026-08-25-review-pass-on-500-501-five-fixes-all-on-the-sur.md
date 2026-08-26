---
id: 
status: recorded
date: 2026-08-25
prs: [500, 501]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**REVIEW PASS ON #500/#501 — FIVE FIXES, ALL ON THE SURFACE OR THE ABSENCE PATH (2026-08-25).**
The call arithmetic and the fence survived review untouched; everything found was in what the cell
SAYS and in what an empty read carries.

- **`peers` was 0 on every empty read.** `CohortRead(call=NO_COHORT)` never set it, so all 75
  no-cohort rows of the committed queue said `peers: 0` and the cell rendered *"measured against
  the 0 Aircraft names in the screened universe"* for an industry that has three. `peers` is now
  carried on every read, counted off the already-grouped members (which also drops the per-row
  re-derivation of all ~1,750 screened industries). Pinned by
  `test_an_empty_read_still_says_how_many_peers_there_were`, mutation-verified.
- **The unresolved-SIC bucket could become a cohort.** `industry_for_sic` returns `"Unknown"` for a
  blank/absent/non-numeric SIC, and the coverage guard tolerates **20% unresolved — ~350 names at
  screen scale**, far past `MIN_PEERS`. The aggregate guard would have passed while that bucket
  took a median over a grab-bag and issued `own`/`cohort` calls against it: the fabricated-value
  class the module docstring forbids, arriving *underneath* the guard written to stop it. Latent
  only (coverage is 100% today), now dropped explicitly at any size. Pinned by
  `test_the_unresolved_sic_bucket_is_never_a_cohort_at_any_size`, mutation-verified.
- **The surface said 6 peers; the floor is 5.** The header tooltip, the label map and the glossary
  all said "under 6" while `MIN_PEERS == 5` — and **11 committed rows carry a 5-peer cohort the
  surface said could not exist**. All three corrected, and the number is now one named JS constant
  (`COHORT_MIN_PEERS`) rather than a digit written into three sentences.
- **One label served two different findings.** A no-cohort read has two causes — *the industry is
  too small* and *this name is not in the newest screen log* (the queue ranks off an older
  candidate snapshot). Both committed rows of the second kind read "too few peers" beside a
  **12-name** cohort. The pill now branches on the peer floor.
- **The idio column lost `num: true`**, leaving one left-aligned header in a row of right-aligned
  numeric ones and the figure beside Depth without `var(--mono)`. Restored; the WORDS inside the
  cell opt back out to `--sans` so the pill does not read as data.

Also: `vinci rank`'s carry-forward used `annotations or carried_causes`, so a `--cause-file` that
annotates nothing was silently overridden by the carried set instead of clearing it — now keyed on
whether the flag was PASSED, not on truthiness. `ranked_queue.jsonl` re-generated on the fixes:
order and every score identical, `cohort.peers` the only field that moved.

**PHASE 0 (the LLM cause classifier) IS NOT BUILDABLE AS SCOPED — FOLDED INTO PHASE 2.** `cause_class`
reads `"unclassified"` on all 268 not because the pass is unwired but because **there is no textual
de-rating source at queue scale at all**: every one of the 525 committed events is
`earnings_gap_down`, produced by the EOD gap-down detector (`screens/assemble.py:359`), with **no
accession and no document**. `rank/cause.py` needs `derate_text`; nothing supplies it. Turning it on
requires 8-K text per de-rated name — the same per-name EDGAR fetching Phase 2 needs, so it rides
with that rather than being half-built. The ranker's own comment already anticipated this split.
