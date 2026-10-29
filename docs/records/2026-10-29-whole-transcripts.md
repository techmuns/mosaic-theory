---
id: 2026-10-29-whole-transcripts
status: open
date: 2026-10-29
prs: []
supersedes:
superseded-by:
---

# Each earnings call reaches the model whole, and a call it does not get is named (audit G-D3, G-D4; operator ruling 2026-10-29, "Whole transcripts")

**WHAT.**
- `ciq_sheets.transcript_for_synthesis` no longer cuts each call at 12,000 characters. The driver
  extraction and the synthesis read every call on file after `_transcript_prose` strips the
  boilerplate: prepared remarks and the full Q&A.
- A call past `_TRANSCRIPT_CEILING` (100,000 characters, about 1.4× the longest committed call)
  is cut there. It ends in a `[… CUT: …]` marker the model reads, and it is named in a QA flag.
- `unparsed_transcript_flag` names every call on file that is missing from the slice (audit
  G-D4), not only an empty slice.
- The synthesis prompt says the calls are whole. The comment that called the old slice the
  "WHOLE transcript" is corrected.
- Extraction version `2026-10-29.G-D3`, after B4's six A-rows; `tests/test_extraction_version_drift.py` re-pinned at it
  (48 modules).
- STATE §5.0 row 41 (the combined rebuild) carries the page note: every page's
  transcript input grows, and AMZN's driver phase is near its output cap.

**WHY.**
- All 48 committed calls were cut, with no marker. In 37 of them the Q&A began after the cut, and
  the median share sent was 22%.
- Meanwhile the prompt said "Prepared remarks + Q&A" and a docstring said the latest call's Q&A
  was never truncated. That broke CLAUDE.md's rule that a truncated output prints its own
  truncation, on the input the lean is drawn from.
- A failed read beside a sibling that read left the model a call short, in silence. It was seen
  live on 2026-10-29: two LibreOffice conversions at once make one fail.
- The operator chose whole calls over a marker on the cut.

**HOW VERIFIED.**
- **Tests.** 5 pins in `tests/test_transcript_slice.py`, on invented calls written as real RTF and
  read through `CiqBundle.from_files` → striprtf → `_transcript_prose`:
  - 4 fail on 8a38005a; the fifth is their negative.
  - The end-to-end pin reads the prompts the driver phase and the synthesis are SENT.
  - One existing pin labelled its slice `call` for a file named `c.rtf`. That is a missing call
    now, so it carries the file's name.
  - Full offline suite: 7,948 passed on the branch; after merging main at bb4ab6e5, 8,105 passed with the
    stale-pin warning as an error.
- **Before/after leans** (operator condition, paid). The same code ran on both sides: this branch
  merged onto #859's head, so the validator is the per-fact one. Only the slice differed (today's
  12,000-character cut vs whole calls). Each side ran the driver extraction over its slice,
  merged onto the committed page's anchored rows, then five synthesis draws with the page's
  sleeve. Nothing was written to the repo.

  | page | side | slice chars | driver rows (in → out tokens) | synthesis prompt tokens | draws | proposal | UNTRACEABLE / TRANSCRIPT-FIGURE | USD |
  |---|---|---|---|---|---|---|---|---|
  | NKE | today | 24,122 | 18 (9,075 → 2,059) | 151,015 | mixed 5/5 | none | 8 / 0 | 1.88 |
  | NKE | whole | 112,086 | 36 (37,286 → 3,708) | 189,178 | mixed 5/5 | none | 7 / 1 | 2.42 |
  | AMZN | today | 24,134 | 29 (9,213 → 3,523) | 255,435 | strongly-bullish 4, mixed 1 | withheld | 10 / 1 | 2.76 |
  | AMZN | whole | 106,484 | 72 (34,962 → 8,736) | 302,014 | strongly-bullish 5/5 | BUY | 7 / 3 | 3.43 |
  | MVST | today | 24,150 | 7 (9,265 → 1,090) | 103,232 | strongly-bearish 5/5 | AVOID (terminal) | 21 / 0 | 1.45 |
  | MVST | whole | 43,592 | 16 (15,661 → 2,152) | 113,572 | strongly-bearish 5/5 | AVOID (terminal) | 22 / 1 | 1.58 |

  Total: $13.51 at list price. No prompt-cache miss on any side.
  - The modal lean is the same on every page.
  - AMZN's proposal moved from withheld to BUY. One draw more agreed, which is inside the run-to-run
    variance already measured on AMZN (BUY 4 of 5 on 2026-09-25). It is not evidence that whole
    calls change a lean.
  - Whole calls more than double the transcript rows on every page.

**BOUNDARY.**
- Calls: the 48 on file for the 24 names with transcripts among the 26 Phase-1 pages, in the
  assembler's CIQ copy, 2026-10-29. One page is held out of Phase 1.
- Whole calls run 17,443–72,147 characters (median 55,682). Per page: median 111,317 characters,
  max 141,914, against 24,000 sent today.
- Before/after: 3 pages chosen ahead of the run.
  - NKE: both calls' Q&A start past today's cut.
  - AMZN: the largest committed synthesis prompt.
  - MVST: the shortest calls.
- One page, 5 draws a side, on the pages' committed mechanical layers. A tally, never a rate.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Measured cost:** +$0.13 (MVST), +$0.53 (NKE) and +$0.67 (AMZN) a page, driver phase included.
  - Synthesis prompts grow +10k, +38k and +47k tokens. That is more than the slice alone adds
    (≈ +30k median at 0.3425 tokens a character), because the doubled driver rows are in the
    prompt too.
  - AMZN reaches 302k tokens.
- **Driver output headroom:** AMZN's driver phase wrote 8,736 of its 16,384 output tokens. A page
  whose calls are longer could reach the cap. That fails loud (`LlmError` → no transcript rows
  and a flag), never a partial row set.
  - Falsifier: a rebuild page whose driver phase raises at `max_tokens`.
- **Concurrent LibreOffice:** two assemblies on one machine can still lose a call. It is now
  named in the QA flag; run assemblies one at a time.
