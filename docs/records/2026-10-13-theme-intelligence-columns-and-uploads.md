---
id: 2026-10-13-theme-intelligence-columns-and-uploads
status: recorded
date: 2026-10-13
prs: [703]
supersedes:
superseded-by:
---

# Theme intelligence — a saved paywalled preview is recorded as a preview, and the desk's crammed columns read plainly

**WHAT.**
- **An importer defect, found by dry-running the operator's three uploads** (`documents.py`,
  `parse.paywall_marker`). A paywalled page SAVED AS PDF without a paid sign-in is still its
  preview: it ends with the subscriber notice ("This post is for paid subscribers … Already a paid
  subscriber? Sign in"). The web scan has always checked for that notice; the importer did not.
  One of the two SemiAnalysis PDFs supplied on 2026-10-13 would have been recorded **read in
  full**. Now the notice makes a supplied document PARTIAL, says why, and Uploads keeps asking for
  the full post. The same marker definition serves both paths.
- **Sources** (`desk.sources_page`). Each channel's state is one plain line built from its latest
  check's structured test results ("some articles are previews or summaries of a fuller report";
  "the site refuses automated access; a known restriction"). The check's own sentences (HTTP
  codes, robots.txt, sampling counts) sit in a "What the check found" fold. The history strip
  appears only once two or more checks are stored ("1 of 1" said nothing). The newest article is
  the newest the check saw on the site or the registry holds. The three intake lines repeated on
  every row are gone: the licence rule is said once, and a channel that differs says so on its
  row ("linked reports read by the scan"). Manual-first channels link their research page.
- **Articles.** Follow-up is one action ("Supply the full report", linked to Uploads). Open items
  fold under "N items to check", with the figures-captured count inside the fold. Fixed column
  widths keep it from squeezing.
- **Uploads.**
  - A source's request lists its articles as linked titles, never as the raw "url — title" line,
    through the one tested reader of that format (`health.split_affected`).
  - Each article says what is already held of it ("supplied — held until you confirm its
    licence", "a preview is held").
  - A source whose articles the scan cannot list (Morgan Stanley, Goldman Sachs) shows "Where to
    look: <its research page>" instead of "unknown — the channel cannot be read".
  - The weekly commands wrap after `python -m vinci.theme_intelligence`, never mid-word.
- **Phone width.** Number cells that stack into cards carry their label ("newest article",
  "sources", "open findings"). The Themes search box takes the full width.
- **The operator's three PDFs — dry run only.** Run on a scratch copy of the pilot registry with
  `--cache-only` and no licence statement. Nothing was written to the pilot registry and nothing
  was sent to a model.

  | PDF | Publisher | Size | Finding | Dry-run result | Estimate (list price) |
  |---|---|---|---|---|---|
  | "Beijing Will Not Pace the Frontier" | SemiAnalysis | 20 pages, 4,698 words | ends with the subscriber notice, so it is the same preview already held: 48 of its 50 paragraphs of ≥12 words are in the held text (the other two are its title line and a table header, 43 words) | Match uncertain | $1–8 |
  | "Are Open Models Catching Up?" | SemiAnalysis | 16 pages, 1,946 words | ends with the subscriber notice, so it is a preview | HELD, and now PARTIAL | $1–7 |
  | "Money: The Evolution to Digital" | Citi | 7 pages, 2,151 words | no notice: a complete document | HELD (licence) | $1–7 |

**WHY.** Two things the operator raised. First: "still many of the columns with crammed up and
have lot of illegible or non-required content", Sources first. Second: whether uploading the
requested articles is the right weekly process, and why Goldman Sachs and Morgan Stanley requests
carry no link. The dry run of the uploads is what exposed the importer defect, and a preview
recorded as read in full would have broken the desk's first rule: a preview is never presented
as read in full.

**HOW VERIFIED.**
- **Importer, real files.** Before the fix, the reader labelled the "Open Models" PDF FULL. After
  it, both SemiAnalysis PDFs are PARTIAL and Citi's stays FULL.
- **Corpus before synthetic.** The marker was run over every distinct document stored in the
  local registries (10, including three long real reports: Citi's ETF, Gridlock and LatAm). It
  matches none of them, and matches exactly the two SemiAnalysis PDFs among the three supplied.
- **Pins.**
  - `tests/test_theme_intelligence_ingestion.py`: a saved preview is PARTIAL and says why; its
    analysed version is stored PARTIAL and Uploads lists it; the full post stays FULL (negative).
    It runs on a new synthetic fixture, `semianalysis_preview_saved_synthetic.pdf`, printed by
    `make_fixtures.py` from invented text.
  - `tests/test_theme_intelligence_desk.py` (4 new):
    - Sources says each channel's state in plain words and folds the check's own sentences; a
      healthy channel has no fold; one check draws no strip.
    - Uploads links each requested title, says what is held, and points to the research page.
    - `split_affected` reads the stored shapes.
    - Articles' follow-up links Uploads, and the figure count lives in the fold.
  - Mutants: 8 of 8 killed (the importer's PARTIAL; the plain line; the strip; the research-page
    link; the reader; the supplied note; the follow-up link; the figure count).
- **In the app** (local preview, headless Brave):
  - no horizontal overflow on Sources, Articles and Uploads at 1440 and 390 px, real pilot and
    synthetic 12-week registry;
  - also none on This week and a reading page at 390 px (real pilot);
  - the after-supply Uploads rendered from the dry-run copy.
- **Standalone pages:** 0 broken links and 0 default-view problems over 386 pages.
- Ruff and `mypy --strict` are clean; the offline suite result is in the PR.

**BOUNDARY.**
- "Pilot registry": a copy of `data/theme_intelligence/v2/pilot-2026-10-12/registry.db` at
  `R-20261012T133456Z-reassess`.
- The dry run: a second copy, three `ingest-file --cache-only` runs on 2026-10-13. Model calls in
  that copy were 23 before and 23 after.
- "10 stored documents": distinct files under `data/theme_intelligence/**/documents/` in the
  `theme-intelligence` worktree, read 2026-10-13 by the current reader.
- Word counts are the text the importer would send. The estimates are `ingest.estimate_cost`:
  deterministic, before any call.
- "386 pages": the standalone renders of the real pilot (18), the synthetic 12-week registry
  (350) and the dry-run copy (18), on 2026-10-13.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0: no model call; nothing written to the pilot registry.
- **OPEN, the operator's:**
  - whether to analyse Citi's "Money" (it needs a licence statement, `--llm-permitted`, and costs
    $1–7 at list price);
  - whether to import the two SemiAnalysis previews at all ("Beijing" adds nothing; "Open Models"
    would be analysed as a preview);
  - whether Nomura's portal-only reports should stop being requested.
- **Nomura's full reports sit on its client portal** (go.nomuranow.com), which offers no public
  sign-up, so its "Full report needed" requests cannot be met. Changing that is a pipeline and
  health-check policy ("not obtainable"), not a desk change, so it waits for the operator's
  decision.
- **Goldman Sachs and Morgan Stanley:** their sites refuse the scan (403; a dropped connection),
  so no article can be listed. The research page linked is the public one in `sources.toml`.
  Fuller institutional research usually sits behind a client login.
