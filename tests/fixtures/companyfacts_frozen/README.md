# Frozen companyfacts vintages

`tests/fixtures/companyfacts/` TRACKS the committed pages: `scripts/build_companyfacts_fixture.py`
is re-run in every PR that re-assembles a name, so a recompute agrees with the page.

A test that compares EDGAR against a FROZEN second source at a shared date (CIQ's balance sheet in
`ciq_net_debt_one_builder.json` / `ciq_cash_and_st_investments.json`), or pins a value read at one
vintage, cannot follow that refresh: the second source does not move until it is re-exported. Such
a test reads the file here first, and the tracking fixture only when none is here.

- `NFLX.json` — the tracking fixture as committed at main `121c29be` (cash instant 2026-06-30, the
  date CIQ's frozen NFLX figures carry). Frozen 2026-10-27, when NFLX's page moved to its
  September-quarter 10-Q. Refreeze it together with the CIQ side, never alone.
- `SMPL.json` — the tracking fixture as committed at main `f2c6e7aa` (cash instant 2026-05-30, the
  date CIQ's frozen SMPL figures carry). Frozen 2026-10-29, ahead of SMPL's page moving to its
  FY2026 10-K. Refreeze it together with the CIQ side, never alone.
- `GOOGL.json` — the tracking fixture as committed at main `0e574f6b` (cash instant 2026-06-30, the
  date CIQ's frozen GOOGL figures carry). Frozen 2026-11-02, when GOOGL's page moved to its
  September-quarter 10-Q. Refreeze it together with the CIQ side, never alone.
- `AMZN.json` — the tracking fixture as committed at main `9e996d7f` (cash instant 2026-06-30, the
  date CIQ's frozen AMZN figures carry). Frozen 2026-11-03, when AMZN's page moved to its
  September-quarter 10-Q. Refreeze it together with the CIQ side, never alone.
- `nonop_window/` — GOOGL, ORKA, WOR, UBER and FUBO, the tracking fixtures as committed at main
  `c4c9f432`. Frozen 2026-11-05 for the non-operating window's value pins
  (`tests/test_nonoperating_earnings.py`, `tests/test_r4_machine_proposal.py`; #916 review
  round 2). A subfolder, not `<T>.json` here, because GOOGL.json above is a different vintage
  frozen for the CIQ side. Each pin cuts its copy at a stated date (`concepts.facts_as_of`), so
  these are refrozen only when a pin's own date moves. `MVST` and `SMPL` joined on 2026-11-12, the
  tracking fixtures as committed at main `650057f3` (last changed in `53cbe9fe` and `3e97ee7d`), for
  the window anchored at the filer's latest filed quarter (STATE row 51 (2)): the two pages whose
  window moves, each pinned at its page's reference and price dates.
- `EPAM.json`, `WLK.json` and `VRRM.json` — the tracking fixtures as committed at main `cb8139ee`
  (cash instant 2026-06-30 on each; the date CIQ's frozen EPAM and WLK figures carry). Frozen 2026-11-09,
  when the three pages moved to their September-quarter 10-Qs (fix request 2, order 1). EPAM and WLK are
  refrozen together with the CIQ side, never alone. VRRM's is a SHAPE fixture, read by
  `tests/test_share_readers_cover_dated.py` and `tests/test_cover_dated_share_counts.py` at reference
  2026-08-14: its August vintage carries the five share tags dated after their own filing, which those
  pins measure; refreeze it only with them. `tests/test_cross_check.py` reads WLK's for the quarter its
  self-funding cite names (2026-06-30).
- `UBER.json` — the tracking fixture as committed at main `6fbbb4a2` (cash instant 2026-06-30, the
  date CIQ's frozen UBER figures carry). Frozen 2026-11-09, when UBER's page moved to its
  September-quarter 10-Q (fix request 2, order 1). Refreeze it together with the CIQ side, never alone.
  `tests/test_cross_check.py` reads it for UBER's 32 revenue filing dates and `tests/test_share_basis.py`
  for its latest count at 2026-08-10. Not `nonop_window/UBER.json`, a different vintage.
