---
id: 2026-10-30-a-covenant-value-states-only-what-its-quote-states
status: shipped
date: 2026-10-30
prs: [873]
supersedes:
superseded-by:
---

# A covenant term whose value states a year or a dollar figure its quote does not is refused (audit E2-D19)

**WHAT.**
- **The defect.** #804 proves a covenant term's QUOTE is a span of its exhibit. The VALUE the model
  writes beside it was never compared with that quote. The audit's stub stored "June 15, 2031"
  PRESENT beside a quote reading "June 15, 2030".
- **The rule.** `covenant_extract.unstated_in_quote(value, quote)` lists each year and each
  dollar figure the value states that the quote does not. When it lists any,
  `_extract_from_exhibit` refuses the term: UNKNOWN, with a note opening
  `VALUE_REFUSED_NOTE_PREFIX` ("(E5) refused: the value states …"), and an (E5) flag naming the
  figures.
- **What counts as stated.** Figures and years are read with the existing parsers; no new figure
  grammar:
  - `release_parse.quoted_figures` reads the value's dollar figures, and `figure_stated` checks
    each at either scale ("$1.5 billion" is "$1,500,000,000"). Both are called, not edited.
  - A year is four digits from 1900 to 2099 standing alone, in any date form ("6/30/2029" is
    stated by "June 30, 2029").
  - **A conformed replacement is stated.** A conformed amendment prints the new figure right after
    the struck one, with no "$" of its own: UBER's "$ 1,500,000,000 1,000,000,000", NFLX's
    "$ 500,000,000 . 750,000,000". Without this rule, three committed values that read the
    replacement correctly would be refused.
  - A bare number that follows no dollar figure is not a dollar figure.
- **Scope.** A percent or bps figure is NOT checked: rate components have their own check
  (`rate_components`, STATE row 34). The span check runs first, so a quote that is not in the
  exhibit keeps its own reason.
- **The page lead.** It is a refusal, so a LATER exhibit withheld this way still withholds an
  older value (`governing_terms`, unchanged). The lead (`render._refused_newer_text`, dossier.js
  `refusedNewerText`) no longer says that refusal's "quote could not be matched", because it was
  matched. It reads "its value could not be verified against the filing, so it is withheld". A
  quote refusal's sentence is byte-identical to before.
- **The maturity event** (`extract_maturity_event`) needs nothing: its value IS its verbatim,
  whitespace-collapsed, so it cannot state what its quote does not.
- **Version.** Extraction version `2026-10-30.E2-D19` (Python and dossier.js), re-pinned.

**WHY.** A value is source-bound only through its quote: the note on the page reads
`verbatim: “…”`. A figure the value adds is the model's sentence. It may have been read from
another clause, but nothing on the page shows which one.

**HOW VERIFIED.**
- *Fails first on main* (8e6b12b1), in `tests/test_covenant_value_in_quote.py`. Every case is a
  model answer stubbed through the real `_extract_from_exhibit`, with frozen value/quote pairs
  copied from committed pages. Seven cases fail on main:
  - the audit's 2031/2030 stub;
  - AMZN's sublimit;
  - V's added "2013";
  - a bare 1,000,000,000 that is not money;
  - a quote refusal keeping its own reason;
  - the collapse lead;
  - the end-to-end NKE page, in Markdown and on the production web renderer.
- *Seven positive pins pass on both main and this branch:*
  - three committed conformed amendments (UBER liquidity, two NFLX rows);
  - three scale or date-form variants;
  - the percent scope pin.
- *The existing pins are unchanged.* `tests/test_covenant_refused_newer.py` still passes: the quote
  refusal's wording and the Python↔JS collapse parity hold on every committed page.
- *Corpus before synthetic.* `unstated_in_quote` ran over every committed page outside the held
  test packs at 8e6b12b1:
  - **29 of 176** PRESENT terms on the 13 in-scope pages, on **9 pages**: AMZN 7, CNXC 5, NFLX 3,
    NKE 3, PARR 3, UBER 3, V 3, SMPL 1, TJX 1. Two are maturity rows (CNXC, V).
  - 35 of 167 on the 13 other non-held pages, on 10 of them. Those are not rebuilt (STATE row 41),
    so they keep their values.
- *Every unquoted figure was set against its whole exhibit,* read from the SEC cache: **0 of the
  29 terms carries a figure absent from its exhibit.** Each was read from another clause, such as
  a currency sublimit or a prepayment threshold, and attached to a quote that does not state it.
- *Through `governing_terms`,* simulated on those committed rows: 26 governing values become
  UNKNOWN. 3 groups gain the later-refusal lead: NFLX's revolving credit agreement, and UBER's
  term loan agreement twice.
- *The preview the PREVIEW rule requires.* NKE's real page with its later refusal rewritten as a
  value refusal, rendered on main and on this branch. On main the lead says "its quote could not
  be matched". On the branch it says "its value could not be verified against the filing". The
  Markdown and the web agree, both in the main-body line and in the appendix row, which sits in
  `<details>` and so prints expanded.

