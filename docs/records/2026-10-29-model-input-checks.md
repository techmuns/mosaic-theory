---
id: 2026-10-29-model-input-checks
status: shipped
date: 2026-10-29
prs: [859]
supersedes:
superseded-by:
---

# The checks between a model's reply and the synthesis now check what they claim: a transcript row's call, context and period come from one located quote; a value must equal a quote figure in its unit; a citation must be a ref; a figure traces to the fact its point cites (audit G-V1, G-D1, G-D2, G-D5, G-D6)

**WHAT.** Five checks on the decision path, each of which passed cases it exists to refuse.

- **One located quote (G-V1, `driver_extract._locate`).** The citation kept the LAST call holding a
  quote and the context took the FIRST match in the slice. On AORT's committed page the sentence
  that opens "Lastly, BioGlue was relatively flat" is on both calls: the row dated Q1 2026 is cited
  to the Q4 2025 call, and the row dated Q4 2025 carries a paragraph only the Q1 2026 call has. Now
  the call and the paragraph come from one occurrence; a quote on several calls takes the one whose
  quarter the row's period names, and otherwise is cited to no call, given no context and flagged.
- **Exact, unit-compared values (G-D1, `_figures` / `_figure_in_quote`).** A value figure passed if
  it was within 2% of a quote figure at any of nine scales, and units were never read, so "2.66
  MWh", "266 GWh", "271 MWh" and "16.3%" all passed against "266 megawatt hours … up 16%". Now a
  value figure must EQUAL a figure of its own quote, and every currency, scale word and unit the
  value states must be the one the quote states (MWh = megawatt hours; GWh is not). The module
  docstring said such rows were dropped; it is now true.
- **A period only where the quote states it (G-D2, `_row_period`).** The model's period was copied
  unchecked. It is kept only when the quote states it, and is otherwise None; a dropped period that
  was not just the cited call's quarter is flagged. The first cut of this PR filled in the call's
  quarter instead — a period read from POSITION ("full-year ASP growth of 4%" said on the Q1 call
  is not a Q1 figure) — and review round 1 reverted it; the call is already in `source_ref`.
- **A citation is a ref, not a fragment (G-D5, `synthesis._traces`, `exposure._cited_filing_text`).**
  `ref in u or u in ref` counted `''` (a substring of every ref) and `'EOD'` (of every EOD ref) as
  cited, for points, missing-data claims and twins. Now a ref must BE one of the layer's refs on
  `verbatim.comparison_key` (case, spacing, typography folded), and an empty one cites nothing. In
  exposure, a fact resolves only to the ONE filing its accession names (or whose whole ref it is),
  and every cited fact is grounded — an empty or accession-less ref used to skip grounding.
