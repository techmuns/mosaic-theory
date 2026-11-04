---
id: 2026-11-04-guidance-quote-cut
status: shipped
date: 2026-11-04
prs: []
supersedes:
superseded-by:
---

# The drawdown outlook quote says where it stops: all four committed quotes ended mid-word, printed as verbatim, and now carry a mark

**WHAT.** `mechanical._extract_revised_guidance` quotes a WINDOW of the drawdown 8-K's Exhibit 99.1:
800 raw characters from the outlook heading (`_GUIDANCE_WINDOW`), whitespace collapsed after the cut.
`drawdown_cause.revised_guidance` stored that window and both renderers printed it as the verbatim
outlook, with nothing saying the filing goes on. The extractor now also records whether any text
follows the window (`_OutlookWindow.cut`, threaded by `_revised_guidance` into the new
`DrawdownCause.revised_guidance_cut`, ABSENT when None via `DROP_WHEN_NONE`). Both renderers
(`render._guidance_fact`, dossier.js `guidanceFact`) mark the quote where it stops:

- `true` → `… (quote cut — the outlook continues in the filing)`;
- `false` (the release ended inside the window) → no mark;
- absent on a PRESENT quote (a page built before the field, every committed page today) →
  `… (quote may be cut — see the filing)`.

The quote itself is unchanged. It is never extended or completed. Version row
`2026-11-04.guidance-quote-cut` (both twins); pins re-taken.

**WHY.** CLAUDE.md: A TRUNCATED OUTPUT PRINTS ITS OWN TRUNCATION. The coordinating session found
SMPL's "…but in the near-ter" while reviewing #906's render preview. It was already on main, so
#906 did not cause it.

Structured, not render-only, because the stored quote cannot tell a cut window from a whole one.
Whitespace collapses after the cut, so VITL's cut quote is 799 characters, not 800. A release that
ends inside the window would also give a short quote. A length test on the value would be a guess,
and "fail loud, never fabricate" rules that out. For a page built before the field, the page cannot
know either way. Its quote came from the same window, so it is marked as possibly cut rather than
left silent or guessed definite.

Committed `dossier.json` files are NOT backfilled. Each of the four was shown cut at $0 (below).
Writing the flag in would be a mechanical-layer change on a page outside its assembly. The hedged
mark is true as it stands, and a re-assembly turns it definite.

**HOW VERIFIED.**
- **Live corpus first.** A $0 probe re-ran `_extract_revised_guidance` on each committed quote's
  Ex-99.1, read from the SEC cache (`vinci.sec.build_sec_http`) at the URL in its `source_ref`.
  All four reproduce the committed quote byte for byte, and all four are cut:

  | Page | Anchor at char | Release length | Cut |
  |---|---|---|---|
  | BRBR | 178 | 36,138 | yes |
  | SMPL | 764 | 32,948 | yes |
  | VITL | 7,195 | 26,544 | yes |
  | VRRM | 2,017 | 13,176 | yes |
- **Re-render at $0.** `refresh._rerender_only` re-rendered every committed page from its stored
  JSON (`dossier.json` untouched), then `mirror_to_frontend`. Exactly BRBR, SMPL, VITL and VRRM
  moved, by one line each: the quote line gains the mark before its cite. No other committed file
  moved.
- **Pins** (`tests/test_guidance_cut_mark.py`):
  - The extractor: positive (cut) and negative (the release ends inside the window, trailing
    whitespace included).
  - The reader threads `cut`, and an UNKNOWN quote carries None.
  - The field is absent on a pre-field page and written when set.
  - E2E on the living corpus: every PRESENT quote prints the mark its field dictates, directly
    after the stored quote. Every page without a quote prints neither mark.
  - E2E positive on both twins: SMPL's real JSON with `cut` true prints the cut mark.
  - E2E negative on both twins: SMPL's real quote cut to 120 characters with `cut` false prints no
    mark.
  - The web twin on the committed SMPL page prints the possibly-cut mark exactly once.
  - The two marks are declared identically in Python and JS.
- **Mutations (11 of 11 caught by `tests/test_guidance_cut_mark.py`):**
  - Python renderer: no mark; marks a not-cut quote; treats a pre-field page as cut.
  - JS renderer: no mark; marks a not-cut quote; its mark drifts from the Python twin.
  - Extractor: `cut` read from the raw length, so trailing whitespace counts; always cut; never
    cut.
  - The reader drops `cut`.
  - The field is unregistered in `DROP_WHEN_NONE`, so it is written as null.
- **Render preview** from committed JSON, `docs/dossier/guidance-quote-cut-2026-11-04/screenshots/`:
  - SMPL Analysis, collapsed;
  - SMPL Analysis, every `<details>` force-open (the fact is outside every `<details>`, so print
    shows it the same way);
  - the cut mark as a recorded `true` renders it.

  No console errors.

**BOUNDARY.**
- "All four committed quotes": the 27 `data/dossiers/*/dossier.json` at main `481e82f7`
  (2026-11-04), filtered to `mechanical.drawdown_cause.revised_guidance.status == "present"`. That
  gives 4 pages; the other 23 hold no quote.
- The probe's anchors and lengths are characters of `html_to_text` output, read from the SEC cache
  in this worktree on 2026-11-04.
- "Exactly four pages moved": `data/dossiers/*/dossier.md` and `frontend/dossiers/*.md`, re-rendered
  at this branch's head.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- Until each of the four names is re-assembled, its page says the quote "may be cut" where the
  probe showed it is. Falsifier: a re-assembled page with a PRESENT quote and no
  `revised_guidance_cut` key, which would mean the field is not reaching the page.
- The synthesis brief now sees the flag too, because `drawdown_cause` goes into the facts dump raw.
  No prompt text was changed.
- #906 (open) adds `drawdown_cause.anchor.at_anchor`, a `DrawdownWindow` holding its own copy of
  `revised_guidance`, printed in its render as "outlook then". If #906 merges first, this branch
  merges main and threads the flag into that copy. If this merges first, #906 owes the same.
