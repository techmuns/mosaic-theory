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