**The 29 terms**, each `<page> · <term> · <exhibit> · what its quote does not state`:
1. AMZN · Principal / commitment amount · 0001104659-23-113444 · $5,000,000,000
2. AMZN · Mandatory prepayment / events of default · 0001104659-23-113444 · $1,500,000,000
3. AMZN · Principal / commitment amount · 0001193125-20-176528 · $3,000,000,000
4. AMZN · Mandatory prepayment / events of default · 0001193125-20-176528 · $1,000,000,000
5. AMZN · Principal / commitment amount · 0001018724-14-000042 · $1,000,000,000
6. AMZN · Mandatory prepayment / events of default · 0001018724-14-000042 · $500,000,000, $1,000,000,000
7. AMZN · Negative covenant - Liens · 0001018724-14-000042 · $250,000,000
8. CNXC · Principal / commitment amount · 0001803599-25-000111 · $750,000,000, $250,000,000, $500,000,000, $75,000,000
9. CNXC · Maturity date · 0001803599-25-000111 · 2028, 2026
10. CNXC · Mandatory prepayment / events of default · 0001803599-25-000111 · $250,000,000
11. CNXC · Principal / commitment amount · 0001803599-23-000107 · $294,702,380.98
12. CNXC · Principal / commitment amount · 0001803599-21-000215 · $2,100,000,000
13. NFLX · Mandatory prepayment / events of default · 0001193125-21-193187 · $250,000,000
14. NFLX · Principal / commitment amount · 0001193125-25-327462 · $200,000,000
15. NFLX · Mandatory prepayment / events of default · 0001193125-25-327462 · $250,000,000
16. NKE · Mandatory prepayment / events of default · 0000320187-25-000008 · $200,000,000
17. NKE · Mandatory prepayment / events of default · 0000320187-24-000009 · $200,000,000
18. NKE · Mandatory prepayment / events of default · 0000320187-26-000020 · $200,000,000
19. PARR · Financial-maintenance covenants · 0001193125-15-116573 · 2016, 2017, 2018, 2019
20. PARR · Mandatory prepayment / events of default · 0001193125-15-116573 · $2,500,000
21. PARR · Financial-maintenance covenants · 0001193125-14-392228 · $1,000,000
22. SMPL · Financial-maintenance covenants · 0001104659-19-060856 · $100,000,000
23. TJX · Mandatory prepayment / events of default · 0000109198-25-000033 · 2030
24. UBER · Mandatory prepayment / events of default · 0001552781-22-000307 · $150,000,000
25. UBER · Principal / commitment amount · 0001552781-23-000109 · $2,511,000,000
26. UBER · Mandatory prepayment / events of default · 0001552781-23-000109 · 2021, $350,000,000
27. V · Principal / commitment amount · 0001193125-13-032823 · $5,000,000,000
28. V · Maturity date · 0001193125-13-032823 · 2013
29. V · Mandatory prepayment / events of default · 0001193125-13-032823 · $150,000,000

**THE BRIEF SAID 27; THIS MEASURES 29.** The brief's count came from a re-verification whose
method is not on file. Seven pages match it exactly. AMZN measures 7 against 6, and PARR 3
against 2; PARR's third term is a capital-expenditure cap of exactly $1,000,000. The brief's
"two are maturity rows" holds. This record trusts the measurement and names every term.

**BOUNDARY.**
- **Committed corpus:** `data/dossiers/*/dossier.json` at 8e6b12b1, excluding the held test packs.
- **In-scope pages:** the 13 committed pages of the 14 names the narrowed rebuild keeps
  (STATE row 41; MCK has no page). 9 of them carry PRESENT terms.
- **What was checked:** each PRESENT `covenant_term_rows` value against the quote in its
  `verbatim: “…”` note.
- **Exhibits:** each term's source exhibit read through `html_to_text` from the primary
  checkout's SEC cache; 0 requests were sent.
- **The percent class:** run with the same rule extended to percent and bps figures.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **29 values most likely read correctly are withheld at re-assembly.** All their figures are in
  the exhibit. This is #804's trade one step further: the page shows a value only where the words
  beside it state it.
  - The cost lands on principal rows (9), prepayment and default rows (14), financial-maintenance
    rows (3), maturity rows (2) and one liens row.
  - On principal rows the commitment the quote DOES state is withheld with the sublimit it does
    not.
  - Falsifier: a re-assembled page whose principal or maturity UNKNOWN hides a figure the
    operator needs. The remedy is a second quote per figure, the way `rate_components` keeps a
    component's own clause, not a looser check.
- **DEFERRED — the percent class.** Extending the rule to percent and bps figures would refuse 13
  more terms on the same 13 pages: 42 against 29. Most are interest and fee rows whose value lists
  a pricing grid the quote does not print. Those overlap STATE row 34, whose rate components
  already carry their own clause. Whether a value's grid percentages must be quoted too is a
  scope call for the coordinator.
- **Not rebuilt here.** No committed page is touched; the change lands at re-assembly
  (STATE row 41).
