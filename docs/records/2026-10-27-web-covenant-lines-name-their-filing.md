---
status: shipped
date: 2026-10-27
prs: [814]
supersedes:
superseded-by:
---

# The web names the filing each covenant value was read from, as the Markdown has since #482: `covenantSourceSuffix` read Python's field names off a JS object, so K1b's "— per an 8-K filed …" was blank on every web and PDF covenant line from the day it shipped

**WHAT.** STATE.md §5.0 row 32 item (19) closes.

- **The fix**, two lines in `frontend/views/shared/dossier.js::covenantSourceSuffix`. It now reads
  `g.baseRef` and `g.amendedBy`, the fields `governingTerms` returns. It had read `g.base_ref` and
  `g.amended_by`, which do not exist on that object, so `base` was always null, `amended` always
  empty, and the function always returned "".
- **The page.** Every curated covenant line in the main body now ends as its Markdown line does:
  ` — per an 8-K filed <date>[, amended <date>]`. The main body prints in every scope, so the PDF
  carries it too.
  - A withheld (refused-newer, #812) line takes no suffix, on either surface. Its lead already
    names its dates.
  - An accession the pointer rows do not date prints nothing, never a guessed date. That is
    unchanged from #482's contract, and is now pinned on the web.
- **Nothing else.** The Python side, the committed JSON and the committed Markdown are untouched.
  No page is re-rendered: the web renders from `dossier.json` at view time.

**WHY.**

*The defect.* #482 (`827a6c81`, 2026-08-20) shipped K1b in both languages. It exists so that a
stale read is visible beside the panel. EPAM's digest read "Expiration Date: October 21, 2026"
from a 2017 8-K, while the capital-structure line said Due 2030, and nothing on the page said
which filing the clause came from.

The JS mirror was written against the Python names. When it shipped, `governingTerms` had already
returned `baseRef` and `amendedBy` for six weeks (RC-1.5d, `32b3a869`, 2026-07-07). So the web
never printed a date at all, and the EPAM line the build was written for still read undated on
the web and in every PDF.

*Why nothing caught it.* Every K1b pin read the Python helper, `_covenant_summary_lines` or the
Markdown. The one artifact pin, `test_the_committed_fleet_dates_its_covenant_values`, renders the
Markdown digest. A JS mirror with no JS-side pin is the shape that let it stay blank for 68 days.

*Found by* #812's build, which compared the web's main-body covenant block with the Markdown line
for line. That build recorded it as row 32 item (19) rather than fix it in scope. The diagnosis was
re-verified independently, on main `18d19bfb` and on #812's head, before this build started.

*Why the smallest fix.* The brief asked for the field names `governingTerms` actually returns. Any
other route — renaming the JS object's keys, or reading both spellings — would touch the collapse
#812 had just brought into parity with Python, or keep the wrong names alive.

**HOW VERIFIED.**

*The preview, approved by the operator before the fix was built* (2026-10-27, "Approved — build
the fix, pin it end to end with the negative case, and open the PR once #812 has merged"). Built
from committed JSON, through the production `renderDossier` under node, with the fix applied to a
scratchpad copy of `frontend/`:
- **Main body.** For EPAM, NKE, BURL and NFLX: the web today, the web after the fix, and the
  committed `dossier.md`, side by side.
- **Print state.** Each of those four full pages with every `<details>` forced open and
  `ds-print-full` on the body. The covenant block sits inside 0 `<details>` on all four.
- **Real PDFs.** Headless Brave printed each forced-open page, before and after. Dated phrases in
  the PDF text, whitespace-normalised: before 0 / 0 / 0 / 0; after 4 / 7 / 6 / 11 for
  EPAM / NKE / BURL / NFLX, equal to the re-count. `undefined` 0 and `NaN` 0 in all eight PDFs.

*The re-count* (boundary below):

| Measure | Count |
|---|---|
| Curated covenant main-body lines, on 20 of 27 pages | 146 |
| Lines dated by the Markdown | 143 |
| Withheld lines, which take no suffix by design | 3 |
| Lines dated by the web before the fix | 0 |
| Lines dated by the web after the fix | 143 |
| Web lines equal to their Markdown line, after the fix (normalised text) | 146 of 146 |

- Per page, the lines that gain a date: AMZN 11 · AORT 12 · BRBR 2 · BURL 6 · CNXC 9 · EPAM 4 ·
  FUBO 2 · IT 8 · MVST 10 · NCNO 4 · NFLX 11 · NKE 7 · PARR 9 · SMPL 4 · TGT 1 · TJX 13 · UBER 7 ·
  V 3 · WERN 8 · WLK 12.
- `undefined` and `NaN` appear 0 times in the whole rendered HTML of all 27 pages, collapsed tiers
  included, before and after.
- `render_markdown` on each page's JSON equals the committed `dossier.md`'s covenant main body on
  all 20 pages, so the Markdown side of the comparison is the committed artifact.

*Pins* (`tests/test_covenant_source_date.py`, 3 new):
- **Positive, end to end:**
  - every committed `dossier.json` goes through `render_markdown` and through the production
    `renderDossier` under node;
  - each family's covenant lines must carry the same suffix, or the same absence, in the same
    order;
  - asserted as parity, never as a date, because the pages are living artifacts;
  - the skip is scoped to the data (no committed covenant line), never to the behaviour.
- **Negative, end to end, on the real type:**
  - no committed line lacks a dated accession, so the corpus never reaches the "nothing" branch;
  - the pin takes EPAM's committed page — the case K1b exists for — and blanks its pointer rows'
    `filing_date` (the schema's own "absent");
  - its covenant lines still render on both surfaces, neither names a filing, and none reads
    `undefined` or `NaN`;
  - the same page, undamaged, dates every web line.
- **Node-free:** every field `covenantSourceSuffix` reads off `g` is a key of the object
  `governingTerms` returns. The two e2e pins skip without node, and this one catches the defect's
  own shape. GitHub's `ubuntu-latest` ships node, so the gate runs all three.

*Mutation: 6 of 6 mutants killed.* Each was applied to `dossier.js`, run against the three new
pins, then restored.
- the original bug (both snake_case names);
- amendments lost (`amended_by` only);
- the call site deleted;
- a guessed date for an undated accession;
- an undated base falling back to the accession text;
- the suffix appended to withheld lines too.

**BOUNDARY.**
- **Pages:** the 27 committed `data/dossiers/*/dossier.json` at #812's head `ee754dd8` (main
  `18d19bfb` plus #812's three commits), measured 2026-10-27. 20 of them render a curated
  `Covenants — <family>` main-body block.
- **Unit:** one curated main-body covenant line — one `<li>` on the web, one `  - **label:**` line
  in the Markdown.
- **Comparison:** text normalised (tags stripped, entities and GFM escapes undone, bold dropped,
  whitespace collapsed). Lines matched by family and position.
- **Web:** node 26 through `renderDossier(d, null)`. PDFs by headless Brave `--print-to-pdf` on a
  static page carrying `styles.css`, `ds-print-full` and every `<details>` opened. The app's
  `beforeprint` handlers do not run in that static page; they split wide tables and rename the
  file, and neither touches this line.
- **Re-taken after rebasing onto main** once #812 merged (`0fc52abd`), on 2026-10-27, with main's
  `dossier.js` as "before": the same 27 pages, the same 146 / 143 / 3 / 0 → 143, 0 mismatches, and
  the same per-page gains. Mutation re-run on the rebased tree: 6 of 6 killed. Full suite on the PR
  head: 6,862 passed, 533 skipped, 0 failed.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Every web covenant line grows by about 30 characters.** The Markdown has carried the same
  text since 2026-08-20, and the operator approved it on the preview.
- **The negative pin damages a real page in memory, not on disk.** It rests on EPAM keeping
  covenant pointer rows and a covenant main-body block. If a re-assembly drops either, the pin
  fails loudly rather than skipping, because a negative that silently loses its subject proves
  nothing.

**Incident → invariant.** A JS mirror read the Python field names and printed nothing for 68
days, while every pin read Python → an end-to-end parity pin across both surfaces on every
committed page, a negative on a real page, and a node-free field-name pin. Shipped: Y.
