---
id:
status: shipped
date: 2026-10-22
prs: [780]
supersedes:
superseded-by:
---

# An operator's recipe decision has its own block — the machine's writes copy it and never erase it; all six hand re-tags migrated, VITL's with its values held

**WHAT.** The anchor gains `operator_decision` (the decided `recipe`; the `reason` VERBATIM;
`decided_by`; `decided_on`; `source_ref` — the record it is taken from; `machine_recipe_at_decision`
where a record says what the machine read then) and `machine_recipe_hint` (the machine's own recipe,
kept beside a decision). `reason` is now always the MACHINE's. Both are absent, never null, on an
undecided page.
- **Both writers keep it.** Re-assembly (`assemble._keep_committed_recipe`) and `anchor-backfill`
  share ONE rule (`preserve_operator_tag`): a recorded decision is copied verbatim, its recipe
  applied, and the machine's recipe and reason refreshed beside it. Assembly no longer returns the
  FRESH dossier when the recipes match, which was the second way a reason was lost.
- **A divergence is shown, never resolved.** The page prints it from the block on every render (md
  and web), so assembly adds no caveat for a decided page. A PLACEHOLDER machine hint (`unknown`,
  `ANCHOR_UNRESOLVED`) is printed as a data gap, never as the machine disagreeing.
- **Every write is guarded.** `write_dossier` and `refresh_dossier` refuse a write that DROPS or
  ALTERS a committed decision. Only `vinci anchor-retag` may change one. They also refuse:
  - an anchor whose `reason` opens "OPERATOR RE-TAG" with no block, which was the old way of
    re-tagging and the next machine write erased it;
  - any write over a committed page that cannot be read as a JSON object, such as conflict markers
    left by a rebase. Such a write could not show that it keeps a decision it cannot see.
- **`vinci anchor-retag`** is the one writer of a decision.
  - It records `--recipe` and `--reason-file` (verbatim), with `--decided-by`, `--decided-on` and
    `--source-ref`; `--retire` removes a decision.
  - Every computed value stays as committed.
  - It REFUSES when the machine's read today moves a committed value, because the machine's reason
    would then describe numbers the page does not show. The one exception is `--values-held`, for a
    page whose values are deliberately held: the decision is recorded, the values stay, and no
    machine reason is written beside them. It never licenses a retire.
  - `--decided-on` must be an ISO date, read on the operator's LOCAL calendar and never after
    today. A BACKDATED decision records no machine read unless `--machine-at-decision` names one,
    and that must be a recipe the machine writes. Today's read is never filed as the read at the
    decision.
  - Every field is stripped before it is checked, so a blank field is a missing one. The decidable
    recipes are read off their constants, and a page that fails to re-render after the write fails
    the command loud.
- **On the page.** The block leads with the decided recipe and who decided it, when. The divergence
  flag or the gap line comes next, then the operator's words as a quote, then the source in an
  on-demand `<details>`, which prints expanded. The machine's reason prints beneath, labelled "The
  machine's read:".

**Migrated (each reason verbatim from git):**

