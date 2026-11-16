# covenant_exhibit_outcomes — frozen E5 outcome lists (STATE row 63)

`<T>.json` is the `covenant_exhibit_outcomes` value the REAL extraction loop
(`covenant_extract.extract_covenant_terms`, code of this PR) writes over `<T>`'s frozen pointer
rows in `tests/fixtures/covenant_unextracted/<T>.json`. One entry per located exhibit, in the
loop's order. EPAM, NCNO, AMZN and BURL.

**How it was made ($0, 2026-11-16, on main b64be6f1 plus this PR's code).**

- The loop ran unmodified.
- Each exhibit was read from the EDGAR cache, cache only. A cache miss raised, and nothing was
  fetched. None of these four pages missed.
- The model boundary was STUBBED from the committed page itself, and no model was called. For each
  exhibit the loop sent, the stub answered with one name-only row per committed term row citing
  that exhibit, and with no rows for an exhibit no committed row cites. Where the committed QA
  flags record an LLM error for an exhibit, the stub raised one; none of these four records one.
- So `extracted` and `no_terms_returned` here are the committed page's answers replayed, not a
  model run. `cost_bound`, `not_debt_agreement` and each `declared_title` are the loop's own
  decisions on the cached exhibit text.

**Checked against the committed record.** Every outcome agrees with the page's own
`(E5)` QA flags and term rows:

- EPAM: `0001352010-26-000015` refused, and its head declares no agreement.
- NCNO: `0001902733-26-000022` refused as an OFFICE LEASE.
- AMZN: `0001193125-18-139368` and `0001104659-26-072140` are past the cost bound.
- BURL: `0001193125-26-116001` refused; `0001193125-22-200058` and `0001193125-14-313404` are past
  the cost bound.

These are #1073's frozen cases. Over all 24 committed pages with pointer rows, the same run agreed
on 83 of 91 exhibits. Of the other 8, 5 were cache misses: MCK's 4 and WERN's 1. The other 3 are
FUBO's, whose 2026-08-18 page predates the identify-or-refuse gate.
