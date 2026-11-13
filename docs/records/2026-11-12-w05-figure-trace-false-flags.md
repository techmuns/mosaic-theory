---
id: 2026-11-12-w05-figure-trace-false-flags
status: shipped
date: 2026-11-12
prs: [1040]
supersedes:
superseded-by:
---

# The figure trace stops flagging four classes of correct figure (W05, the follow-up to #1023) — a metric word binds the row it names, a coarse print counts as the exact value the page states there, a year naming what it dates is no figure, and a field name, accession, URL or hash states no span; a fifth, a January year end's "fiscal 2025", is dropped in review round 1 because TJX and nCino name their years as CIQ does; on the 27 committed pages exactly two flags clear (PARR's "$21.54", VITL's "2030") and none is added

**WHAT.** #1023 made the synthesis figure trace read a figure as written (RG-D1 to RG-D7). Its
record (`docs/records/2026-11-11-figure-trace-as-written.md`, "WHAT IT COSTS") and its round-2
review named the false caveats left. All five are in `vinci/dossier/synthesis.py`. Review round 1
(below) narrowed four of them and dropped the fifth; this is what ships:

- **(a) A metric no row label carries.** `_claim_rows` bound a figure to the table metric written
  nearest it, and the metric written beside it was invisible when no row label carried that word:
  "revenues" (the row says "Revenue"), "net sales", "operating income" (an EBIT row), "capital
  expenditures" (a Capex row), "profit", "impairment" (an "Asset Writedown" row).
  - Each such word now names its row (`_ROW_SYNONYMS`): "revenues" and "net sales" Revenue,
    "operating income" and "operating profit" EBIT, "capital expenditures" Capex, "impairment" and
    "writedown" Asset Writedown.
  - A word naming no one row ("profit", "sales" alone, or a synonym whose row the table lacks) is a
    mention of none (`_OTHER_METRICS`): its figure meets the cited fact.
  - A list of k metrics, then k figures with no metric between, is read in order: "FY25 EBITDA and
    revenues: $262.3M and $1,450.9M".
  - A period carries past a figure of ANOTHER metric (`_bound_cells`): in "FY26 EBITDA was $8,425M
    while revenues were $64,031M", $64,031M is FY26's revenue. It never carries past a figure of
    the same row, which is a comparison ("rose from $1,331M to $1,451M in FY25"), nor across a
    word placing the figure in another period ("versus prior-year revenue", "a year earlier").
  - A synonym's word inside another row's longer name is that row's: "goodwill impairment" is
    the "Impairment of Goodwill" row, never "Asset Writedown" by its synonym "impairment".
- **(b) The fact's printed width.** The tolerance was the smaller of the claim's written width and
  the old 2% / 0.05, so a figure written one digit finer than the fact prints it was refused:
  PARR's "$21.54" against its consensus fact's "21.5 (latest)".
  - Each prose number and display cell keeps half a unit of its last printed digit and its unit
    class (`_prose_numbers_printed`, `_FactNumbers.halves`, `_Cell.half`).
  - Where the page states an exact value inside that width (a STRUCTURED number,
    `_FactNumbers.exact`), a claim inside the print traces only as that value, at its own width:
    PARR's "21.5" is the 21.54 its table and multiples carry. Where the page states none, the
    print's width stands.
  - A margin cell ("27%") is its table's own ratio, `<metric> ÷ revenue` from the table's
    structured rows, as `ciq_sheets` computes it (`_table_cells`).
  - It is never wider than the old bound, applies only at the scale the fact prints the number
    in, and only when the fact prints the claim's unit class or no unit. Without those two
    conditions two TRUE flags cleared: CNXC's "$375M term loan" met a two-decimal "0.37…" read at
    a thousand, and GOOGL's "interest coverage of 60.3x" met a "60%" gross margin.
