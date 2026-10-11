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
| `ms_report_synthetic.pdf` | a two-page report from a channel that refuses automated access | Case B (no URL), Case C/D, tables, footnotes, page refs |
| `ms_report_synthetic.html` | the same report saved as HTML | Case C — one report in two formats is one article |
| `scanned_page_synthetic.pdf` | a report with a page that has no text layer | the scanned-page flag; PARTIAL |
| `undated_synthetic.pdf` | a report that prints no publication date | no date from the file name or PDF metadata |

The real end-to-end demonstrations (public PDFs, live LLM extraction) are recorded in the build
record and its worked-output folder, not here: those documents are not ours to redistribute.
