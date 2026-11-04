---
id: 2026-11-04-guidance-quote-cut
status: shipped
date: 2026-11-04
prs: [907]
supersedes:
superseded-by:
---

# The drawdown outlook quote says where it stops: all four committed quotes ended mid-word, printed as verbatim, and now carry a mark

**WHAT.** `mechanical._extract_revised_guidance` quotes a WINDOW of the drawdown 8-K's Exhibit 99.1:
800 raw characters from the outlook heading (`_GUIDANCE_WINDOW`), whitespace collapsed after the cut.
`drawdown_cause.revised_guidance` stored that window and both renderers printed it as the verbatim
outlook, with nothing saying the filing goes on. The extractor now also records whether any text
follows the window (`_OutlookWindow.cut`). `_revised_guidance` returns it beside the quote, and
#906's reader `_read_gaps` → `_GapRead` carries it into the new `revised_guidance_cut`, both on
`DrawdownCause` (the rolling window) and on each dated part `DrawdownWindow`
(`drawdown_cause.anchor.at_anchor` / `.since`, #906, merged into this branch at `05b2529b`). Each
model writes the field only when it is set (its `_absent_not_null` serializer). Both renderers
(`render._cut_mark`, dossier.js `cutMark`) mark the quote where it stops, on the current window's
fact line and on a dated part's "outlook then" line:

- `true` → `… (quote cut — the release continues in the filing)`;
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
- **#906's merge.** After merging main at `05b2529b`, the $0 re-render over all 27 committed
  pages moved nothing: no committed page yet carries `drawdown_cause.anchor`, and every committed
  `dossier.md` already equals a fresh render. The dated-part mark is pinned on #906's own
  real-shape fixture `tests/fixtures/prespend/2026-11-04/SMPL-mechanical-anchored.json`: SMPL's
  $0 build, whose April quote, ending "near-ter", sits in `at_anchor` and whose rolling window
  holds none. It is also pinned on a build from #906's real-text 8-K fixtures.
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
  - The dated part, built by `_drawdown_cause` from #906's real-text fixtures: the at-underwrite
    quote records `cut` true and writes the key. The since part holds no quote and writes none.
    Built at 2026-08-14 with no anchor, the rolling window carries the quote with `cut` true.
  - #906's anchored fixture, serialised before the field, round-trips with no key.
  - E2E on both twins: the at-underwrite "outlook then" line prints the possibly-cut mark as
    built, the cut mark once recorded, and nothing for a quote the release ended inside.
- **Mutations (17 of 17 caught by `tests/test_guidance_cut_mark.py`):**
  - Python renderer: no mark; marks a not-cut quote; treats a pre-field page as cut.
  - JS renderer: no mark; marks a not-cut quote; its mark drifts from the Python twin.
  - Extractor: `cut` read from the raw length, so trailing whitespace counts; always cut; never
    cut.
  - The reader drops `cut`.
  - `_read_gaps` drops it; `DrawdownWindow` is built without it; `DrawdownCause` is built
    without it.
  - The at-anchor line is unmarked, in Python and in JS.
  - `DrawdownCause` writes the field as null; `DrawdownWindow` writes it as null.
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
- On a page built with the field, the synthesis brief sees it too, because `drawdown_cause` goes
  into the facts dump raw. No prompt text was changed.
- **Not done here (review round 0, reported, not fixed):**
  - On a page built before the field, the model still reads the cut quote with no mark:
    `synthesis._mark_drawdown_guidance` prepends only a vintage mark.
  - Two readers parse figures out of the quote without reading `cut`:
    `_pe_reconciliation` (`_ADJ_EPS`) and the reader near `mechanical.py:1849`. A window ending
    inside a range ("$1.19 to $1.") could hand them a figure the filing never stated.
  Each would change what a page computes or what the model is given, so each is its own build.
- The cut mark says "the release continues", not "the outlook continues". `cut` only knows that
  text follows the window, and a 99.1 always runs on past its outlook into tables and boilerplate.
- #906 merged first (`05b2529b`) and is merged into this branch. The flag reaches its dated parts
  and the "outlook then" line is marked. A page rebuilt after this lands records the dated part's
  `cut`. Until then an anchored page shows the possibly-cut mark there, as SMPL's coming rebuild
  will if it is built on code without this branch.
