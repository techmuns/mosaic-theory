---
id:
status: open
date: 2026-11-10
prs: [961]
supersedes:
superseded-by:
---

# A covenant term's value states only figures its own quote states, in every class: whole dates, ratios, percents and unmarked amounts (TeamNostra fix request 2: RE2-D16, with E2-D19's residual). 24 more committed terms on 13 pages are withheld at their next re-assembly; none moves now

**WHAT.**
- **`covenant_extract.unstated_in_quote`, the deterministic fence around the covenant model step,
  now reads every class of figure a value states.** Each is compared in its own unit against the
  term's quote:
  - **a whole date:** day, month and year, in month-day-year, day-month-year or numeric form. A
    lone year is still checked as before.
  - **a ratio against one,** in any form. "4.50x" is "4.50 to 1.00", which is "4.50:1.00". A span
    such as "3 to 5 years" is not a ratio.
  - **a percent,** with basis points in the same unit ("175 bps" is "1.75%"). A 0% is stated by
    "zero".
  - **an unmarked amount,** read only where it is comma-grouped, scaled or carries three or more
    decimals. It is stated by any amount the quote states, marked or not. "Section 6.02", "3
    years" and "48.0" are not read.
- **A conformed copy's strike-and-replace forms are read in the quote.** Examples are BURL's
  "December 22 July 25 , 2026 2030" and NFLX's "(b) 2.50 2.75 times". This is the date and ratio
  analogue of #873's money replacement.
- **A rate component's own clause also counts as stated text for the value line**
  (`_quoted_clauses`), when it is a span of the exhibit, the same rule `rate_components` keeps a
  component by.
- **A value that states a figure its quotes do not is refused whole**, as #873 refuses one: a
  visible UNKNOWN whose note and (E5) flag name the figures.

**WHY.**
- **TeamNostra's re-audit (document 14, E2-D16) and V2's recheck of E2-D19 found that only years and
  currency-marked money were checked.** These stood PRESENT:
  - "5.00x" beside "4.50 to 1.00";
  - "2.50x" beside "3.00 to 1.00";
  - "Term SOFR plus 2.00%" beside "1.75%";
  - "July 25, 2030" beside "December 22, 2030";
  - "Commitments of 1,000,000,000" beside "$750,000,000";
  - "50.0000 shares" beside "45.4545 shares".
- **#873 deferred the percent class as a scope call** (STATE row 34; its record). RE2-D16 asks for
  it in order 3, and the operator approved this stream on 2026-11-10 ("go ahead").

**HOW VERIFIED.**
- **Fail first.** `tests/test_covenant_value_in_quote.py` was run in an export of `origin/main`
  `5e3def4a`: 9 fail and the negative pins pass. The 9 are:
  - TeamNostra's 6 constructed cases;
  - AMZN's committed grid percents and PARR's committed "June 5, 2023";
  - the old scope pin's first assertion. That pin was renamed: it kept "Term SOFR + 1.75%" beside
    "plus the Applicable Margin" as intended behaviour, and now pins its refusal.

  On this branch every `-k covenant` test passes.
- **Real text in the pins.** The value and quote pairs named per case are frozen literals copied
  from committed pages at `5e3def4a`. PARR's value is cut after its June 6 clause. The constructed
  pairs are TeamNostra's.
- **Two changed rate-component pins.** `tests/test_covenant_rate_components.py` used AMZN's
  committed 2020 row, whose value itself states the grid's 0.00% and 0.50%; the value is now refused
  before a component is read. Both mechanisms stay pinned. That value is refused, naming 0.50%. The
  same row with a figure-free value keeps its line and withholds both unquoted components, as before.
- **CORPUS FIRST: every PRESENT covenant term on the 27 committed pages.** That is 343 terms on 21
  pages; 22 carry component clauses. Each was run through main's guard and this branch's, reading
  the stored quote plus the stored component clauses:
  - main refuses 38. These are #873's, waiting on re-assembly (STATE row 41).
  - this branch refuses 62: **24 newly, on 13 pages, and 0 cleared.**
  - the 24 by class: 23 are a percent or bps figure, mostly a pricing grid's levels, a SOFR
    adjustment or a floor read from another clause, plus pledge percentages and a 1.00% repricing
    premium. The other is PARR's "June 5, 2023" against a quote stating June 6.
  - by page: BURL 2, CNXC 2, EPAM 1, FUBO 1, IT 4, MCK 1, NCNO 2, NKE 2, PARR 2, SMPL 2, UBER 1,
    VRRM 1, WERN 3.
  - I read each of the 24, and in each the figure is absent from every quoted clause. The values
    are most likely correct facts read from other clauses, as #873's 29 were. The check proves
    reading, so a figure no quote states is withheld.
  - **No false refusal survived the corpus:**
    - BURL's conformed maturity date and NFLX's struck 2.50 → 2.75 times are kept;
    - NCNO's and CNXC's ratios before a full stop are kept;
    - NFLX's "Sections 6.01, 6.02 and 6.04" are not read as figures.
