# Frozen covenant rows and exhibit clauses for the rate-component pins

`tests/test_covenant_rate_components.py` reads these. They track NO page.

- `rows.json` — every covenant term row on the 27 committed pages that carries a structured rate
  component (`margin_pct`, `margin_bps`, `floor_pct`, `pik_pct`), as committed at main 1114490b
  (2026-10-28), with each page's `covenant_pointer_rows`: 36 rows on 17 pages, 48 components. These
  ARE the model's output: the components and the quote each row stores are what the extractor
  received and kept.
- `*.txt` — a window of one real exhibit's text, as `vinci.graph.filings.html_to_text` gives it
  and single-spaced, from 300 characters before the clause to 1,500 after; cut from the shared SEC
  cache:

| file | exhibit | clause |
|---|---|---|
| `AMZN-2020-applicable-rate.txt` | 8-K 0001193125-20-176528 · d948849dex101.htm | “Applicable Rate” — 0.50% for Eurocurrency Rate Loans |
| `AMZN-2020-interest.txt` | 8-K 0001193125-20-176528 · d948849dex101.htm | Section 2.08: the LIBO Rate “plus the Applicable Rate” — the quote AMZN's committed row stores |
| `AMZN-2020-screen-rate.txt` | 8-K 0001193125-20-176528 · d948849dex101.htm | “Screen Rate” — less than zero is deemed to be zero |
| `AORT-2025-adjusted-term-sofr.txt` | 8-K 0000784199-25-000145 · ex101.htm | “Adjusted Term SOFR” — floored at two percent (2.00%) |
| `NCNO-2024-pricing-grid.txt` | 8-K 0001902733-24-000171 · exhibit101creditagreementb.htm | the Applicable Rate grid — 2.00% / 2.25% / 2.50% by leverage |

- `real_run_2026-10-28.json` — the interest term rows this branch's extractor wrote on 2026-10-28
  from a REAL model call (`claude-opus-4-8`) on AMZN's, BRBR's and NCNO's exhibits above (the full
  cached exhibits, one call each), as `CovenantTerm` JSON: AMZN's margin and floor and BRBR's and
  NCNO's floors kept by a clause of their own, NCNO's grid margin withheld. Frozen, never re-drawn:
  a fresh call words its `value` differently.
