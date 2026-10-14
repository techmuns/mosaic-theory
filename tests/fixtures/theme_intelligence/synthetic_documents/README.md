# Synthetic documents — invented content, for automated tests only

Every file here is **SYNTHETIC**: text invented for these tests, printed to real PDF bytes by a
headless Chromium browser (`make_fixtures.py`). Every page carries the banner
"[SYNTHETIC TEST FIXTURE — invented content for automated tests; not research by any publisher]".
Nothing here is, quotes, or paraphrases research by SemiAnalysis, Morgan Stanley, Goldman Sachs or
any other publisher. The figures are made up.

They exist because the scenarios they test involve documents this repository must never hold:

| File | Stands in for | Tests |
|---|---|---|
| `semianalysis_preview_synthetic.txt` | the free preview paragraphs of a paid post (what the feed delivers, recorded PARTIAL) | Case A — preview, then full document |
| `semianalysis_full_synthetic.pdf` | the full post, supplied later by an authorised subscriber | Case A — the upgrade; byline authors |
| `semianalysis_preview_saved_synthetic.pdf` | a paid post's page saved as PDF without a paid sign-in: the preview, then the subscriber notice | a supplied preview is recorded PARTIAL, never FULL |
| `web_page_dated_in_a_box_synthetic.pdf` | a research web page saved as PDF whose headline and date sit in layout boxes the reader detects as a table | the date is read from the page, never left unknown |
| `overprinted_chart_synthetic.pdf` | a web page saved as PDF whose chart label is printed three times over itself (faux bold) beside a body figure with legitimately repeated digits | an overprinted label is read once (61%, not 666111%%%); repeated digits in the text stay (1100) |
| `ms_report_synthetic.pdf` | a two-page report from a channel that refuses automated access | Case B (no URL), Case C/D, tables, footnotes, page refs |
| `ms_report_synthetic.html` | the same report saved as HTML | Case C — one report in two formats is one article |
| `scanned_page_synthetic.pdf` | a report with a page that has no text layer | the scanned-page flag; PARTIAL |
| `undated_synthetic.pdf` | a report that prints no publication date | no date from the file name or PDF metadata |
| `glyph_mixed_synthetic.pdf` | a report whose text layer is partly undecodable — a font with no character map, read as `(cid:N)` codes (written byte by byte by `make_glyph_fixture.py`) | glyph quarantine: a clean page, a mixed page (readable lines, a mention of a CID, an undecodable table cell), an unreadable page |

The real end-to-end demonstrations (public PDFs, live LLM extraction) are recorded in the build
record and its worked-output folder, not here: those documents are not ours to redistribute.