- **Code review, round 0 (`/code-review high --fix`).** Six fixes, each pinned:
  - an unmarked amount followed by a comma ("500 million, which …") is read;
  - a fraction percent ("5 1/4%") is 5.25%, never a "4%". MCK's real "50%/0%" stays two
    percents;
  - a date with no space after its comma ("December 22,2030") is read;
  - the quote and the component clauses are joined by " | ", so no strike, replacement or range
    reader crosses from one clause into the next;
  - the quote's money is read once;
  - **a withheld component's clause vouches for nothing.** The value may take figures only from
    the clauses of components the term KEEPS, which are the clauses the page stores
    (`component_quotes`). Before, the page could cite a clause it never keeps.

  None of the six moves a corpus refusal: still 62 refused, 24 newly, on the same 13 pages.
  Deferred as rarer forms the readers do not yet take: a struck percent ("1.50 1.75%"), a
  same-year struck date, "2 times per year" read as a ratio, and an ISO date.
- **Codex, round 1 (two P2).** Two fixes, each pinned on a test that fails on `a94c18d7`:
  - an unmarked amount with an abbreviated scale ("1.5bn", "500MM") is read at its scale;
  - a percent or ratio in the quote ("1.750%") is no unmarked amount, so it no longer states a
    value's "1.750 shares".

  The corpus result is unchanged: 62 refused, 24 newly, on the same 13 pages.
- **The version.** Row `2026-11-10.covenant-value-figures`, in both tables, re-pinned.

**THE PANEL CHECK, PREPARED AT $0 (coordinator 2026-11-10: "ready the panel registration … Draw
nothing").**
- **The transform.** `vinci/evals/variants.py` gains `covenant_value_figures` (`RE2_D16`). The
  capture hands the synthesis the layer before the term rows are attached
  (`capture_child.pre_synthesis_mech`), so what this change moves in the REQUEST is the
  `covenant_terms` digest the assembly builds from the rows. The transform:
  - re-runs the ref's own fence on the page's stored rows (`fenced_covenant_rows`);
  - rebuilds the digest by the assembly's own composition where a row moved;
  - never attaches the rows.
- **It is not the identity at main, by design.** Main's own fence (#873) withholds 7 BURL and 5
  CNXC terms committed before it, so the base request is main's builder, the candidate's is the
  branch's, and their difference is this change alone.
- **The $0 equality is pinned** (`tests/test_evals_covenant_transform.py`). For every PRESENT quoted
  term on BURL, CNXC, MCK and SMPL, the transform's row is the row `_extract_from_exhibit` writes for
  the same stored answer.
- **`python -m vinci.evals compare --base origin/main --cand claude/fixreq2-covenant-guard
  --transform covenant_value_figures`**, on the frozen panel:
  - CNXC differs by 5 lines (−117 characters of `user.facts`): its governing "Interest / coupon
    rate" line leaves the digest;
  - SMPL differs by 5 lines (−147): its interest line and an "amended by" annotation leave the
    digest;
  - BURL, LLY, MCK and ROST are IDENTICAL. The terms the fence newly withholds on BURL (2) and
    MCK (1) are not the governing ones.
- **Cost estimate.** The panel whole is 6 pages × 5 draws × 2 refs = 60 draws. #941's run of that
  design cost $27.50 of a $35 cap, with requests of the same size (about 513k characters of user
  facts on SMPL). So about $28, cap $35. A no-worsening registration has no target this change
  aims at; it would show whether withholding grid percents worsens any class metric on CNXC and
  SMPL. Nothing drawn, nothing registered: registration pins `origin/main` and the branch head, so
  it is written when the operator sets the cap.

**BOUNDARY.**
- **Terms:** every `covenant_term_rows` entry whose value is PRESENT with a stored `verbatim: “…”`
  quote, on `data/dossiers/*/dossier.json` at `5e3def4a`. That is 343 terms on 21 pages; 6 pages
  carry none.
- **Unit:** one term. A term refused for several figures counts once.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **24 PRESENT terms on 13 pages become UNKNOWN at each page's next re-assembly.** 18 of them are
  interest or coupon lines whose structure ("Term SOFR plus the Applicable Rate") is lost with the
  grid levels beside it. Each page prints the refusal lead "its value could not be verified against
  the filing, so it is withheld" and names the figures. Nothing moves on a committed page now: the
  guard runs only beside the model step.
- **This changes the synthesis REQUEST at re-assembly.** `covenant_term_rows` is sent to the
  synthesis; it is not in `NOT_SENT`. Of the frozen panel (BURL, CNXC, LLY, MCK, ROST, SMPL),
  BURL 2, CNXC 2, MCK 1 and SMPL 2 terms move. **The six-page panel check (RUNBOOKS §n) is
  PROPOSED, not run.**
  - It needs a $0 transform in `vinci/evals/variants.py` that re-applies `unstated_in_quote` to each
    stored PRESENT row.
  - Then `compare` at $0, and a paid no-worsening run on the operator's approval: about $28–35, from
    #941's 60-draw panel run at $27.50 of $35.
  - Nothing paid was spent.
- **A $0 refresh of the committed pages would need a new writer.** The guard is a function of the
  stored value and quote alone, so re-applying it is deterministic. No layer-refresh writer does it
  today, and adding one means editing `LAYER_REFRESH_WRITERS` in the hook-guarded `schemas.py`.
  Proposed, not built. #873's 38 refusals wait on re-assembly the same way.
- **Accepted, with its falsifier: a figure stated in words is not read.** "four and one-half to one"
  and "one hundred percent" are examples. A value writing the figure in digits beside such a quote is
  refused. *Falsifier:* a re-assembled page whose refused term's quote states the figure in words.
