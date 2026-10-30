---
id: 2026-10-30-a-gap-between-two-digits-is-kept-in-the-span-check
status: open
date: 2026-10-30
prs: []
supersedes:
superseded-by:
---

# The verbatim-span check keeps a gap between two digits, so two figures no longer join into a third (audit G-D7)

**WHAT.**
- `vinci/verbatim.comparison_key` removed ALL whitespace. Between two digits that joined two
  figures into a third, so "Level 1 1.25%" and "Level 11.25%" reduced to the same key. A covenant
  quote stating a margin of 11.25% was VERBATIM in an exhibit printing 1.25%, and
  `rate_components` then kept the 11.25 it read from that quote as PRESENT.
- A whitespace run between two digits now reduces to ONE space, never to nothing. Every other
  run still folds away, including the spaces `html_to_text` puts inside a defined term or before
  a comma. The invisible format characters (soft hyphen, zero-width space and joiners, word
  joiner, BOM) are dropped first. So one inside a figure still folds away, and none can make a
  gap.
- One key, four consumers, all reading the same reduction:
  - `covenant_extract`: terms, rate-component clauses and the maturity event;
  - `graph/extract`: edge evidence;
  - `synthesis._traces` / `_values_by_ref`: citation keys (#859, G-D5);
  - `themes/exposure._cited_filing_text`: a fact ref with no accession.
- Extraction version `2026-10-30.G-D7` (Python table and its web twin), re-pinned.

**WHY.** The module forgives typography and spacing, nothing else. Its own furniture pin
(`test_page_furniture_is_not_forgiven`) names digits as where a figure would hide. Dropping the
space between two digit runs is not spacing: it writes a figure the document does not print. The real committed corpus
shows where it matters: conformed amendments print a struck figure beside its replacement.
- UBER: "$ 1,500,000,000 1,000,000,000".
- UBER: "June 13 April 4 , 2023 2027".
- AORT: "January 18, 2030 2031".
- NFLX: "$ 3,750,000,000, 6,000,000,000, and (b) 2.75 3.50 times".

The old key read each pair as one run of digits.

**HOW VERIFIED.**
- *Fails first on main.* Two pins fail on 9503c4fa and pass on this branch:
  - `test_a_space_between_two_digit_runs_is_not_forgiven`. On IT's real pricing grid (8-K
    0001193125-24-083467, from the SEC cache) the row with the ratio-to-fee gap closed is refused,
    and so is the audit's own case. The row as printed still matches, across a line break or a
    non-breaking space, and so does an elided quote. On UBER's real liquidity covenant the joined
    figure is refused and the committed quote kept.
  - `test_a_covenant_quote_joining_two_figures_is_refused_end_to_end`, through
    `extract_covenant_terms`: the joined quote gives UNKNOWN plus an (E5) flag and no margin; the
    printed one gives PRESENT with its margin.
- *A new real case.* UBER's committed liquidity quote, with its window, joins
  `tests/fixtures/verbatim/real_cases.json` as `uber-struck-figure-beside-its-replacement`. It
  was committed at 545403de and still is.
- *Mutants.* All three are killed by the new pins:
  - digit gaps dropped again (the bug);
  - invisible characters kept;
  - invisible characters counted as a gap.
- *Corpus before synthetic.* Every consumer was run on its committed corpus under the OLD key (as
  on main) and the NEW key (`scratchpad/d1/corpus_d1.py`). Nothing was sent: the primary
  checkout's SEC cache was read only, with 0 misses.

| consumer | population | old → new | flips | carrying a digit gap |
|---|---|---|---|---|
| covenant terms (PRESENT quotes) | 343 on 20 pages; 176 on the 13 in-scope pages (9 carry terms) | 220 verbatim / 113 elided / 10 not_found, both | 0 | 9, all still found |
| maturity event | 1 | 1 verbatim, both | 0 | 0 |
| rate-component clauses | 10 | 9 verbatim / 1 elided, both | 0 | 0 |
| graph edges | 339 on 75 focal names | 302 / 25 / 12, both | 0 | 1 (COHU), still found |
| synthesis citations | 605 against 4,139 layer refs | 580 cited / 25 uncited, both | 0 | 148 citations and 74 refs; 0 `_values_by_ref` keys split |
| exposure facts | 14,595 | key path never taken: 14,594 carry one accession, 1 carries two | 0 | — |

The 9 covenant quotes with a digit gap are the non-trivial case: each crosses a gap the new key
keeps, and each still matches. Four are the conformed figures above. Five sit in a pricing grid
or covenant schedule, where a ratio or date stands beside a figure: NFLX's grid, PARR's margin
grid and leverage schedule, and AORT's two leverage schedules ("Q4-2024 6.25:1.00").

**BOUNDARY.**
- Dossier pages: every committed `data/dossiers/*/dossier.json` at 9503c4fa outside the held
  test packs, 26 pages.
  - Covenant terms are each PRESENT `covenant_term_rows` value, read the way
    `scripts/audit_verbatim_corpus.py` reads it (the quote is the note's `verbatim: “…”`).
  - The source is the cited exhibit through `html_to_text`.
  - "The 13 in-scope pages" are the committed pages of the 14 names the narrowed rebuild keeps
    (STATE row 41; MCK has no page yet).
- Graph: `data/graph_coverage.json` at 9503c4fa. Each focal's 10-K is reconstructed as the latest
  filed on or before 2026-06-26, cut to `relevant_excerpts` (the audit script's default).
- Synthesis citations: bull and bear points, decisive evidence for and against, and each twin's
  source. The universe is every `source_ref` / `accession` / `url` in the page's `mechanical`.
- Exposure: every `disclosed_facts[].source_ref` in the 7 committed `data/scan_history/*/*.jsonl`
  files.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A quote that types as one figure what the document prints as two, split only by whitespace,
  is now refused. That is the fix. But `html_to_text` joins text nodes with a space. A filing
  that splits ONE figure across two tags ("1<b>2</b>50") would read "1 2 50", and a quote typing
  "1250" is refused.
- Not observed: 0 of the 693 quotes above flipped. The cost is a refused term, never a wrong
  one.
- Falsifier: an (E5) "the model's quote is not in" refusal at re-assembly whose exhibit splits
  the quoted figure across tags.
- No committed page moves, so none is added to STATE row 41.
