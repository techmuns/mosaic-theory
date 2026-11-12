---
id: 2026-11-11-fix2-rg-d21-residual-a-points-decline-reads-negative
status: recorded
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# Fix request 2, RG-D21 residual: a decline stated after a points unit reads negative — "a 27 percentage point decline" is −27, and +27 for it is refused

**WHAT.** This closes the residual of `docs/records/2026-11-11-fix2-rg-d21-a-stated-decline-reads-negative.md`
(#987). It is one regex in `vinci/theme_intelligence/verify.py`: `_PCT_UNIT` becomes
`_RATE_UNIT`, the unit `_decline_beside` steps over between a figure and the decline word after
it.
- It stepped over a percent only (`%`, "percent", "per cent", "pct"). Now it also steps over a
  rate's points: pp, ppt(s), percentage point(s) ("percentage-point" too), bp(s) and basis
  point(s) ("basis-point" too), and bare pt(s)/point(s) ("2.5 pts", "a 300 point decline").
- The unit may be hyphenated onto the figure: "a 40-basis-point decline", "a 27-percentage-point
  drop", "a 27-percent drop". The compound-adjective form is common in rate prose, and without it
  the residual stayed open in that form (found by this PR's own `/code-review`, round 0).
- It matches case-insensitively, as the decline words beside it always have.
- A scale word ("million") is not added. The coordinator's negative pin keeps "27 million
  decline" reading as it does today.

**WHY.**
- **Codex on #987** (comment 4535189339): with the value text "27" and its unit stored apart
  ("percentage points"), the quote "Margins posted a 27 percentage point decline" accepted +27
  and refused −27. That is the same silent wrong value RG-D21 names, in another unit. The decline
  word stood past a unit the check could not step over.
- #987's review round was capped, so the coordinator handed it back as a residual: RG-D21 is not
  closed until it lands.

**HOW VERIFIED.**
- **Pins, failing first on main `6d9907d7`** (`tests/test_theme_intelligence_number_sign.py`): 28
  of the new cases fail there.
  - `test_a_points_decline_read_as_positive_is_refused` (14) and
    `test_a_points_decline_read_as_negative_passes` (14).
  - Each unit is covered: percentage point, "percentage-point", "percentage points", 2.5pp and
    "2.5 pp", 40 bps and 40bp, basis point, and "basis points lower".
  - Review round 0 added 5 cases to each (14 apiece, 28 in all): "40-basis-point",
    "27-percentage-point", "27-percent" (hyphenated onto the figure), "2.5 pts" and "300 point".
    Each failed at the pre-review head (+ passed, − refused) and passes now.
- **Negative pins, passing at base and head:**
  - **"27 million decline" stays as it reads today.** With "27 million" as the value text, +27M
    is refused and −27M passes.
  - **A points rise or level is unchanged:** "up more than 100 basis points", "a 40 bps rise",
    "by roughly 6 percentage points".
  - **The registry's one points figure worded as a drop still passes:** C-7f13888d27d72f, read
    as −8 ("drops as low as –6 to –8 percentage points").
- **Cross-setup, deterministic, $0.** Every claim carrying a figure in the desk's registry went
  through `_number_check` at base and at head, with the same script #987 used:
  - **0 of 696 verdicts move** (re-run after the review round's widening: still 0 against base
    and 0 against the pre-review head);
  - **0 `number_passes` flips.**
- **The corpus.**
  - **16 of the 696 name a points unit** in their value text, unit or quote.
  - **None states a decline beside its points figure** in either place the check reads. That is
    why nothing moves.
  - **One carries a decline word anywhere in its quote:** C-7f13888d27d72f, already negative.
- **The suite:** see the PR.

**BOUNDARY.**
- **Claims:** the registry at `theme-intelligence-state` ea8fb4a6 (`state status`: local and
  branch in step). 1,190 claims, of which 696 carry a value or a value text.
- **"Names a points unit":** the regex `pp|ppts?|percentage[-\s]points?|bps?|basis[-\s]points?`
  as a whole word, anywhere in the value text, unit or quote (measured before the review round
  added bare pts/points; a scan of quotes for a figure, an optional hyphen, any of these units or
  bare pt(s)/point(s), then a decline word found 0 claims).
- **Base:** main `6d9907d7`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0.
- **No stored claim and no desk render moves.**
- **Left as it reads, per the coordinator's pin: a scale word between the figure and the decline
  word.**
  - With the value text "27", a unit "USD millions" and the quote "a 27 million decline", +27
    still passes and −27 is refused.
  - With "27 million" in the value text (the pinned shape), both read right.
  - The registry has **0** claims whose quote states "<n> million/billion/… decline".
  - Closing it means stepping over scale words, which changes the pinned shape's path: the
    coordinator's call.
