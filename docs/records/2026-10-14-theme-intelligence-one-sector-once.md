---
id: 2026-10-14-theme-intelligence-one-sector-once
status: recorded
date: 2026-10-14
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — one sector shown once; the menu button that "did nothing" was a stale stylesheet

**WHAT.** Operator, 2026-10-14: "* fix the duplicate sector entry * and nav bar collapse icon
doesnt work".

1. **One sector, shown once** (`cards.distinct_sectors`). The extraction can name one sector twice
   from one sentence. The Alzheimer thesis (TH-8DDD7B2868) holds both:
   - "Diagnostics and care delivery, retirement and insurance industries" (no direction);
   - "Diagnostics and care delivery, as well as the retirement and insurance industries" (could
     benefit).

   Both quote the same span, which the source frames as "could benefit from — or need to adapt
   to". The reading page listed the sector twice: under "Could benefit" and under "direction not
   stated".
   - **The rule:**
     - two names are one sector when one's content words are all the other's, and make up at
       least two-thirds of them;
     - the one with a stated direction is kept, else the first;
     - **two that say opposite ways both stay** — a contradiction is shown, never hidden;
     - a single sector inside a list of several stays apart.
   - **Display only.** The stored version and the card's JSON keep every entry as extracted.
   - **Applied where sectors are listed:**
     - the reading page's "Who is exposed" and its exposure gate;
     - the card: its HTML rows, section 05's count and its Markdown;
     - the weekly dashboard.
   - **Not applied:** the audit view's priority trace, which quotes the factor value sealed with the
     version, verbatim.
   - **Does this select on form?** No. It is display only and not a gate. The priority rules read
     `sector_exposures` unchanged.
2. **The menu collapse button: no fault in the code.**
   - **It works when served current.** In the in-app browser, at desktop width (1280px) the rail
     goes 212px → 52px and hides its three groups, then reopens; the choice is saved. At phone
     width it folds to the brand row.
   - **It fails when the browser holds the old stylesheet:**
     - the local preview (`python -m http.server`) sends no caching header, so the browser served
       `app.js` and `styles.css` from cache **without asking the server** (0 bytes transferred, a
       file that is revalidated shows 300);
     - before the menu change (`44404035`), `styles.css` had last changed on 2026-09-10, while
       `app.js` had changed that morning, so the two could come from different versions;
     - **reproduced with the real pre-change stylesheet** (`44404035^`) and the current `app.js`:
       the click sets `data-nav="collapsed"`, the rail stays 236px with all three groups, and the
       button is the browser's plain grey default (the old stylesheet has no style for it).
   - **Fixed in the preview, not the code.** Port 8895 now runs a static server that sends
     `Cache-Control: no-cache` (a scratch script, not in the repo). A normal reload then revalidates
     both files: 304s, 300 bytes each. A browser that cached them earlier needs **one hard reload**
     (Cmd+Shift+R).
   - **Confirmed by the operator** after one hard reload, 2026-10-14: "hard reloaded, collapse
     works now".

**WHY.** A sector listed twice reads as two exposures, under two headings that disagree on
direction.

**HOW VERIFIED.**
- **Corpus before synthetic.** Over the pilot registry: 23 theses, 33 versions, 69 sector lines.
  **Two versions merge**, both true repeats:
  - TH-8DDD7B2868 v1, the pair above;
  - TH-16225B12C4 v2: "consumer-packaged goods and restaurants" into "…restaurants space", both
    could benefit.
- **What the corpus caught.** The first version merged unrelated sectors of equal size: "Treasurys"
  with "US equity", and "managed care" with "healthcare utilization". With equal sizes, picking the
  smaller and larger by length returned the same set, so the subset test compared a set with
  itself. The pair is now ordered explicitly.
- **Pin, end to end** (`tests/test_theme_intelligence_desk.py`): a hypothetical article in the
  real extraction type is rendered, then read on the reading page, the gate, the card (Markdown and
  HTML) and `dashboard.json`.
  - Positive: the pilot's pair is shown once, kept as could benefit.
  - Negative:
    - "Treasurys" and "insurance" (equal size) stay apart;
    - "insurance" inside the longer list stays apart;
    - "US equity and credit" (benefit) and "…markets" (hurt) both stay;
    - the stored version keeps all six.
  - **Mutants: 10 of 10 killed** — the equal-size bug, opposite directions merged, the two-thirds
    share, the directional entry, and each of the six call sites.
- **The real page**, republished from the pilot: "Who is exposed" lists the sector once, under
  Could benefit, and the gate names it once.
- Ruff and `mypy --strict` are clean; the offline suite result is in the PR.

**BOUNDARY.**
- "23 theses / 33 versions / 69 sector lines": every version of every thesis, retired included, in
  the pilot registry `data/theme_intelligence/v2/pilot-2026-10-12/registry.db` (the
  `theme-intelligence` worktree), read 2026-10-14 after `R-20261014T110419Z-reanalyse`. Read-only:
  the checksum is unchanged.
- The menu: the in-app browser (Chromium) against `127.0.0.1:8895` serving this worktree's
  `frontend/`. **The deployed preview was not checked:** it sits behind Cloudflare Access.
  Cloudflare Pages' documented default makes the browser revalidate on every load, which would rule
  this cause out there, but that was not verified here. If the button fails on the deployed site,
  this diagnosis does not cover it.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0 of model spend. The pilot stays at $17.8535 of $25.
- **No machine check for the stale stylesheet.** The cause is the preview server, which is not in
  the repo. The deployed site is not known to be affected.
