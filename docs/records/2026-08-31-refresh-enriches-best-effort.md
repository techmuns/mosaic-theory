---
id:
status: shipped
date: 2026-08-31
prs: [528]
supersedes:
superseded-by:
---

# `vinci refresh` fills the SIC at the point of entry — and a flaky SEC never stops a price backfill

**WHAT.** Operator ruling on STATE.md §5.0 row 7 (the last open item from the #523/#525 SIC work),
now closed. `refresh` resolves each ticker and then fetches its EDGAR SIC, so a name that enters
the entity master through this command arrives complete instead of with a permanent hole. The SIC
fetch is **best-effort**: a `data.sec.gov` failure prints and degrades to UNKNOWN rather than
aborting the run.

**WHY IT MATTERED.** `refresh` is how a name **outside the cap band** enters the entity master, and
`build_universe` never comes back to enrich a name it does not admit — so whatever `refresh` stores
is what that name keeps, forever. It stored no SIC. NFLX has been SIC-less since it arrived exactly
this way, and Gartner (#523) was the same class: **ledgered but out-of-universe**, the class whose
label a human actually reads on the monitor. The #525 backfill swept the existing holes; this stops
new ones being dug.

**WHY NOT SIMPLY `enrich=True`.** Because it would have made a price backfill fail for a reason that
has nothing to do with prices. `resolve_ticker(enrich=True)` propagates the raw HTTP error, and
every ticker is resolved BEFORE any bars are fetched, so a single SEC hiccup aborts the whole run
**before it starts**. Demonstrated rather than asserted, against the real resolver with a failing
HTTP client:

```
naive  resolve_ticker('NFLX', enrich=True):
   RAISES RuntimeError: HTTP 503 from data.sec.gov
   -> aborts the ENTIRE backfill before it starts. No bars, for a SIC the job never needed.

shipped _resolve_for_refresh(resolver, 'NFLX'):
   NFLX: SIC lookup FAILED (RuntimeError: HTTP 503 …) — refreshing prices with SIC UNKNOWN.
   returns NFLX sic=None -> the backfill proceeds
```

**THE SPLIT: STRICT ON IDENTITY, TOLERANT ON THE ADORNMENT.** An unknown or ambiguous TICKER still
fails loud and is skipped — mis-resolution is the system's worst failure and the resolver exists to
refuse it. A SIC is an adornment on a price job. **The tolerance lives at this ONE call site, not
in the resolver**, deliberately: a soft mode on `EntityResolver` would let every other caller
degrade silently, including the universe gate that fails CLOSED on a missing SIC (`unknown_sic`).

**SAFE ONLY BECAUSE OF #523.** Writing UNKNOWN can no longer erase a stored SIC — `upsert_security`
COALESCEs. Before that fix, this degradation would have BEEN the clobber. The ordering of the three
builds was load-bearing, not incidental.

**A DEFECT THE LIVE RUN FOUND, that the unit stubs had tidied away.** EDGAR returns
`sicDescription: ""` — an empty string, not null — for a SIC-less issuer (observed on FSK, a BDC).
SQL `COALESCE` treats `''` as PRESENT, so that blank would have **overwritten** a stored
description instead of deferring to it, re-opening on the sibling column exactly the erasure #523
closed. *Found only by running it against the live API; the first stub returned `None` and the pin
would have passed vacuously.*

**AND THE FIRST FIX WAS AT THE WRONG LAYER — corrected in review.** It normalised the blank in
`vinci/cli.py` alone, which left the defect standing on every path it had not touched:
`resolve_ticker(enrich=True)`, `_enrich_issuer` (both the securities and the issuer row), and
`scripts/backfill_entity_master_sic.py`, which feeds the description straight into `model_copy` and
is committed and re-runnable. The normalisation now lives in **`sic_for`**, the one place every
consumer reads through, and is pinned there
(`test_sic_for_normalises_edgars_empty_description_to_absent`). Fixing a shared helper's defect at
one call site is how the next consumer repeats it — which is precisely what this PR's own first
draft did.

**VERIFIED (live EDGAR, all four cases through the shipped helper).**

| ticker | result | what it proves |
|---|---|---|
| `NFLX` | `7841` "Services-Video Tape Rental" | the hole this closes — the name that has been SIC-less |
| `IT` | `8741` "Services-Management Services" | agrees with the #523 repair |
| `FSK` | `None`, "EDGAR publishes no SIC … never inferred" | ABSENT reported as absent, not as a failure |
| `ZZZZ` | skipped, "no US issuer for ticker" | the identity is still fail-loud |

**INCIDENT → INVARIANT (shipped Y).** `tests/test_refresh_enrich.py`, all driven through the REAL
`_cmd_refresh` rather than the helper alone — a helper-level pin stays green if the call site stops
calling it, and what matters is the identity that reaches `upsert_security`:
`test_refresh_stores_the_sic_it_fetched` (the SIC must reach the STORE — fetching and dropping it
is the dead write #83 fixed in `build_universe`),
`test_a_failing_sic_lookup_degrades_to_unknown_and_still_ingests_bars` (**the negative pin**),
`test_an_unknown_ticker_still_fails_loud`,
`test_an_issuer_edgar_publishes_no_sic_for_is_reported_not_inferred`,
`test_an_empty_sic_description_is_stored_as_none_not_as_a_blank`,
`test_benchmark_etfs_stay_resolver_exempt` (a SIC on SPY would be invented).
plus, added in review: `test_a_run_that_lost_every_sic_says_so_once_at_the_end` and
`test_a_clean_run_prints_no_failure_tally`, and `test_sic_for_normalises_edgars_empty_description_
to_absent` in `tests/test_resolver.py`.
Three were run against the PRE-CHANGE call site and FAILED; the empty-description pin FAILED
without the normalisation; the tally pin FAILED without the tally; the resolver pin FAILED without
the source fix. Guards shown able to fail, not merely passing.

**TWO MORE THINGS REVIEW CHANGED.** (1) **A systemic SIC failure now says so once, at the end.**
Per-name lines are not a signal: on a long refresh during an SEC outage — or after a change that
breaks `sic_for`, since `except Exception` catches an AttributeError just as readily — every name
degrades, the lines scroll past inside Polygon's progress output, and the run still ends `done:`
with exit 0, reading as a clean refresh while the hole this command exists to close is re-dug
wholesale. A tally (`WARNING: n/m SIC lookup(s) FAILED — …`) prints after the run summary. An
issuer EDGAR simply publishes no SIC for is NOT counted — a warning that fires when nothing is
wrong trains the operator to ignore it. (2) **The tests are now hermetic.** They had stubbed the
resolver, store and price-ingest but not `get_config`, so `_cmd_refresh` ran the real
`ensure_dirs()` and mkdir'd `data/`, `data/cache/` and `data/snapshots/` into the pytest CWD —
invisible from the repo root, where those already exist. Demonstrated by running the file from an
empty directory; it now leaves nothing behind.

ruff + `mypy --strict vinci` clean; `pytest -m "not network"` **3302 passed, 0 failed, 138
network-skipped**. Live re-check after moving the normalisation: NFLX `('7841', 'Services-Video
Tape Rental')`, IT `('8741', 'Services-Management Services')`, FSK `(None, None)`.

**WHAT THIS DOES NOT DO.** It does not re-verify a SIC that is already stored, so the accepted risk
recorded with #523 stands unchanged: a SIC EDGAR STOPS publishing still cannot be cleared, and
nothing detects it. Its falsifier and un-accept path are unchanged in STATE.md §2.