| name | decision | decided | reason taken from | machine reads | source_ref |
|---|---|---|---|---|---|
| AMZN | `R4_forward_ev_ebit` | 2026-10-09 | the page (restored #701/#752) = `22320fca` | R4 (agrees) | `2026-10-09-amzn-uber-re-tagged-r4.md` (#698) |
| UBER | `R4_forward_ev_ebit` | 2026-10-09 | `58dd1ef6` — **erased by #705, restored here** | R4 (agrees) | same |
| GOOGL | `R3_forward_pe` | 2026-09-01 | the page = `c005449f` | R1 — **diverges** | `2026-09-01-r3-reaches-the-create-path.md` (#557) |
| AORT | `R2_NEEDED` | 2026-10-07 | the page = `feca6b93` | R1 — **diverges** | `2026-10-07-four-recipe-re-tags-restored.md` (#671) |
| CNXC | `R1_NOT_ROBUST` | 2026-10-07 | the page = `9b9228bc` | R1 — **diverges** | same |
| VITL | `R2_NEEDED` | 2026-10-07 | the page = `9b9228bc` — **values held** | R1 — **diverges** | same, plus the open ruling (STATE row 32 (11)) |

- AORT's, CNXC's and VITL's decision date is the operator's restore instruction (2026-10-07). Their
  `source_ref` states the July re-tag commit and that it was written "pending the analyst". They
  carry no `machine_recipe_at_decision`, because no record says what the anchor writer read that day.
- **VITL's values stay HELD** (STATE row 32 (11)): its `shares_outstanding` and
  `dilutive_increment` stay as committed, and its anchor carries NO machine reason until they land.
  Its hand reason has no marker, so no guard could tell it from a machine reason. Left in `reason`,
  it would have been replaced the day the machine came to agree, which is the review's finding 2.
  Recording it in the block now changes no value and makes no ruling. The operator's open question,
  revise or keep the reason, is answered by `vinci anchor-retag` with the revised words, then
  `anchor-backfill` lands the values.

**WHY.** Operator ruling 2026-10-22: "keep my reasons in their own block". There were four
erasures on two names:
- AMZN's R4 re-tag reason was erased by a re-assembly (#700), by the backfill (#752) and in #762,
  and restored by hand each time.
- UBER's was erased by its re-assembly on fresh CIQ (#705) and never restored.

There were two causes. The shared rule kept a hand reason only while the machine DISAGREED with
the hand recipe, so a reason was lost exactly when the machine came to agree. And assembly's guard
wrote the fresh anchor whenever the recipes matched. A field the machine rewrites on every build
cannot also hold the human's words. Practice outside the repo points the same way:
- model-risk guidance (Federal Reserve SR 11-7) asks that overrides of a model's output be
  analysed and documented;
- CFA Standard V(C) requires the records that support an investment action to be kept.

Both are impossible while the override and its reason live in the model's own output field. The
split also serves the fund's own accounting. The ledger already separates the machine's proposal
from the human's disposition, and the recipe now has the same two layers.

**HOW VERIFIED.**
- **The real erasures, replayed through the write paths and read back from disk** (fixture
  `tests/fixtures/operator_decision_erasures.json`, frozen from git):
  - AMZN `58dd1ef6`→`cb31a302` and UBER `58dd1ef6`→`91467746` went through `_write`, and through
    `anchor-backfill` run AS A COMMAND with only EDGAR stubbed (its machine read is the real
    rebuilt block). The decision is kept verbatim, and the machine's reason refreshes beside it.
  - GOOGL's 09-18 R1 rebuild (#631) against its decided R3: the decision stands, the divergence is
    printed first, and no caveat is added.
  - GOOGL's pre-migration block (the reason opens "OPERATOR RE-TAG", no block) is REFUSED, and
    nothing is written. So is a GOOGL page carrying conflict markers, a JSON non-object, or an
    empty file.
- **A real, unstubbed `anchor-backfill` on live EDGAR over the five pages migrated first:** 0
  changed, every artifact byte-identical, three divergences reported (GOOGL, AORT, CNXC). That is
  the write that erased AMZN's reason in #752. VITL was not run through it, because a backfill
  lands its held values by design.
- **Migration diffs.** On each of the six pages only `anchor` moved (`operator_decision`,
  `machine_recipe_hint`, and `reason` except on UBER, whose reason was already the machine's), plus
  one `layer_refreshes` row (`anchor-retag`). Each `frontend/dossiers` mirror is identical to its
  source.
- **Completeness.** Before VITL's migration, a dry-run backfill over all 27 pages found one undecided
  page whose recipe the machine does not reproduce: VITL. No committed reason carries the
  "OPERATOR RE-TAG" mark.
  - The same dry-run would also move FUBO's, LLY's, MVST's and NFLX's anchors. That is value
    drift, unrelated to this change, and nothing was written.
- **Mutation.** 31 mutants of this change, 31 killed. They span the rule, the assembly guard, the
  write guard and its fail-loud reader, the refresh guard, the md and web renderers (the
  placeholder twin list included), the CLI and the serializer.
  - Two survived the first battery. One retire-with-held-values pin hit an earlier refusal; the
    other was a strip that the missing-field check repeated. Both pins were corrected and re-run
    killed.
- **Previews.**
  - Web, collapsed and expanded, at 1280 and 500 wide: GOOGL (divergent), AMZN (agreeing) and VITL
    (held).
  - A CONSTRUCTED AMZN copy whose machine hint is `unknown` shows the gap line.
  - The full PDF export prints the `source_ref` that is collapsed on screen.
- **Suite.** The full offline suite on this branch: counts in the PR.

**BOUNDARY.**
- The corpus is the 27 committed dossier pages on `fix/operator-decision`, off main `5969a48f`,
  2026-10-22.
- "Hand re-tags on record" means the six named by
  `2026-10-07-four-recipe-re-tags-restored.md` and `2026-10-09-amzn-uber-re-tagged-r4.md`.
- The completeness check is the dry-run backfill's DIVERGES/PRESERVED output on all 27 pages,
  2026-10-22, before VITL's migration, plus the marker scan.
- The mutation count covers mutants of this PR's code only. It ran against six test files
  (`test_operator_decision`, `test_rebuild_keeps_committed_recipe`, `test_r4_machine_proposal`,
  `test_anchor_write_paths`, `test_valuation_basis`, `test_anchor`).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Fail-loud refusals.** A page whose reason opens "OPERATOR RE-TAG" with no block is refused by
  every writer until it is migrated; none remains. A committed page that is not readable JSON is
  refused by every writer until it is repaired. Both are by design.
- **The guard cannot see an UNMARKED hand edit of `reason`.** Text is all it has, and a hand reason
  without the marker reads like a machine's. No such reason remains on the corpus, since VITL was
  the last one. Every decision goes through `anchor-retag`. Falsifier: an undecided page whose hand
  reason a machine write replaces.
- **A decision never follows the machine.** GOOGL, AORT, CNXC and VITL read R1 and keep their
  decided recipes until the operator re-decides or retires them, which by the ruling is the point.
  AORT's July reason still quotes a 2.72% median, against 3.87% today
  (`2026-10-07-four-recipe-re-tags-restored.md`). The block keeps the words; it does not re-check
  them.
- **VITL's machine recipe is today's read on values its page does not show.** The recipe is
  recorded; the reason, which would cite numbers, is not.
- **The refresh guard refuses nothing today.** Its top-level seam cannot set the anchor
  (`_TOP_LEVEL_REFRESHABLE`). The guard is there so a seam opened later says so, and a test opens
  the seam to prove it fires.

## Review of #780 (`/code-review high`, 2026-10-22)

| # | finding | disposition |
|---|---|---|
| 1 | the guard failed OPEN on an unreadable committed page | FIXED — `committed_anchor_block` refuses; pinned on conflict markers, a non-object, an empty file |
| 2 | an unmarked hand re-tag (VITL) is invisible to the guard | FIXED for the corpus — VITL migrated with `--values-held`; the general limit is accepted above, with its falsifier |
| 3 | `refresh_dossier` bypassed the guard | FIXED — guarded; pinned by opening the seam |
| 4 | a placeholder machine hint read as a divergence | FIXED — a gap, in the rule's note and both renderers; the web twin's list is pinned to Python's |
| 5 | `decided_on` unvalidated, read on UTC's calendar | FIXED — ISO or refused, local calendar, never in the future |
| 6 | whitespace passed the missing-field check | FIXED — stripped once, before every check |
| 7 | an unguarded re-render after the JSON write | FIXED — reported, and the command fails |
| 8 | the decidable recipes hard-coded as strings | FIXED — read off their constants; a stated machine read must be a recipe |
| 9 | dead code and a duplicated note | PARTIAL — the assembly short-circuit is gone and the note is one helper; the rule's branch for a `new` that already carries a decision is KEPT, because it makes the rule idempotent, which the corpus negative (every page rewritten over itself) pins |
| 10 | `write_dossier` re-parses the page | PARTIAL — the retag comparison dumps once; the guard still reads the bytes ON DISK at write time, because a caller's copy can be stale and the guard exists to see what the write replaces |

STATE: row 27's item (6) is removed (closed here), row 10's AMZN-reason item is ruled and built,
and row 32 (11) records that VITL's reason is in its block with its values still held.
