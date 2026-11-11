---
status: open
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# Fix request 2, order 4 (RG-D1 to RG-D7, and B's fix 5): the synthesis figure trace reads a figure as written — its printed sign, its unit, its width, the period and metric it names — and traces every field and every call; each of the audit's constructed replies now fails, random dollar figures trace against the annual table 7.0% of the time where they traced 78.3%, and the panel metrics' inputs do not move

**WHAT.** `synthesis._validate`'s number trace (the check that a figure a synthesis writes is a
figure of the fact it cites). Audit G-D1 to G-D7 (`fixpack2/notes/G.md` §5), the fix request's
RG-D1 to RG-D7. Order 4's "done when": each constructed reply in the G notes fails the check it
should, and random dollar figures no longer trace against the annual table at anything like 78%.

1. **RG-D1, the sign.** A sign printed before a figure ("+29%", "-$5M", "(−24%") must be the
   fact's. The fact's sign is what IT prints: a minus, ASCII or "−", in its text
   (`_prose_numbers`, the one reader of a fact's prose numbers); a structured value's own sign; a
   transcript figure's `change` word ("down 7%" is −7). A number whose sign the fact does not state
   (prose "a loss of $156M"; a transcript figure with no `change`) is never checked against a
   claimed sign (`_FactNumbers.unsigned`). A hyphen after a digit or a letter is a range or a name
   ("8-15x", "5-10%"), never a minus — the old trace read "5-10%" as −10. A sign carried in words
   ("fell 24%") is not read; an unsigned figure is compared on magnitudes as before.
2. **RG-D2, the unit.** A "%" traces at the fact's percent or fraction (scales 1, 1e2); an "x" at
   scale 1; a "$" at a power of a thousand, never 1e2; basis points at 1, 1e2, 1e4; a figure with
   no unit keeps all nine scales. A table row that states an amount ("Revenue ($M)") is read at the
   scale word the figure writes ("$1.5B" is $1,450.9M; "$1.5M" is not); a per-share row at $1; a
   rate row (a growth, a margin) is no amount; a "/sh" row is dollars per share, like EPS. A "$979" with no scale word may be the table's own
   unit (VRRM's "FY27E revenue is $873M versus FY25 $979").
3. **RG-D3, the period and the row.** A financial table (`FinTable`) is no longer one bag of 315
   numbers: each cell keeps its row's metric and its column's period (`_Cell`). A claim's figure
   meets only the cells of the periods it names ("FY25", "FY2025", "fiscal 2025", "LTM",
   "trailing twelve months", "Q2-26", "Q2 2026", "2Q26") and the rows it names (by content word in
   any order, so "goodwill impairment" names "Impairment of Goodwill"; "net loss" names net income;
   "EBIT" is not in "EBITDA"), each where the table HAS one. A named metric brings its own rate
   rows ("revenue" brings "Revenue growth"). A period binds only the figures written beside it,
   with no other figure between them: in "rose from $1,331M to $1,451M in FY25", FY25 binds the
   $1,451M and leaves FY24's $1,331M to every column. A period the table lacks restricts nothing.
4. **RG-D4, the width.** A figure is matched within the SMALLER of half a unit of its last written
   digit and the old tolerance (2%, at least 0.05). So the change only removes passes: "$0.04" is
   no target of ~0; "$1,479.0M" is not $1,450.9M; a coarse "15%" keeps the old 2%.
5. **RG-D5, a duration (closes STATE row 45).** "47 months", "95 days", "a 5-year window" were
   calendar labels the trace never read. A duration is a figure in its time unit now, traced as a
   span a fact of the PAGE states: a number in a field its name times (`window_span_years`), or a
   window a ref, a field name or the code's own text names ("180d", `pe_percentile_5y`, "~1.7y",
   "DTC 8.8d"), at its written width alone (a span is specific: "the band spans ~9y" is the page's
   8.8 years). Never a table cell, nor a number of no stated time unit read at every unit. A bare
   year ("capex for 2027") traces as a year the page dates something in.
6. **RG-D6, the fields that cite nothing.** A figure in a key unknown, the decisive question or
   the evidence balance is traced, as written, against everything the page states — every fact,
   and the notes and caveats beside them — and flagged `UNTRACEABLE figure 'N' in key_unknown [on
   no fact of the page]`, a shown caveat. (B's **fix 5**, "every claim bound to a fact the page
   carries", is delivered at the FIGURE level by items 3, 6 and 7: every figure of every field is
   bound to a fact the page carries. A claim's qualitative assertion is not bound by any check; that
   is not built.)
7. **RG-D7, a figure cited to a call.** The instruction says no number is read from a call's text;
   the check gave a call-cited figure a hidden `TRANSCRIPT-FIGURE` note. A figure cited to a call
   OF THE PAGE now traces to that call's VALIDATED figures (its driver rows' `figures`, which
   `_values_by_ref` holds under the call's ref), and one none of them states is `UNTRACEABLE figure
   'N' in <where> [from the call <ref>]`, a shown caveat; the point keeps `cited=True`. A
   computed figure with such an input is UNDERIVED. `TRANSCRIPT-FIGURE` is no longer emitted (the
   QA list keeps it, for the flags old pages store).
8. **The panel's instrument does not move.** `evals.metrics` finds figures through
   `synthesis._claim_figure_ends` and reads `_stated_numbers`' years and ranks. Both are unchanged:
   `_claim_figure_ends` is a filter over the new reader that returns what it returned before (it
   still skips the old labels and reads a match's hyphen as a sign).

**WHY.** The trace compared magnitudes (`abs`) at nine scales within 2% or 0.05 of anything the
cited fact's whole subtree states, so a wrong sign, unit, period or row passed whenever some number
of the fact was near at some scale — and a table with 315 numbers is near almost everything. The
audit reproduced each on the frozen SMPL page; every one passed unflagged.

**HOW VERIFIED.**
- **The audit's constructed replies** (`demo_synthesis_checks.py`, on the frozen SMPL page): all 14
  are shown caveats here. Before, 1 of 14 was (the made-up ref), the call figure was a hidden note,
  and 12 passed unflagged. Pinned one by one, each beside the correctly written fact, which must
  trace (`tests/test_figure_trace_as_written.py`).
- **The trace rate** (`demo_trace_rate.py`): 2,000 random "$<x>M" figures cited to the annual
  table, which names no period or metric: 1,567 traced (78.3%) before, 141 (7.0%) here — each a
  1-dp figure EQUAL, as written, to one of the table's amounts. The one-number fact: 49 → 0.
- **The untraced fields** (`demo_untraced_fields.py`): the three figures are flagged, each naming
  its field.
- **The committed corpus, re-validated** ($0: each committed synthesis through `_validate` at the
  base and at this tree; 27 pages). See BOUNDARY for the counts. Every figure newly flagged was
  read against its cited fact and classed (the record's scratch tools: `classify.py`,
  `nearest.py`). They are, by class:
  - **a call figure none of the call's validated figures states** (53 flags; the 37 hidden notes
    re-routed, and 16 more) — WLK's "$600 million" improvement and "$201M", PARR's "$500M"
    notes, UBER's "net-debt/EBITDA of 0.5x", EPAM's "~57% of revenue", AMZN's "within 5 to 10
    years", GOOGL's "over the next 24 months": figures read from the call's text;
  - **a near-miss of the right number** — GOOGL's Q3 revenue "$127.6B" where the fact states
    $127,701M; PARR's FY26E EBITDA "$1,333.5M" where it states $1,332.1M; "15.9x" for 16.0x;
  - **a number of another fact, met only by coincidence before** — MCK's "$7,455.6M" levered FCF
    cited to a ref stating EBITDA $7,350M (1.4% off); IT's "-24% over 52 weeks" cited to a fact
    whose only 24 is the benchmark's +24%; LLY's "-0.9%" share change cited to a 0.9x leverage
    fact; WLK's "-$2,100M" segment loss met as a −21 restructuring charge at scale 100; MVST's
    "$128M" cash met as 1.3 at scale 100; WLK's "LTM ROIC of only 1.0%" met as FY27 revenue
    growth in an annual table that has no ROIC;
  - **a duration no fact of the page states** — VRRM's "7-year Avis contract", WERN's "within ~18
    months" (a maturity distance the model computed), and the three in key unknowns ("101 days
    stale", "219 days old", TECX's "24-week efficacy result");
  - **a figure no fact of the page states, in a key unknown** — GOOGL's "$924B" purchase
    commitments and CNXC's "$375M term loan" (searched in each layer: absent).
- **The false caveats found on the corpus, and fixed before this record** — each class seen on a
  committed page and closed: a fact's Unicode minus read as a plus (LLY, MVST); a transcript
  figure's "down" ignored (CNXC's "-3% to -5%"); a fact's unsigned prose number taken as positive;
  "8%ile" read as a percent; a "$979" with no scale word held to raw dollars; "net loss" and
  "goodwill impairment" not naming their rows (SMPL, VRRM); a duration traced at five time units
  against any number (NCNO's "2.3y" met its 27.8x multiple as 27.8 months); a span stated in another
  fact of the page ("the 52-week high", "over ~1.7 years"); a 5-year window on a field whose value
  is UNKNOWN; key unknowns quoting the page's own notes ("only 95 points, below the 450 floor");
  bare years ("in 2027") met only by the old 2% at scale 1,000.
- **The change only narrows, but for spans and years**: a phrasing-free test re-states the old rule
  and asserts, on every committed point, that each figure tracing now traced then too, but for a
  duration or a bare year (`test_on_every_committed_point_the_trace_only_narrows_but_for_spans_and_
  years`). Five flags clear on the corpus, all of that kind: four decimal durations that are spans
  the page states, cited beside another fact (NCNO's 2.3y, SMPL's 8.8y and V's 9.5y own-history
  spans; MVST's ~1.7y share-count trail), and EPAM's year 2023.
- **The panel metrics' inputs are byte-identical**: `_claim_figure_ends` and `_claim_figures` give
  the same output at base and here on all 998 texts the committed syntheses write (27 pages and
  the frozen fixtures) plus 12 edge cases; `_stated_numbers`' years and ranks are the same on all
  36 layers.

**BOUNDARY.**
- **The corpus counts:** the 27 committed `data/dossiers/*/dossier.json` with a synthesis, at
  `6fe06f1c` (PR 3's head, the base); each page's committed synthesis and layer re-validated by the
  base code and by this tree's code, on 2026-11-11. Flags: 447 → 476; shown caveats 314 → 380;
  UNTRACEABLE 296 → 362; TRANSCRIPT-FIGURE 37 → 0. Added 82 (53 call figures, 26 point figures, 3
  key-unknown figures); removed 53 (the 37 transcript notes, each re-routed as a call figure; 11
  untraceable flags reworded — the figure now carries its printed sign, or a range's end is no
  longer negative; 5 cleared, listed above). Flags move on 24 of the 27 pages. A COMMITTED page's
  stored flags do not change until it is rebuilt: these are what the next build prints.
- **The demos:** the frozen SMPL page (`tests/fixtures/frozen_pages/2026-08-18/SMPL`), the audit's
  seeds (20261109, 2,000 figures log-uniform on [1, 100,000] at 1 dp).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **More caveats on rebuilt pages:** 66 more shown untraceable figures across the 27 pages, about
  2.4 a page. Each class above was read; the residual false caveats found are two, both accepted:
  GOOGL's "capex rising to -$159,804M" (an outflow written negative against a fact stating capex
  positive — a sign convention, 2 flags) and WLK's "revenue growth -0%" (a whole-percent zero for
  −0.3%, which the old 2% bound refuses). FALSIFIER: an operator reading the next rebuild's caveats
  finds a class of correct figures flagged that is not one of these two.
- **Residuals, not built:** a sign in words ("fell", "a loss of") is not read — MATERIAL-DIRECTION
  covers the material figures; a duration that equals ANY window the page names passes (a page
  names some 30 to 44, and a lowercase "12m" or "3d" in a fact's prose is read as one), so a
  made-up "6 months" passes wherever the page prints "(6m)" — the pre-PR review's finding 6,
  accepted because the old rule passed every whole-number duration unread; a table cell parsed
  from its display string counts as signed (harmless while every negative cell prints a minus —
  the review's finding 7); a period the table lacks restricts nothing; a qualitative claim is
  bound to no fact (fix 5 is delivered for figures only); a table's display cells without a
  structured value (the growth and margin rows) are read from their strings, as before.
- **B's fix 2** (sign, unit, period and basis on every figure the synthesis INPUT digests print)
  changes the request, and so needs a paid panel check: not in this change.
