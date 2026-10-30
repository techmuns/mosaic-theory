---
id: 2026-10-30-a-release-figures-span-frame-and-gross-margin-basis-are-read-as-stated
status: shipped
date: 2026-10-30
prs: [873]
supersedes:
superseded-by:
---

# A release figure's span, its release's frame and its gross margin's basis are read as stated; no committed value moves (audit E2-D4, D6, D9; Phase 2 batch B2)

**WHAT.** Changes are in `vinci/edgar/release_parse.py` only. `parse_release`'s signature is
unchanged.
- **SPAN (E2-D4).** A six- or nine-month figure is no longer filed as the quarter.
  - `_PHRASE`'s year-to-date group reads a bare "six/nine month(s)" span, so "ended" is no longer
    required. "Nine Months Highlights", BellRing's "Nine Month Operating Results" and
    "Nine-Month Results" are year-to-date sections.
  - `_PERIOD_WORD` reads "month" in the singular, so those headings count as headings at all.
  - `_under_trailing_lead_in` reads a year-to-date lead-in ("● For the nine months ended
    September 30, 2026: ○ …") as well as the trailing-twelve-month lead-in of audit E2-D5.

  A figure under any of these takes no period label, which is the rule for TTM.
- **FRAME (E2-D6).** `_release_frame` never takes its frame from a comparison in the head
  (`_own_header`: a match after a `_CMP` marker or "from" in its own clause is skipped). Amazon
  heads its 2026 releases "… in the second quarter, compared with $167.7 billion in second
  quarter 2025", and both framed as 2025. A head that names its quarter only by its end date
  ("its second quarter ended June 30, 2026", `_HDR_QENDED`) now frames by that date, with no
  fiscal shift. The year is the date's own, and `_fy_offset` would have read +1 from Amazon's
  table column header "Three Months Ended March 31, 2025 2026".
- **BASIS (E2-D9).** The GAAP gross margin is the first `_GROSS_MARGIN` statement that meets
  three tests: it is not non-GAAP (`_NON_GAAP_LEAD`: "Non-GAAP", "adjusted" or "Non-GAAP
  adjusted", standing right before it), it is not a segment's, and it states its period.
  - Before, a 12-character "adjusted" look-back let "Non-GAAP gross margin was 47.0%" through as
    GAAP.
  - Only the first statement was ever read, so a GAAP margin stated after a non-GAAP or a
    year-to-date one was dropped.
- **`EXTRACTION_VERSIONS` row `2026-10-30.E2-spans-frames`**, in both twins. The drift pins are
  repinned.

**WHY.** Two of audit E2's root-cause classes:
- **The period from the wrong place (RC2).** A heading's span was unread, and a comparison set
  the release's frame.
- **A substring metric match (RC4).** "gross margin" inside "Non-GAAP gross margin".

None of these moves a committed value, and none is on the decision path. Each is closed behind
its probe.

**HOW VERIFIED.**
- **Failing first.** `tests/test_release_spans_and_frames.py` holds 15 tests. All 15 pass on this
  branch.
  - **Main `8e6b12b1`:** 9 fail (A5–A7, A9–A11, BellRing's nine-month section, the year-to-date
    lead-in, Amazon's two heads, and the fiscal-shift pin). 6 pass: the 4 negative pins, and
    review round 0's 2.
  - **Review round 0** (`/code-review high --fix`): its 2 pins guard regressions that the first
    draft introduced and main does not have. Each fails on the draft: "Adjusted EPS and gross
    margin was 40.0%" lost its GAAP figure, and a segment's gross margin was reached past an
    unreadable first statement.
- **The real-text fixtures**, each verbatim (whitespace collapsed); where a test joins two
  fragments of one filing, it says so:
  - Amazon: 8-K 0001018724-26-000024 and -000012, each head at ≤600 characters, plus its
    income-statement column header;
  - BellRing: 0001628280-26-052137, its head and the nine-month section;
  - NIKE: 0000320187-26-000026, its head and income statement. This is the brief's negative pin,
    Q3 gross margin 40.2;
  - Microvast: 0001628280-26-055471, a GAAP gross margin first and the non-GAAP adjusted one after.
- **The real run.** A read-only, offline replay from the primary checkout's SEC cache, run on
  main's code and on this branch's code, compared field by field (guidance, actuals, one-offs,
  qa_flags):
  - **The 13 pages in the rebuild's scope:** 53 of 54 cited releases. **0 field differences.**
  - **26 of the 27 committed pages:** 113 exhibits. **0 field differences.**
- **Each check on real text** (127 EX-99 documents: the 113, plus 14 more cached EX-99 found by
  filename):
  - **Frames.** 3 change, all Amazon: 2026-07-30 from Q2 2025 to Q2 2026, 2026-04-29 from Q1 2025
    to Q1 2026, and the cached Q3 2025 release (`amzn-20250930xex991`) from Q3 2024 to Q3 2025.
  - **Labels.** Of the 494 actual-candidate figures (`_RECON`, `_REVENUE` and `_GROSS_MARGIN`
    matches, before any dedupe), 2 lose their label. Both are BellRing's year-to-date adjusted
    EBITDA: $222.4M under "Nine Month Operating Results" (2026-08-04), and $144.1M under "Six
    Month Operating Results" (2026-05-05). Main labelled each as that release's quarter, then
    dropped it only because the quarter's own figure held the slot.
  - **Gross margin.** No stored figure changes. The 15 gross-margin rows the 26 pages' releases
    parse to are identical.
- **Gates.** ruff, `mypy --strict vinci`, `node --check frontend/views/shared/dossier.js`, and the
  full offline suite (`pytest -m "not network"`). The PR body carries the counts.

**BOUNDARY.**
- **Commit.** Measured 2026-10-30, main `8e6b12b1` against this branch.
- **Pages.** 27 committed pages under `data/dossiers/`. One is held out under a standing operator
  constraint and was not opened or replayed, and its issuer's filings were excluded from the
  cache scan by CIK.
  - The 13 pages in the rebuild's scope: AMZN, CNXC, GOOGL, LLY, NFLX, NKE, ORKA, PARR, ROST,
    SMPL, TJX, UBER and V.
  - The other 13: AORT, BRBR, EPAM, FUBO, IT, MVST, NCNO, TECX, TGT, VITL, VRRM, WERN and WLK.
- **Releases.** One EX-99.1 per cited 8-K.
  - The 13 pages: 54 cited, 53 cached (no EX-99.1 resolves from the cache for LLY's 2026-10-29
    8-K).
  - All 26: 114 cited, 113 cached.
- **Label population.** 494 matches across the 127 documents, each compared at main's and the
  branch's frame.
- **Cache.** The primary checkout's `data/cache/sec`, read-only, with no network.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A bare "six months"/"nine months" in a figure's own clause now unlabels it.** For example,
  "revenue of $X million, the most in nine months". Of the 494 real candidates, only BellRing's
  two year-to-date figures changed. Falsifier: a quarter's figure dropped for a span word that
  is not its own.
- **A head framed by its quarter-end date takes the date's calendar year.** For a fiscal-year
  filer whose head names no fiscal year, that is not the fiscal year. Only Amazon (calendar)
  frames this way in the 127 documents. Falsifier: a fiscal filer's quarter labelled a year
  early.
- **The GAAP gross margin is now the first readable statement, not only the first statement.** A
  release whose first gross-margin statement states no period now yields its next one, never a
  segment's. On the 26 pages' releases the stored figures are identical.
- **`_fy_offset` can read a table's column header as the quarter end** (review round 0, not
  changed here). Amazon's "Three Months Ended March 31, 2025 2026" gave +1. The quarter-end frame
  bypasses it. A header-framed calendar filer with such a table would get the same +1. In the
  127 documents only BellRing (fiscal, +1) and Target (fiscal, −1) carry a non-zero offset, and
  both are correct. Falsifier: a calendar filer's frame with a non-zero `fy_offset`.
