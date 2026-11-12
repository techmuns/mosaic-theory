---
id: 2026-11-12-w05-figure-trace-false-flags
status: shipped
date: 2026-11-12
prs: [1040]
supersedes:
superseded-by:
---

# The figure trace stops flagging five classes of correct figure (W05, the follow-up to #1023) — a metric no table row carries meets the cited fact, a fact's own printed width counts, a year naming what it dates is no figure, a January year end's "fiscal 2025" is CIQ's FY26, and a field name, accession, URL or hash states no span for the page; on the 27 committed pages exactly two flags clear (PARR's "$21.54", VITL's "2030") and none is added

**WHAT.** #1023 made the synthesis figure trace read a figure as written (RG-D1 to RG-D7). Its
record (`docs/records/2026-11-11-figure-trace-as-written.md`, "WHAT IT COSTS") and its round-2
review named the false caveats left. All five are in `vinci/dossier/synthesis.py`:

- **(a) A metric no row carries.** `_claim_rows` bound a figure to the table metric written nearest
  it, and the metric written beside it was invisible when no row label carried that word:
  "revenues" (the row says "Revenue"), "net sales", "operating income" (an EBIT row), "capital
  expenditures" (a Capex row), "profit", "impairment" (an "Asset Writedown" row).
  - Such a word is now a mention of NO row (`_OTHER_METRICS`). Where it is the figure's own, the
    figure binds no row and meets the cited fact.
  - Review round 0: a row mention marked its whole window as covered, so "EBITDA and revenues"
    hid "revenues". Only the phrase's own words are marked now.
- **(b) The fact's printed width.** The tolerance was the smaller of the claim's written width and
  the old 2% / 0.05, so a figure written one digit finer than the fact prints it was refused:
  PARR's "$21.54" against its consensus fact's "21.5 (latest)".
  - Each prose number and display cell now keeps half a unit of its last printed digit, and the
    unit class it is printed in (`_prose_numbers_printed`, `_FactNumbers.halves`, `_Cell.half`).
  - A claim within that width traces, still never wider than the old bound. Two conditions apply:
    - it is compared at the scale the fact prints it in;
    - the fact prints the claim's unit class, or no unit.
  - Both conditions are measured: without them, two TRUE flags cleared.
    - CNXC's "$375M term loan" met a two-decimal "0.37…" read at a thousand.
    - GOOGL's "interest coverage of 60.3x" met a "60%" gross margin in its cited fact.
