# Covenant coverage-rule fixtures (STATE row 63)

`<T>.json` holds one committed page's covenant inputs, for `tests/test_covenant_coverage_rule.py`:

- `capital_structure` is the page's `mechanical.capital_structure`, unmodified, from
  `data/dossiers/<T>/dossier.json` at main `51784e53` (2026-11-16). That covers its pointer rows,
  its CIQ panel instruments and its maturity check, whose `bound` is the page's reference date.
- `texts` maps `"<accession> · <exhibit>"` to the text of every exhibit the loop reads: every
  target (`covenant_extract._core_agreement_exhibits`) and, since review round 2, every other
  exhibit of a located filing, which the loop reads for who it is but never sends. Each is a CUT
  of the real document.

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
  `is_debt_agreement` and `is_amendment`, the same `exhibit_identity`, the same
  `displaced_agreements`, and, for an exhibit whose title is not read, the same dates in its head.
  Every one of the 61 cuts does, at this PR's code.

The cuts run 300 to 6,353 characters.

**`round2_heads.json`** holds three more real heads, for review round 2: UBER's `…21-000058` (its
base read from its heading, not its recital's history; 1,050 characters, which read as the full
exhibit at this PR's code and gave the base the review found at the head it reviewed), VRRM's
`vrrm-ex10_2.htm` and NKE's five-year agreement (each the shortest head that reads its title,
amendment and identity as the full exhibit does).

To re-cut one, read the exhibit with `_fetch_exhibit(build_sec_http(), cik, accession, exhibit)`,
where `cik` is the page's own, and cut it as above. Re-cut a fixture only together with the pins
that read it.
