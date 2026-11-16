# Covenant coverage-rule fixtures (STATE row 63)

`<T>.json` holds one committed page's covenant inputs, for `tests/test_covenant_coverage_rule.py`:

- `capital_structure` is the page's `mechanical.capital_structure`, unmodified, from
  `data/dossiers/<T>/dossier.json` at main `51784e53` (2026-11-16). That covers its pointer rows,
  its CIQ panel instruments and its maturity check, whose `bound` is the page's reference date.
- `texts` maps `"<accession> · <exhibit>"` to the text of every exhibit the loop targets
  (`covenant_extract._core_agreement_exhibits`). Each is a CUT of the real document.

Pages: AMZN, BURL, CNXC, NFLX, NKE, TJX and VRRM, the seven whose sends the rule moves or whose
reader branch a pin needs. Public SEC filings, not licensed data.

**How each text was cut ($0, 2026-11-16, cache only).**
- The exhibit was read from the operator's EDGAR cache (`data/cache/sec`) through
  `_fetch_exhibit`, as the loop reads it. A miss raised, and nothing was fetched. None missed.
- The cut is the shortest head, at least 300 characters in steps of 50, then ` … ` and the
  clauses the coverage reader binds and displaces with, verbatim and single-spaced:
  - the recital or definition that names the earlier agreement;
  - the definition of a defined date it uses ("“Original Closing Date” shall mean March 1, 2018");
  - for a paired definition ("“Existing Credit Agreements” means the Existing 3-Year Credit
    Agreement and the Existing 364-Day Credit Agreement"), both parts' definitions;
  - the displacing clause, with 60 characters before it.
- A cut is kept only if it reads exactly as the full text reads: the same `agreement_title`,
  `is_debt_agreement` and `is_amendment`, the same `exhibit_identity`, and the same
  `displaced_agreements`. Every one of the 43 cuts does, at this PR's code.

Full texts run 2,404 to 796,756 characters; the cuts run 300 to 6,353.

To re-cut one, read the exhibit with `_fetch_exhibit(build_sec_http(), cik, accession, exhibit)`,
where `cik` is the page's own, and cut it as above. Re-cut a fixture only together with the pins
that read it.
