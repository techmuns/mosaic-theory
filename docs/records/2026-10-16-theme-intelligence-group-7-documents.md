---
id: 2026-10-16-theme-intelligence-group-7-documents
status: recorded
date: 2026-10-16
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — group 7 of the verified review leads, the documents as read and the files their answers are cached in: U30, U15, U22 (U50 skipped)

**WHAT.** Operator, 2026-10-16: "move to group 7". This is group 7 of the grouping in
`docs/records/2026-10-15-theme-intelligence-group-5-facts.md`: how a document is read, which
channel it may come from, and the files that cache paid answers and fetched pages.

| Lead | Defect | Fix |
|---|---|---|
| U30a | Each line of a two-column PDF page was read across both columns, so their sentences interleaved. | **A gutter** is an empty vertical band. At least 3 lines must each hold a gap of 12pt or more, centred in the middle 30–70% of the page, with at least 4 characters on each side; the band is where all those gaps overlap. A line with a character inside the band runs full width (a title, a banner) and stays in place. Each run of lines between such lines is read left half, then right half. Each half is rebuilt from the run's own characters, each character going to the half its centre lies in. A jump back up the page starts a new paragraph. |
| U30b | "Microsoft Office User" (metadata) and "2030" (from "By 2030, …") were read as authors. | An authoring tool's placeholder in the Author field is not an author. A byline counts only when every name is one to five capitalised words. |
| U30c | A footer's "subscribe to read our newsletter" marked a full page PARTIAL. | The page-wide search for a subscriber notice now skips footers and navigation: `<footer>`, `<nav>`, and elements with a `footer` or `site-footer` class. |
| U30d | A table cell that repeated an earlier value ("5%") was dropped, shifting its row's columns. | Table cells are never de-duplicated; other repeated text still is. |
| U30e | "AI-" at a line end followed by "driven" was joined as "AIdriven". | A line-end hyphen after a capital or a digit belongs to the compound and is kept. After a lowercase letter it still marks a split word, which is joined ("sig-" + "nal" → "signal"). |
| U30f | `og:title` was cut at its first dash, so a Citi title with a subtitle was stored as its first half. | Only a trailing part that is exactly the `og:site_name` is dropped. |
| U30g | A line repeated on one page was dropped from the whole document as a running header. | A running header or footer is now counted by pages: it must appear on more than half of them. |
| U15a | A report linked from a live page but hosted by a retired channel was fetched and stored. | The report is never fetched. An INFO issue, `LINKED_REPORT_RETIRED`, names the host's channel and its retirement date, and no upload is requested. |
| U15b | An upload accepted while its channel was live was refused on replay once the channel retired, and stayed pending for ever. | A `state pull` replay of a document from a retired channel is treated as history: it is replayed and attributed to that channel's publisher. A new import from the channel is still refused, and so is a replay from a channel never configured. |
| U22 | A cache file torn by a kill raised JSONDecodeError on every later run. | **`cachefile.py`.** Every paid answer, truncation marker and page record is written whole or not at all: to a temporary file in the same folder, flushed, then renamed over the old one. A torn file is moved to `<name>.torn-<UTC>`, a warning is raised, and the file is treated as absent, so the request is asked or fetched again. A cached page body is checked against the sha256 in its record. |
| U50 | — | **SKIPPED.** The lead was rated only PLAUSIBLE: 0 of 275 cached pages carry a "Read the full article"-style anchor. Building it would be speculative. |

**WHY.** Every one of these lost or bent what a document says before any model read it:
- sentences from two columns spliced together;
- a non-person named as an author;
- a full article analysed as an excerpt;
- a table row shifted;
- a compound misspelt;
- a title halved;
- a repeated line deleted.

U15 broke the retired-channel rule in both directions: it fetched what is refused, and it refused what is history. U22 made one interrupted write a permanent failure.

**HOW VERIFIED.**
- **The PDF corpus, main 2a794602's code against this branch** (CORPUS BEFORE SYNTHETIC). Of
  16 distinct real PDFs, 7 read differently. **0 characters are lost in any of them**, counting
  every non-space, non-hyphen character over all blocks. Every title and author list is
  unchanged.
  - **Columns separated:** a web-page PDF's two columns (28 → 46 blocks); a Citi report's
    disclosure page (a column of analyst names had run into a column of legal entities); a
    web-page PDF's two header cards; one block of a Citi report's infographic, split in two at its
    gutter.
  - **Compounds kept:** "AI-powered", "AI-focused" and "COVID-driven", one in each of three
    PDFs.
  - **Lines no longer dropped (U30g).** These are the 3 distinct lines the lead counted, and none
    is argument text. They were dropped only because the old rule counted occurrences. Each is
    on fewer than half its document's pages, so none is a running header:
    - in one 34-page Citi report, a copyright notice under its exhibits (24 blocks, on 16 pages)
      and a chart source line (19 blocks, on 15 pages);
    - in a 7-page TrendForce PDF, a "Back" link (4 blocks, on 2 pages).
  - **Two looser forms of the column rule failed on this corpus and were fixed before pinning:**
    - On 5 pages of a Citi report, a bullet set 14pt before its text was read as a gutter. The
      bullets became blocks of their own, and a contents page's page numbers were split from
      their titles. Fixed by requiring 4 characters on each side of the gap. Both shapes are now
      in the fixture.
    - A crop that kept only characters lying wholly inside each half lost a glyph that straddled
      the dividing line ("MANAGE" → "MANAG"). Fixed by assigning each character to the half its
      centre lies in, which brought the characters lost to 0.
