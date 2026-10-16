Operator, 2026-10-16: "move to group 7". This is group 7 of the grouping recorded with group 5 (#723). It covers how a document is read, which channel it may come from, and the files that cache paid answers and fetched pages. The full account is in `docs/records/2026-10-16-theme-intelligence-group-7-documents.md`.

**Independent of #723 and #724.** This branch was cut from main and shares no code with either. All three PRs append a clause to STATE row 32, so each one merged after the first takes main's line and keeps its own clause. No published view changes. This PR stops for the operator's merge approval.

## What changes

| Lead | Defect | Fix |
|---|---|---|
| U30a | Each line of a two-column PDF ran across both columns, interleaving their sentences | The page is read a column at a time. A gutter is a band left empty by 3+ lines, each with a gap of 12pt or more mid-page and 4+ characters on each side, so a bullet or a page number beside its line is no gutter |
| U30b | "Microsoft Office User" and "2030" (from "By 2030, …") were read as authors | An authoring tool's placeholder is not an author; a byline counts only when every name is 1–5 capitalised words |
| U30c | A footer's "subscribe to read" marked a full page PARTIAL | The page-wide search for a subscriber notice skips footers and navigation |
| U30d | A table cell repeating a value was dropped, shifting its row | Table cells are never de-duplicated |
| U30e | "AI-" + "driven" was joined as "AIdriven" | A line-end hyphen after a capital or digit is kept ("sig-" + "nal" still joins) |
| U30f | `og:title` was cut at its first dash | Only a trailing part that names `og:site_name` is dropped |
| U30g | A line repeated on one page was dropped as a running header | Running headers are counted by pages (more than half) |
| U15a | A report linked from a live page but hosted by a retired channel was fetched and stored | It is never fetched; an INFO issue `LINKED_REPORT_RETIRED` is raised and no upload is requested |
| U15b | A replay of an upload from a since-retired channel was refused for ever | The replay is treated as history and attributed to that channel's publisher. A new import is still refused, and so is a replay from an unknown channel |
| U22 | A torn cache file raised JSONDecodeError on every later run | `cachefile.py`: atomic writes (temporary file, fsync, rename). A torn file is set aside as `<name>.torn-<UTC>`, warned about and asked or fetched again. A page body is checked against its sha256 |

## Real-run verification

All comparisons run main 2a794602's code against this branch, over the `theme-intelligence` worktree's `data/` with backups excluded.

**PDFs: 16 distinct real files; 7 read differently, and 0 characters are lost in any of them.** Titles and authors are unchanged in all 16.
- **Columns separated:**
  - a web-page PDF (28 → 46 blocks);
  - a Citi disclosure page, where a column of analyst names had run into a column of entities;
  - a web-page PDF's two header cards;
  - one block of a Citi report's infographic, split in two at its gutter.
- **Compounds kept:** "AI-powered", "AI-focused" and "COVID-driven".
- **Lines no longer dropped (U30g):** the 3 distinct lines the lead counted, none of them argument text. In one Citi report these are a copyright notice and a chart source line, on 16 and 15 of its 34 pages. In a TrendForce PDF it is a "Back" link, on 2 of 7 pages.
- **Two looser forms of the column rule failed on this corpus and were fixed before pinning:**
  - Bullets set 14pt before their text, on 5 pages of a Citi report, became lone "•" blocks, and its contents page split page numbers from their titles. Both shapes are now in the fixture and pinned.
  - A crop that kept only characters lying wholly inside each half lost a glyph straddling the line ("MANAGE" → "MANAG").

**HTML: 275 distinct cached pages.**
- 5 distinct titles change, across 18 pages (15 Citi, 3 BofA). Each now equals the page's own `<h1>`, e.g. the full "Overcoming Gridlock 2.0 — Solving Power Bottlenecks to Drive AI & Energy Security".
- 0 retrieval states and 0 blocks change. U30c and U30d do not occur in these pages.

**U15:** the 275 pages hold 70 linked reports, and none is a report on a retired host linked from a live page. The pilot's 9 documents all come from active channels. Neither case occurs in the corpus, so both are pinned on synthetic input.

**U22:** 4,175 cache files, read with plain `json` so nothing was moved:
- 2,506 page records, 1,072 review answers, 327 completeness answers, 247 extraction answers, 23 enrichment answers;
- 0 are torn;
- 572 page bodies were checked against their sha256, and 0 differ.

Checks:
- **Pins:** `tests/test_theme_intelligence_group7.py`, 28 tests, each fix with its negative.
  - Two new synthetic PDFs, `two_column_synthetic.pdf` and `office_export_synthetic.pdf`; main's code reproduces every failure on them.
  - U22 is pinned at every call site.
  - A lint checks that the five cache modules use no bare `write_text`, `write_bytes` or `read_text`; it finds 20 such sites at main.
- **Mutants:** 24 of 24 killed, and the unmutated baseline passes.
- `ruff check .` and `mypy --strict vinci` (189 files) are clean.

Offline suite (`pytest -m "not network"`): **5,538 passed, 513 skipped, 37 deselected** (exit 0); record and STATE lints 734 passed, 1 skipped.

## Disposition

| Item | Status | Note |
|---|---|---|
| U30a two columns | SHIPPED | 4 real PDFs read differently; 0 characters lost |
| U30b placeholder / clause authors | SHIPPED | 0 of 16 real PDFs affected (as the lead found) |
| U30c footer subscribe link | SHIPPED | 0 cached pages affected |
| U30d repeated table cells | SHIPPED | 0 cached pages affected |
| U30e compound hyphens | SHIPPED | 3 real PDFs |
| U30f whole og:title | SHIPPED | 5 distinct titles, each now the page's own heading |
| U30g running headers by pages | SHIPPED | restores the lead's 3 non-argument lines (see accepted) |
| U15a retired host's linked report | SHIPPED | not in the corpus; pinned |
| U15b replay from a since-retired channel | SHIPPED | not in the pilot; pinned |
| U22 atomic cache files, torn ones set aside | SHIPPED | 0 torn files in 4,175 |
| U50 "Read the full article" anchors | SKIPPED | PLAUSIBLE only; 0 of 275 cached pages carry the form, so building it would be speculative |

Accepted, stated in the record:
- **Exhibit chrome is now kept as text:** copyright and source lines on fewer than half the pages (43 blocks in one Citi report). Falsifier: a claim extracted from such a line.
- **A torn paid answer is paid for again** instead of failing every run. The torn file is kept for inspection.
- **The column thresholds are face-validity values from this corpus**, never from outcomes. A three-column page is read as before.

Noticed and not changed: the synthetic fixtures' README says every page carries the banner, but multi-page fixtures carry it on page 1 only. This was already true of `ms_report_synthetic.pdf`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