- **(c) A year that names what it dates.** VITL's "management withdrew its 2030 financial targets"
  was traced as a figure, a year the page never dates.
  - A year after a determiner or a possessive and before a word is a label (`_ClaimFigure.named`),
    unless it precedes every year the page dates: TGT's "its 1987 stores" is a count.
  - "matures in 2041" and "targets 2041" are still traced (#1023's round-2 pin).
- **(e) A span only the code names.** A duration traced against every window the page named,
  including field names (`pe_percentile_5y`, `high_52w`), accessions and URLs (VRRM's
  "…/d123116d8k.htm" read as 123,116 days, a span of 337 years) and sha256 locators.
  - A field name labels its own fact's window only (`_FactNumbers.named_windows`), traced in a
    point citing that fact and never page-wide.
  - An accession states no span. A URL or a hash is cut out of the string before its spans are
    read (`_CODE_TEXT`), so the rest still states its own: BRBR's cadence ref "median 91d gap …
    https://…" states 91 days.
  - A ref's window ("EOD SMPL 180d", "39 quarters spanning … (9.5y)") stays a span the page states.
- **(d) DROPPED: a January or February year end.** W05 read every such filer's "fiscal 2025" as
  CIQ's FY26. That holds for Ross, Target and Burlington, which name a year by the year it STARTS.
  TJX and nCino name it by the year it ENDS, as CIQ does: TJX's 8-K 0000109198-26-000045 guides
  "Fiscal 2027" EPS of $5.31 to $5.36 against CIQ's FY27E $5.33, and nCino's guidance reads
  "Fiscal Year 2027 Ending January 31, 2027". So on those two pages a correct "fiscal 2026" was
  refused and a wrong "fiscal 2025" passed. "fiscal YYYY" is CIQ's FYYY on every page again, as
  on main. The class is OPEN (below).

**WHY.** A caveat that names a correct figure untraceable teaches the reader to skip caveats. These
were the classes #1023 left. PARR's and VITL's are live; (a) is latent on today's corpus; (e) let
any duration in a key unknown trace on the code's own names. Round 1's narrowing matters as much:
a relaxation that passes a WRONG figure removes the caveat the reader most needed.

**REVIEW ROUND 1.** Codex's review failed on its usage limit (2026-11-12 17:05Z). A's independent
review (`techmuns/mosaic-theory` #1004, issuecomment-6833102025, approved by the operator) stood in
for it. It ran constructed claims through the real `_validate` on the committed pages, at main and
at `7d512a7b`, and found:
- **(d) inverted TJX and nCino** (blocking). Above. This record's first version said TJX "calls
  that year 'fiscal 2025'"; that was false.
- **(a) silenced six true flags main had caught:** TJX "revenues were $7,178M" (EBIT's figure),
  EBITDA and revenue written swapped, "operating income was $8,425M" (EBITDA's), "capital
  expenditures were $3,892M" (FCF's), TGT "a $250M impairment" (restructuring's; the writedown row
  states 69), and TJX "FY26 … revenues were $64,031M" (FY27E's). A figure read as no row met all
  160 cells of TJX's table, every period. This record's first version said such a figure meets
  "the cited fact's whole period"; that was false. All six are flagged again.
- **(b) passed any figure inside a print's width though the page states the exact value:** NCNO
  FY27E EBITDA margin "26.6%" (the table's ratio is 27.15%), TJX "13.8%" (13.96%), PARR "$21.45"
  to "$21.55" (beside the page's 21.54). All refused now.
- **(b)'s unit-class condition had no pin.** Dropped, every test passed and GOOGL's committed
  "60.3x" cleared. Pinned now, on GOOGL's page.
- **(c) exempted any 1900–2099 number after a determiner:** TGT "its 1987 stores". Refused now.
- **(e)'s `_CODE_TEXT` had no pin and dropped the whole string:** BRBR's "median 91d gap" and LLY's
  "1095d scanned" lost their source. VRRM's fix came from removing the ref loop, not from it. It
  now cuts only the URL or hash, and is pinned on BRBR's page.
- **The rest held:** 17 of 17 tests at `7d512a7b`; 8 of 10 hand-applied mutants caught; flags 476
  → 474 on the corpus, PARR's a true clear; no synthesis request moves.
- **Then `/code-review high --fix` on round 1's change** found 8. Three were fixed in the same
  commit:
  - the "impairment" synonym took "goodwill impairment" from its own row, refusing TJX's true FY18
    goodwill impairment;
  - live-page expectations formatted the page's decimals where the claim printed a whole number;
  - a readability helper.
  A fourth was fixed after it: the carried period took FY26 onto "prior-year revenue", refusing
  TJX's true FY25 revenue. Each has a pin that fails on the code before its fix. A fifth moved
  the pins onto frozen copies of the real pages, since the pins read values that a rebuild
  re-draws. Of the other three, a list paired by count ("Revenue and EBITDA rose 9% to
  $60,372M") is flagged identically at main and `7d512a7b`, so it was not introduced here. The
  exact-value neighbours and the named-year floor are accepted below, measured.

**HOW VERIFIED.** All at $0.
- **The committed corpus, re-validated:** every committed synthesis and its layer through
  `_validate`, with main's code (`c2934d07`), with `7d512a7b`, and with round 1's code.
  - **476 → 474 flags, at both.** Exactly two clear against main: PARR's "21.54" and VITL's "2030".
  - **None is added**, and no flag differs between `7d512a7b` and round 1, per class.
  - (a) and (e) move no committed flag; nor did (d).
- **The review's 45 constructed claims, at round 1** (TJX, TGT, NCNO, ROST, BURL, WERN, PARR,
  VITL): every wrong figure of (a), (b) and the (c) count is flagged; every correct (a) and (b)
  figure traces; (d) reads as on main.
- **What two rejected designs did on the same corpus (round 0):**
  - The width at every scale and unit cleared CNXC's and GOOGL's true flags (above).
  - Taking refs out of the page-wide spans flagged five TRUE own-history spans: TGT's "9.2-year
    range", V's and WLK's "9.5-year", VRRM's "32 quarters" and CNXC's "5.7y". Each is a span the
    EV/EBITDA percentile fact's ref states ("39 quarters spanning 2017-03-31..2026-09-30
    (9.5y)"). It also cleared none of the common durations (below). So refs stay page-wide.
- **And one rejected in round 1:** taking every structured value in a print's width as an exact
  value it may trace to, without holding the claim inside the print, cleared three TRUE flags
  (CNXC "2.6", MCK "2.25", VITL "1.5"): a value at the edge of the print plus the claim's own
  width. A claim must lie inside the print.
- **(e) on the common durations:** year counts 1 to 5 and month counts 1, 2, 3, 6, 9, 12, 36 and
  60, each written in a key unknown, on the committed SMPL, WERN and VRRM pages.
  - They pass 13, 12 and 12 of 13 at main, and the same at this branch, even with refs excluded.
  - The pages' own prose states them: the consensus revision windows ("1m 0↑/0↓, 2m …, 3m …"),
    "12m → latest", "LTM 12 months", "a 3y window", "a clean 5 years".
  - So #1023's residual ("pass on every page") stands, now for spans the page STATES rather than
    names; the frozen pins show what the change removes.
- **Tests:** `tests/test_figure_trace_false_flags.py`, 34 nodes, on the frozen SMPL and VRRM pages,
  `test_dossier._minimal_mech`, and (round 1) the real TJX, TGT, NCNO, PARR, GOOGL, BRBR, WERN,
  ROST and BURL pages, frozen byte-identical from `data/dossiers/` on 2026-11-13
  (`tests/fixtures/frozen_pages/README.md`) ahead of the combined rebuild. Each claim is built
  from the page's own structured values.
  - Round 1: 12 nodes fail at `7d512a7b` and pass now; the three OPEN pins below XPASS there.
  - Round 1's mutants: each of its ten guards, removed by hand, fails a pin. That includes the
    print's scale guard, whose survivor was GOOGL's "$127.6B" against a "127,701" ($M) print:
    $127.7B, so a true flag.
  - Round 0's pins stand but two: "1.54x" against SMPL's "1.5x" is gone (the page's structured
    net-debt/EBITDA is 1.5 itself, and 1.54 traced only on an unrelated 1.5447), replaced by
    "$28.14M" against a "$28.1M" the page states no exact value for; and the (d) pins, which moved
    SMPL's dates to fake a January year end, are replaced by the real pages.
- **#1023's own files still pass** (`test_figure_trace_as_written.py`, `test_footnote_every_figure
  .py`, `test_untraceable_rank_and_duration.py`). That includes "the trace only narrows, but for
  spans and years" on every committed point.
- **No synthesis request moves.** The trace reads the draw; it writes nothing the model is sent.
  The impact check (`python -m vinci.impact run`, in the PR body) agrees. The $0 build carries no
  synthesis, so the flags above move only when a page is rebuilt.

**BOUNDARY.** The corpus is the 27 `data/dossiers/*/dossier.json` with a synthesis (2,201 claim
figures), at main `c2934d07`, re-validated on 2026-11-12 and again at round 1 on 2026-11-13. The
print count is every distinct (value, unit class, width) printed with a width in a cited fact of
those 27 pages, against each page's own structured values, at round 1's code.
"Flags" are `_validate`'s whole list, untraceable and other. The review's claims are 45, on eight
committed pages. The durations table covers 13 written durations, in a key unknown, on three
committed pages.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A label year passes unread.** "the 2041 notes" or "its 2041 maturity" is no figure under (c),
  so a wrong year written as a label is not caught. A year claimed as a date is still traced.
  Falsifier: a rebuilt page whose label year is wrong.
- **A count written as a year passes** under (c) when it is not before every year the page dates.
  The floor is that page's earliest dated year, 1990 to 2015 across the 27 pages, so "its 2019
  stores" passes. Falsifier: such a count on a rebuilt page.
- **A growth cell keeps its print's width.** A margin cell is its table's ratio; a growth cell's
  base column is stated only in its rendered text ("+8% (vs FY26)"), which the trace does not
  parse. Falsifier: a wrong growth figure inside its cell's half a percent on a rebuilt page.
- **The exact value is any structured value of the page inside the print**, related or not: a
  structured value carries no unit, and the one PARR needs sits in another fact. So a print whose
  width holds an UNRELATED value traces a claim equal to it (SMPL's survival "1.5x" holds the
  EV-gap ratio 1.5447), and refuses a correct finer figure the page states nowhere exactly, as
  main did. Measured: 6,907 of 23,775 distinct prints in cited facts (29%; 18% to 56% a page)
  hold a structured value inside their width. A print holding none keeps its width. All of it
  stays inside the print and the old bound. Falsifier: a correct finer figure refused on a
  rebuilt page.
- **A figure with no period beside or before it, or whose row another figure of the claim
  shares, meets every column** — #1023's rule, unchanged ("rose from $1,331M to $1,451M in
  FY25"). Falsifier: a wrong figure of another year inside such a comparison.
- **(e)'s residual stands as above.** Tightening it means binding a free field's duration to the
  fact it is about: a design, not this fix.

**OPEN: a January or February year end's "fiscal YYYY".** On Ross's, Target's and Burlington's
pages a correct "fiscal 2025 revenue" (CIQ's FY26) is flagged, and a wrong "fiscal 2026" passes,
as on main. No committed claim writes it: the committed syntheses on the five such pages write
CIQ's "FYxx", and the one "fiscal '26" (nCino's) is CIQ's year. Pinned as `xfail(strict=True)`.
What would read the convention, and why it was not built here:
- **The page states it, unevenly.** nCino's guidance headlines pair the label with the year end
  ("Fiscal Year 2027 Ending January 31, 2027"). TJX's and Burlington's guidance rows carry the
  label beside the filing date, and a guided year is the one in progress then. Ross and Target
  carry it only in CIQ's Key Development headlines.
- **That last premise breaks on Target's own page:** "Confirms Earnings Guidance for the Fourth
  Quarter and Full Year of 2025" (2026-02-10) names the year that had just ENDED. A read made right
  needs guards fitted to these same five pages.
- **And a claim's "fiscal 2026" may be either.** The model reads CIQ's table, whose columns say
  "FY26", and the company's text. A known convention does not say which the claim used; the cited
  fact would.

**NOT DONE.** The next build of each page prints the new caveats. No committed page is rebuilt
here.
## Amendments

- **2026-11-13 — the rejected round-1 design cleared FOUR true flags, not three** (W05 follow-up,
  the independent re-review of `40ae6410`). HOW VERIFIED says that letting a claim trace to any
  structured value inside a print, without holding it inside the print, "cleared three TRUE flags
  (CNXC "2.6", MCK "2.25", VITL "1.5")". That count was measured on an earlier variant, which
  compared signed values. The shipped code compares magnitudes. With the inside-the-print
  condition removed from it, the 27 committed pages lose four true flags, 474 → 470 at main
  `fd1c97f3` (measured 2026-11-13): those three and IT's "-1.5" in `decisive.against` ("Q1-26
  -1.5% YoY"). The condition now has frozen pins (SMPL's "32%" against a "33%" print, VITL's
  "16.8x" against "16.7x"; `test_a_claim_must_lie_inside_the_print_on_frozen_pages`), where only
  the corpus invariant on IT's living page caught its removal before.
- **2026-11-13 — (a)'s bare "sales" and "profit" are no longer a mention of no row** (the same
  follow-up). WHAT shipped "A word naming no one row ("profit", "sales" alone …) is a mention of
  none". Written bare, with no modifier before it and no noun after it, "sales" now names
  Revenue, and "profit" the profit rows (EBITDA, EBIT, net income), any of which it may mean. A
  qualified word or a compound ("sales leverage", "profit per share") still names none. TJX's
  "while sales were $7,178M" (EBIT's figure) had passed on the carried period. `_shares_row`, the
  comparison guard, is pinned as well, and now compares the rows themselves, each set less its
  rate variants. The rest is in `docs/records/2026-11-13-w05-followup-bare-sales-and-profit.md`.