- **The HTML corpus, 275 distinct cached pages:**
  - 5 distinct titles change, across 18 pages (15 Citi, 3 BofA). Each is now the page's own
    `<h1>` heading, e.g. the full "Overcoming Gridlock 2.0 — Solving Power Bottlenecks to Drive
    AI & Energy Security".
  - 0 retrieval states change and 0 blocks change. U30c and U30d do not occur in these pages.
- **U15:**
  - The 275 pages hold 70 linked reports; none is a report on a retired host linked from a live
    page.
  - The pilot's 9 stored documents all come from active channels.
  - Neither case occurs in the corpus, so both are pinned on synthetic input.
- **U22:** 4,175 cache files were read with plain `json`, moving nothing:
  - 2,506 page records, 1,072 review answers, 327 completeness answers, 247 extraction answers
    and markers, 23 enrichment answers;
  - 0 are torn;
  - 572 cached page bodies were checked against their record's sha256, and 0 differ.
- **Pins:** `tests/test_theme_intelligence_group7.py` has 28 tests, each fix with its negative.
  - Two new synthetic fixtures. `two_column_synthetic.pdf` is a two-column page, then a contents
    page and a margin-set bullet list in the real Citi shapes. `office_export_synthetic.pdf` is
    a placeholder author, a "By 2030," opening sentence, line-end hyphens, a pull-quote twice on
    one page, and a footer on every page. Main's code reproduces every failure on them.
  - The web-page leads are pinned on HYPOTHETICAL pages. U15 is pinned end to end: through
    `process_url` with a retired host, and through `ingest_file` with a replay.
  - U22 is pinned at every call site: a torn extraction answer, named answer, marker,
    completeness answer, enrichment answer, card review and page record; a page body cut short;
    and a failed write. One lint checks that the five cache modules touch no file through bare
    `write_text` / `write_bytes` / `read_text`; at main it finds 20 sites.
- **Mutants: 24 of 24 killed.** An unmutated baseline passes.
- **Suite:** ruff clean; `mypy --strict vinci` clean (189 files); `pytest -m "not network"`
  5,538 passed, 513 skipped.

**BOUNDARY.**
- **Code:** main 2a794602 against this branch, on 2026-10-16. Groups 5 (#723) and 6 (#724) were
  open and unmerged at the time, so neither side of the comparison includes their changes.
- **Data:** everything under the `theme-intelligence` worktree's `data/`, with backups excluded.
  - PDFs are distinct by sha256. The 16 real ones exclude the synthetic fixtures.
  - The 275 HTML pages are the distinct status-200 HTML bodies in its HTTP caches.
  - Cache files are every `*.json` under an `llm_cache/{extract,complete,enrich,review}/` or
    `http_cache/` path.
- **Pilot:** read from a copy. The live `v2/pilot-2026-10-12/registry.db` keeps its checksum
  (5fcc240d4b087d2feb1f81e6d6fabc3c).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0; no model, SEC or web requests.
- **Exhibit chrome is now kept as text.** These are copyright and source lines that appear on
  fewer than half the pages (43 blocks in one Citi report). They are not argument text; they
  cost prompt tokens. Dropping them would need a new exhibit-footer rule, which is not built
  here. *Falsifier: a claim extracted from such a line.*
- **A torn paid answer is paid for again.** The only alternative was failing on every run. The
  torn file is kept beside the new one for inspection.
- **The column thresholds are face-validity values read off this corpus, never off outcomes:**
  12pt, 3 lines, 4 characters, and the middle 30–70% of the page. A three-column page, or a
  gutter outside the middle of the page, is still read line by line as before.
- Noticed and NOT changed: the synthetic fixtures' README says every page carries the banner,
  but multi-page fixtures carry it on page 1 only. This was already true of
  `ms_report_synthetic.pdf`.

**REVIEW FIXES (2026-10-16, `/code-review high` of #723–#725).** Four findings on this PR, all
fixed before merge:
- **A byline name had to begin with an ASCII capital,** so "By Émile Durand and Jane Doe" gave no
  author at all. A name word may now begin with a capital in any script; particles ("von der")
  stay allowed and numbers stay refused.
- **A torn file was said only on stderr,** so a re-paid answer never reached the run record. Each
  file set aside during a run is now a WARN issue `CACHE_FILE_TORN` on that run, plus a run
  warning. A file set aside outside any run is not attributed to the next one.
- **With no `og:site_name`, an og:title kept the " | Site" suffix** the old split removed. A
  trailing part that names the page's own host ("| Morgan Stanley" on morganstanley.com) is now
  dropped too.
- **Every full page was parsed twice.** The footer-free copy is now parsed only when the page's
  text holds a subscriber marker at all.
- **Corpus re-run on the fixed code:** 275 HTML pages, 0 titles, states, blocks or notes change
  against the pre-fix branch; 21 PDFs (16 real and the synthetic fixtures), 0 author or block
  changes.
- **Mutants:** 5 of 5 killed. 36 tests.
