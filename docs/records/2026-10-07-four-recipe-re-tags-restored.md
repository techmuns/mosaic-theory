---
id: 2026-10-07-four-recipe-re-tags-restored
status: shipped
date: 2026-10-07
prs: [671]
supersedes:
superseded-by:
---

# The four recipe re-tags a re-assembly erased are back — GOOGL's and AORT's records pass their gate again

**WHAT.** The `recipe_hint` and `reason` of four committed anchors are restored to the hand re-tags
that the next re-assembly erased (history in `2026-10-07-a-rebuild-keeps-the-committed-recipe.md`).
Each block is verbatim from git; every computed value on the anchor is today's. The JSON write is
byte-preserving (`replace_anchor_block`), the page is re-rendered from the stored record
(`_rerender_only`), and the frontend is mirrored. No LLM and no re-assembly.

| name | restored to | erased since | block taken from |
|---|---|---|---|
| GOOGL | `R3_forward_pe` (reason opens "OPERATOR RE-TAG 2026-09-01") | 09-18 (#631) | `c005449f` |
| AORT | `R2_NEEDED` | 07-23 | `b2a5f5b5` (set in `feca6b93`) |
| CNXC | `R1_NOT_ROBUST` | 07-22 | `b2a5f5b5` (set in `9b9228bc`) |
| VITL | `R2_NEEDED` | 07-22 | `b2a5f5b5` (set in `9b9228bc`) |

**WHY.** Operator instruction, 2026-10-07: restore the four erased recipes. That comes after #670
made a re-assembly keep a committed recipe. **#670 must merge first**, or the next rebuild erases
them again.

**WHAT IT MOVES, measured on this branch.** The scenario gate (`check_tier_agreement`) now ACCEPTS
GOOGL's committed `R3_forward_pe` record and AORT's committed `R2_terminal_margin` record. Both were
refused before as "disagrees". CNXC and VITL have no scenario record.

**DO THE JULY REASONS STILL HOLD?** Read with the repo's own propose-only tagger on today's
committed records:
- **CNXC** — the tagger proposes `R1_NOT_ROBUST` today. Net debt is 138% of anchor equity, against
  139% at the re-tag.
- **VITL** — the tagger proposes `R2_NEEDED` today. The trailing multiple's band is incoherent, and
  the margin runs 2.3% → 10.1% from the earliest three years to the latest three.
- **AORT** — the tagger proposes R1, reading CIQ EBIT (6.5% → 7.5%), which excludes unusual items.
  The re-tag's basis is GAAP operating margin, whose 10-FY median is 3.87% today, unchanged since
  July. That is a basis difference, not a reversal. AORT's committed scenario record is R2, and the
  next rebuild prints the disagreement as a caveat (#670).
- **GOOGL** — `R3_forward_pe` is an operator judgment the tagger cannot propose: an equity basis,
  ratified 2026-09-10.

The reasons stay as written then. They are dated by their records, not restated here.

**HOW VERIFIED.**
- Each `dossier.json` diff is exactly two lines (`recipe_hint`, `reason`). The bytes before the
  anchor block were asserted unchanged, and every mirrored page is byte-identical to its source.
- The gate checks above, run on the restored files.
- `tests/test_propose.py`'s corpus pins, made state-robust in #670, pass on the restored corpus.
- #670's 26-name negative passes (no rebuild disagrees with itself).
- Full offline suite on this branch, which is #670 plus this restore: counts in the PR.

**BOUNDARY.** Four names. Committed dossiers on this branch, stacked on #670 @`8ffd527a` (main
@`4ab4de36`). The tagger figures are its own printed signals, 2026-10-07.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Merge order is load-bearing:** #670, then this.
- **The `applicable` coupling (§5.0 row 10) still applies.** GOOGL's R3 record is refused whenever
  a build finds R1 inputs incomplete, which happened on 3 of its 8 committed anchors.
- **AORT's reason quotes a "corrected 5yr median 2.72%" from July**; today's 10-FY median is 3.87%.
  It is not restated, because the reason is the operator's dated judgment.

STATE: row 32's item (8), opened in #670, is removed — closed here.