- **(c) A year that names what it dates.** VITL's "management withdrew its 2030 financial targets"
  was traced as a figure, a year the page never dates.
  - A year after a determiner or a possessive and before a word is now a label
    (`_ClaimFigure.named`).
  - "matures in 2041" and "targets 2041" are still traced (#1023's round-2 pin).
- **(d) A January or February year end.** CIQ labels the year that ends 2026-01-31 FY26. ROST,
  TJX, TGT and BURL each date their FY26 column so (their committed statement reconciliations).
  The company calls that year "fiscal 2025", and `_period_key` read it as FY25.
  - For a page whose reconciled years end in January or February (`_fiscal_shift`), a claim's
    "fiscal YYYY" now keys FY(YY+1).
  - CIQ's own "FY25" is never shifted.
- **(e) A span only the code names.** A duration traced against every window the page named,
  including field names (`pe_percentile_5y`, `high_52w`), accessions and URLs (VRRM's
  "…/d123116d8k.htm" read as 123,116 days, a span of 337 years) and sha256 locators.
  - A field name now labels its own fact's window only (`_FactNumbers.named_windows`), traced in a
    point citing that fact and never page-wide.
  - An accession, a URL or a hash states no span.
  - A ref's window ("EOD SMPL 180d", "39 quarters spanning … (9.5y)") stays a span the page
    states.

**WHY.** A caveat that names a correct figure untraceable teaches the reader to skip caveats. These
were the classes #1023 left. PARR's and VITL's are live; (a) and (d) are latent on today's
corpus; (e) let any duration in a key unknown trace on the code's own names.

**HOW VERIFIED.** All at $0.
- **The committed corpus, re-validated:** every committed synthesis and its layer through
  `_validate`, with main's code (`c2934d07`) and with this branch's.
  - **476 → 474 flags.** Exactly two clear: PARR's "21.54" and VITL's "2030".
  - **None is added**, and no other flag changes.
  - (a), (d) and (e) move no committed flag, as #1023's record expected for (a) and (d).
- **What two rejected designs did on the same corpus:**
  - The width at every scale and unit cleared CNXC's and GOOGL's true flags (above).
  - Taking refs out of the page-wide spans flagged five TRUE own-history spans: TGT's "9.2-year
    range", V's and WLK's "9.5-year", VRRM's "32 quarters" and CNXC's "5.7y". Each is a span the
    EV/EBITDA percentile fact's ref states ("39 quarters spanning 2017-03-31..2026-09-30
    (9.5y)").
  - It also cleared none of the common durations (below). So refs stay page-wide.
- **(e) on the common durations:** year counts 1 to 5 and month counts 1, 2, 3, 6, 9, 12, 36 and
  60, each written in a key unknown, on the committed SMPL, WERN and VRRM pages.
  - They pass 13, 12 and 12 of 13 at main, and the same at this branch, even with refs excluded.
  - The pages' own prose states them: the consensus revision windows ("1m 0↑/0↓, 2m …, 3m …"),
    "12m → latest", "LTM 12 months", "a 3y window", "a clean 5 years".
  - So #1023's residual ("pass on every page") stands, now for spans the page STATES rather than
    names; the frozen pins show what the change removes.
- **Tests:** `tests/test_figure_trace_false_flags.py`, 17 nodes (13 fail on main's code) on the frozen SMPL
  and VRRM pages
  and `test_dossier._minimal_mech`.
  - The positive half of each item fails on main's code; each (−) half passes before and after.
  - (a): six metric words, plus round 0's "EBITDA and revenues". Negatives: a made-up value, and
    #1023's swapped values.
  - (b): "1.54x" against "1.5x" and "18.1%" against an "18%" cell. Negatives: "1.58x", "18.6%".
  - (c): "its 2045 financial targets". Negatives: "matures in 2041", "targets 2041".
  - (d): "fiscal 2024" against a January year end. Negatives: "fiscal 2025" refused there, "FY25"
    traced, and an August year end unshifted.
  - (e): "within 5 years" on a layer whose only five-year span is a field name. Negatives: "6
    months" on a ref's 180d, prose-stated spans, and a cited fact's own ref window. Also: no
    cited fact on the frozen VRRM page states a span over 50 years.
- **#1023's own files still pass** (`test_figure_trace_as_written.py`, `test_footnote_every_figure
  .py`, `test_untraceable_rank_and_duration.py`: 282 with this file). That includes "the trace
  only narrows, but for spans and years" on every committed point.
- **No synthesis request moves.** The trace reads the draw; it writes nothing the model is sent.
  The impact check (`python -m vinci.impact run`, base `c2934d07`, head `5050294d`, both sides
  built within one UTC day, VALID) agrees:
  - it built 27 of 27 pages, and 0 pages and 0 requests move;
  - the frozen panel differs on 0 of 6, so the row-53 panel check is not owed;
  - 13 of the 17 new tests fail with main's code and none with this branch's.
  - The $0 build carries no synthesis, so the flags above move only when a page is rebuilt.

**BOUNDARY.** The corpus is the 27 `data/dossiers/*/dossier.json` with a synthesis, at main
`c2934d07`, re-validated on 2026-11-12. "Flags" are `_validate`'s whole list, untraceable and
other. The durations table covers 13 written durations, in a key unknown, on three committed
pages.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A label year passes unread.** "the 2041 notes" or "its 2041 maturity" is no figure under (c),
  so a wrong year written as a label is not caught. A year claimed as a date is still traced.
  Falsifier: a rebuilt page whose label year is wrong.
- **A coarse unit-less fact widens a claim in any unit class**, at its own scale. PARR's "21.5
  (latest)" carries no unit, and the claim is dollars. Bounded by the old 2% / 0.05.
- **A metric no row carries widens its figure to the cited fact's whole period**, so a figure
  meets every row of the periods it names. Measured: no committed flag clears that way.
- **(e)'s residual stands as above.** Tightening it means binding a free field's duration to the
  fact it is about: a design, not this fix.

**NOT DONE.** The next build of each page prints the new caveats. No committed page is rebuilt
here.
