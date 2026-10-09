---
id:
status: shipped
date: 2026-10-09
prs: [701]
supersedes:
superseded-by:
---

# AMZN's anchor carries the operator's re-tag reason again — restored by hand, and erased again by the next re-assembly unless provenance is recorded

**WHAT.** AMZN's `anchor.reason` is restored to the operator's 2026-10-09 re-tag text, verbatim
from the #698 page ("OPERATOR RE-TAG 2026-10-09. R3 -> R4: EV/NTM EBIT, an ENTERPRISE basis. …").
#700's re-assembly had replaced it with the machine's own R4 reason.
- **One field, byte-preserving.** `replace_anchor_block` swapped only the anchor block. The script
  asserted that `reason` is the only anchor key that moved, that every other top-level key is
  equal, and that the 654,947 bytes before the anchor are identical.
- **The page was re-rendered from the stored record** (`_rerender_only`), and the mirror ran once.
- **Nothing else:** no LLM, no re-assembly, no code. A hand edit isn't a code writer, so no
  `layer_refreshes` entry is added (as with #671 and #698).

**WHY.** Operator instruction, 2026-10-09: "restore my re-tag reason". #700 flagged the
replacement and left it to the operator.

**⚠ THE NEXT RE-ASSEMBLY WILL ERASE IT AGAIN.** Both anchor writers apply `preserve_operator_tag`.
Under an UNCHANGED recipe it takes the fresh reason (`anchor.py`, the review of #670).
- **The premise of that rule** was that no operator note under an unchanged recipe appears in the
  committed history, while NFLX and V carried stale machine refusals.
- **AMZN is now the first counterexample.** The operator's tag and the machine's proposal agree,
  so the recipe is "unchanged" and the operator's reason loses.
- **The block records no provenance,** so the rule cannot tell the two apart. That limit is
  already named in the function's docstring.
- **Not fixed here.** Holding the operator's text across rebuilds needs provenance on the block,
  for example a marker or a field naming who wrote the reason. That is a code change to both
  writers and is the operator's call.
- **Until then, the next AMZN rebuild** (expected after the Q3 report) will need this restore
  repeated, or the machine's reason accepted.

**HOW VERIFIED.**
- **The edit script's assertions,** run first as a dry run on #700's page and then for real: only
  `anchor.reason` moved, the other top-level keys are equal, and the bytes before the anchor are
  identical.
- **The restored text is byte-equal** to the #698 page's `anchor.reason` (main @9dfede17).
- **`dossier.md` moved one line,** the reason under the screening context. The mirror is
  byte-identical to the page.
- **Suite:** `pytest -m "not network"` on the committed artifacts. Counts are in the PR.

**BOUNDARY.**
- **Scope:** one field on one page, AMZN, 2026-10-09.
- **Source of the text:** `data/dossiers/AMZN/dossier.json` at main @9dfede17 (#699's merge,
  before #700).