- **A figure traces to the fact its point cites (G-D6, `synthesis._values_by_ref`).** The trace ran
  against every number in the layer (5,615–11,808 a page) and could not fail. It now reads only the
  numbers the cited fact STATES (`_stated_numbers`), from its values rather than a JSON dump: a date
  (ISO, CIQ's "Aug-31-2026", "May 07, 2026", "Nov-2025", "Q1-26", "FY2024-25") gives its year,
  traced only as that year, and an accession, a URL or an id gives nothing. The first cut scanned
  the dump, so 2026-08-14 put 2026, 8 and 14 in the fact (2026 × 1e-2 traced a made-up "20.3%")
  and a dumped "−" read as 2212 through its escape; review round 1 found the dates. The claim side
  skips the same dates and a digit fused to a word ("GLP-1", "low-20s").

One extraction version, `2026-10-29.G-V1`, names all five (Python table and its web twin).

**WHY.** The synthesis is told these rows are "already validated" and that a row's context
qualifies its fact; its committed lean drives the machine's proposal. A check that cannot fail
reports validation that did not happen.

**HOW VERIFIED.**
- 37 pins in `tests/test_model_input_checks.py`. 21 failed on c51c286a, run in a detached checkout of
  it (the decisive-mirror dedup keyed on the cited ref was found in this PR's own review and failed
  on its first commit); 4 more failed on 91e77597 and pin review round 1 (the date and accession
  digits, and the period left empty); the rest are their negatives. Two existing fixtures leaned on the
  defects and were corrected, each with a comment: `test_themes_exposure._STREAM`'s stub filings
  now carry the tokens their facts cite (they passed only because a non-EDGAR ref skipped
  grounding), and the guardrail test in `test_dossier.py` cited the relative-return fact for two
  absolute returns.
- G-V1 and G-D2 on real transcripts, no model call: every committed transcript row was fed back
  as the model's reply through `extract_transcript_drivers` on today's production slice
  (`transcript_for_synthesis` over the calls in the assembler's CIQ copy, read-only), once on
  c51c286a's code and once on this one. Main reproduces every committed citation and context on
  the 23 names whose calls are all still on file (602 rows), so the slice is the one the pages were
  built on. Across the 620 replayable rows, exactly TWO change citation or context, both AORT's: the
  Q1-dated "BioGlue" row moves to the Q1 2026 call, and the Q4-dated one keeps the Q4 2025 call and
  now carries that call's own next paragraph instead of the Q1 call's. Periods, on the round-1 code:
  82 rows keep a period their quote states and 538 carry none (54 already had none); of the 484
  periods dropped, 157 are flagged and 327 were only the cited call's quarter. No row is dropped
  that main kept.
- G-D1 on the corpus: every committed transcript row passes the new check (626 of 626), and each
  row's own first figure rescaled ×100 is refused.
- G-D5 on the corpus: all 484 committed synthesis points cite an exact ref; no UNCITED flag before
  or after, and the one point read as uncited (SMPL's MISMATCH: a missing-data claim citing a
  present field) and the 12 twin flags are the same on both; of 14,595 committed exposure refs,
  14,593 resolve by one accession under both rules and 2 are uncited under both.
- G-D6 on the corpus: `_validate` over the 26 committed syntheses with no model call. Main: 0
  UNTRACEABLE, 0 TRANSCRIPT-FIGURE. Round-1 code: **263 hard UNTRACEABLE figures on 137 of 484
  points, on all 26 pages (1–21 a page, median 10)**, and 24 soft TRANSCRIPT-FIGURE notes on 13
  pages (QA, hidden). The first cut read 258 hard / 30 soft: dropping dates and ids added 18 hard
  flags, real figures that had traced only through a date's digits (AORT 20.6x, NFLX 20.2x, GOOGL
  $201,846M, SMPL 10.9x, V's $20bn buyback), and removed 13 hard and 7 soft (adding 1) that were
  date or label pieces ("Q2-26", "S-8", "EX-99.1"). A 16-flag hand sample of the first cut (seed 7): every one is a figure the point takes
  from a fact it does not cite — two leverage panels cited as one, a percentile and its range cited
  to the current-multiple fact, absolute returns cited to the relative return. On the frozen SMPL
  page 195 of 199 made-up figures are flagged (0 on main, 189 on the first cut); the 4 that trace
  sit within tolerance of a number the cited fact states.

**BOUNDARY.**
- Corpus: `data/dossiers/*/dossier.json` at c51c286a, 26 of the 27 committed pages (one is held out
  of Phase 1); unit = synthesis point, transcript row (`tier == llm-fenced`), figure or ref as named.
- G-D2: 571 of 626 committed transcript rows carry a period; 82 are stated in their quote, 489 are
  not; 55 carry none. The replay counts are over the 620 replayable rows.
- G-D6: measured 2026-10-29 with this PR's round-1 code (the commit after 91e77597) over the pages
  at c51c286a; units are figures (a point can carry several) and points.
- Exposure: every `disclosed_facts` ref in the 7 files of `data/scan_history/*/*.jsonl`.
- Replay: the 24 names with transcript rows among the 26, their 48 calls as on file 2026-10-29;
  SMPL's 6 rows whose call is no longer on file do not replay on either code (620 of 626).
- The frozen page is `tests/fixtures/frozen_pages/2026-08-18/SMPL/dossier.json`, seed 20261029,
  200 draws in [100, 1000) at 1 dp (199 distinct).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Nothing on a committed page moves in this PR.** Each check acts at assembly; the pages change at
  the combined Phase-1 rebuild. AORT's page keeps its mis-cited row until then.
- **The G-D6 finding went to the operator, and is ruled.** Every UNTRACEABLE flag is a
  CAVEAT shown to the reader (`flags.py`), so a rebuild on this code prints ~10 a page (1–21 on
  the committed pages). The point schema has ONE `source_ref` and the prompt never says a
  point's figures must all come from it, so a multi-fact point is the model doing what it was
  asked. RULED 2026-10-29, the operator verbatim: "Show on the page" — UNTRACEABLE figure caveats stay reader-facing (`flags.py` routing unchanged); TRANSCRIPT-FIGURE notes stay QA. A true gap between a figure and the fact it cites is shown, not hidden; letting a point cite each fact it uses (the citation schema) is a later build.
- The value check reads units from a closed map; a unit word outside it compares nothing rather
  than guessing (falsifier: a committed row whose value and quote differ in an unmapped unit).
