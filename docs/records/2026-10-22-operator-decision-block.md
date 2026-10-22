---
id:
status: shipped
date: 2026-10-22
prs: [780]
supersedes:
superseded-by:
---

# An operator's recipe decision has its own block — the machine's writes copy it and never erase it; five pages migrated, VITL waits on its ruling

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
  and web), so assembly adds no caveat for a decided page.
- **Every write is guarded.** `write_dossier` refuses a write that DROPS or ALTERS a committed
  decision. Only `vinci anchor-retag` may change one. It also refuses an anchor whose `reason` opens
  "OPERATOR RE-TAG" with no block: the old way of re-tagging, which the next machine write erased.
- **`vinci anchor-retag`** is the one writer of a decision.
  - It records `--recipe` and `--reason-file` (verbatim), with `--decided-by`, `--decided-on` and
    `--source-ref`; `--retire` removes a decision.
  - Every computed value stays as committed.
  - It REFUSES when the machine's read today moves a committed value, because the machine's reason
    would then describe numbers the page does not show.
  - A BACKDATED decision records no machine read unless `--machine-at-decision` names one. Today's
    read is never filed as the read at the decision.
- **On the page.** The block leads with the decided recipe and who decided it, when. The divergence
  flag comes next, then the operator's words as a quote, then the source in an on-demand
  `<details>`, which prints expanded. The machine's reason prints beneath, labelled "The machine's
  read:".

**Migrated (each reason verbatim from git):**

| name | decision | decided | reason taken from | machine reads | source_ref |
|---|---|---|---|---|---|
| AMZN | `R4_forward_ev_ebit` | 2026-10-09 | the page (restored #701/#752) = `22320fca` | R4 (agrees) | `2026-10-09-amzn-uber-re-tagged-r4.md` (#698) |
| UBER | `R4_forward_ev_ebit` | 2026-10-09 | `58dd1ef6` — **erased by #705, restored here** | R4 (agrees) | same |
| GOOGL | `R3_forward_pe` | 2026-09-01 | the page = `c005449f` | R1 — **diverges** | `2026-09-01-r3-reaches-the-create-path.md` (#557) |
| AORT | `R2_NEEDED` | 2026-10-07 | the page = `feca6b93` | R1 — **diverges** | `2026-10-07-four-recipe-re-tags-restored.md` (#671) |
| CNXC | `R1_NOT_ROBUST` | 2026-10-07 | the page = `9b9228bc` | R1 — **diverges** | same |

- AORT's and CNXC's decision date is the operator's restore instruction (2026-10-07). Their
  `source_ref` states the July re-tag commit and that it was written "pending the analyst". They
  carry no `machine_recipe_at_decision`, because no record says what the anchor writer read that day.
- **VITL is NOT migrated.** Its page is held at main until the operator rules on its re-tag reason
  (STATE row 32 (11)). `anchor-retag` refuses it as it should: the machine's read today moves its
  held `shares_outstanding` and `dilutive_increment`. It keeps the legacy rule meanwhile, which
  preserves its diverging recipe and its reason. Once the ruling is made, land the values
  (`anchor-backfill`), then record the kept or revised reason with `vinci anchor-retag`.

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
    nothing is written.
- **A real, unstubbed `anchor-backfill` on live EDGAR over the five decided pages:** 0 changed,
  every artifact byte-identical, three divergences reported (GOOGL, AORT, CNXC). That is the write
  that erased AMZN's reason in #752.
- **Migration diffs.** On each page only `anchor` moved (`operator_decision`,
  `machine_recipe_hint`, and `reason` except on UBER, whose reason was already the machine's), plus
  one `layer_refreshes` row (`anchor-retag`). Each `frontend/dossiers` mirror is identical to its
  source.
- **Completeness.** A dry-run backfill over all 27 pages finds one undecided page whose recipe the
  machine does not reproduce: VITL. No committed reason carries the "OPERATOR RE-TAG" mark.
  - The same dry-run would also move FUBO's, LLY's, MVST's and NFLX's anchors. That is value
    drift, unrelated to this change, and nothing was written.
- **Mutation.** 16 mutants of this change, 16 killed. They span the rule, the assembly guard, the
  write guard, the md and web renderers, the CLI and the serializer.
- **Previews.** Web, collapsed and expanded, at 1280 and 500 wide: GOOGL (divergent) and AMZN
  (agreeing). The full PDF export prints the `source_ref` that is collapsed on screen.
- **Suite.** The full offline suite on this branch: counts in the PR.

**BOUNDARY.**
- The corpus is the 27 committed dossier pages on `fix/operator-decision`, off main `5969a48f`,
  2026-10-22.
- "Hand re-tags on record" means the six named by
  `2026-10-07-four-recipe-re-tags-restored.md` and `2026-10-09-amzn-uber-re-tagged-r4.md`.
- The completeness check is the dry-run backfill's DIVERGES/PRESERVED output on all 27 pages,
  2026-10-22, plus the marker scan.
- The mutation count covers mutants of this PR's code only. It ran against six test files
  (`test_operator_decision`, `test_rebuild_keeps_committed_recipe`, `test_r4_machine_proposal`,
  `test_anchor_write_paths`, `test_valuation_basis`, `test_anchor`).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A pre-migration page cannot be rebuilt.** A page whose reason opens "OPERATOR RE-TAG" with no
  block is refused by every writer until it is migrated. None remains on the corpus; it fails loud
  by design.
- **An unmarked hand reason on an undecided page still rides the legacy rule.** It is kept only
  while the recipes diverge. VITL is the one such page. Every new decision goes through
  `anchor-retag`, which the guard enforces for marked text only. Falsifier: an undecided page whose
  hand reason a machine write replaces.
- **A decision never follows the machine.** GOOGL, AORT and CNXC read R1 and keep their decided
  recipes until the operator re-decides or retires them, which by the ruling is the point. AORT's
  July reason still quotes a 2.72% median, against 3.87% today
  (`2026-10-07-four-recipe-re-tags-restored.md`). The block keeps the words; it does not re-check
  them.
- The refresh path (`refresh_dossier`) needs no guard. Its top-level seam cannot set the anchor
  (`_TOP_LEVEL_REFRESHABLE`), so a decided page passes through it unchanged.

STATE: row 27's item (6) is removed (closed here), and row 10's AMZN-reason item is ruled and
built.
