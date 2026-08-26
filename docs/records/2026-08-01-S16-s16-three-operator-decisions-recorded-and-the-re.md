---
id: S16
status: recorded
date: 2026-08-01
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**S16. THREE OPERATOR DECISIONS RECORDED, and the reads that closed two of them (2026-08-01).**

- **ROUTING: CARRY.** *Decided by the density measurement, not by preference.* DROP leaves **49
  names, two sector groups of >=3, and ZERO theme clusters** — a pool too thin to run a
  cross-sectional discriminator over. CARRY keeps 331. The NOT_EVALUATED names stay in and stay
  LABELLED, which is the point: the label is the worklist, and dropping them would delete the
  evidence that the valuation gate cannot see 282 of the 413 names that reach it.
- **CANONICAL SPOT: `grouped_daily`.** The store is its CACHE (every store row's `source` reads
  `polygon-grouped`), and the screen already consumes it, so naming it canonical changes no
  behaviour and removes a choice. **Per-symbol `daily_bars` is the VERIFICATION route** — an
  independent endpoint to check against, which is worth more than a third opinion that is really
  the same opinion. All seven committed spots agree exactly across all three (S12).
- **P3 pt1: NOT BACKFILLED. Write-forward binding stands.** The 70 unstamped references need
  analyst source material that is not in the record; parsing the 49 dated `source` strings would
  manufacture confidence about which token is the period (D21). `VINTAGE_REQUIRED_FROM` binds
  forward; the 70 stay unstamped and SAY so.

**THE ENTRANT READ — the gap-on-return risk is RETIRED, measured not argued.** Of the **58 names
that entered the universe at 2026-07-29**, **54 have a largest gap of 4 days** (weekends). They
accrued bars throughout the window they were OUTSIDE the universe — 18 bars each between 07-06 and
07-29, `source=polygon-grouped`. **Mechanism:** `ingest_prices` is called with
`start = reference_date - lookback_days` (1825d), so **every run re-backfills the full five-year
window for every current member** — an entrant is backfilled by the very run that admits it, before
any gate reads. No hole can survive to be seen. The apparent outliers are SHORT HISTORIES, not
holes: OGG 8 bars from 2026-07-20, DFNS 138 spanning 2021-2026, SOLS 186, PSKY 245, AAUC 286 — each
continuous to 2026-07-29.

**AND THEY ARE NOT SYSTEMATICALLY UNASSESSABLE.** In `-03` the 58 entrants read **46 FAIL, 1 PASS,
11 NOT_EVALUATED (19%)** — of the 11, **8 at `g3_multiple_floor`**, 2 at `g1_drawdown`, 1 at
`g2_idiosyncratic`. The G3 eight is the fleet-wide valuation-data gap (282 of 413 that reach G3),
not an entrant property; the three at G1/G2 are the short-history listings above. **This RETIRES
the inference recorded one turn earlier** that departed names return with a hole #294's anchor bound
would refuse — the bound is correct, the hole does not occur.

**THE TEMPORAL SKEW IS STILL LIVE — established from code.** `screen_universe` reads
`store.latest_universe(reference_date)`, defined as *the most recent snapshot at/before a date*.
**Nothing binds it to a `build_universe` run**: the build is a separate CLI subcommand
(`_cmd_build_universe`), nothing sequences them, and **`RunManifest` records run_id /
reference_date / screen / band / routing_policy / stages but NOT the universe snapshot's `as_of`**
— so the skew is not merely possible, it is INVISIBLE in the record. `-02` and `-03` matching their
snapshot is same-day coincidence, exactly as suspected, not a fix. `-01`'s caveat now carries the
corrected mechanism.

**TWO CAP BANDS, NEITHER CITING THE OTHER, NOTHING WATCHING THEM.**
`vinci/config.py:40-41` `UniverseConfig.market_cap_min_usd = 300_000_000` /
`market_cap_max_usd = 10_000_000_000` is **AUTHORITATIVE** for the fund's universe — it is what
`build_universe` gates on. `vinci/themes/assay.py:90` `CAP_MIN, CAP_MAX = 100e6, 10e9` is a
**hardcoded literal pair** for the themes retrocast; `assay.py` does not import `UniverseConfig`.
**Neither cites the other and no test relates them.** The floors already differ 3x (100M vs 300M);
the ceilings agree at 10B **by coincidence of two independent literals**, which is the more
dangerous half — they look consistent and nothing keeps them so. Changing one leaves the other
silently untouched. Recorded, not reconciled: which band the retrocast SHOULD use is a research
decision, not a lint.

**BAND BASIS — still none.** The only recorded justification for 300M/10B is the comment at its
definition: *"Defaults are face-validity starting points (revisit by eyeballing the resulting
universe, never by forward returns)."* Honest, and explicitly not a derivation — unlike G2's -15%
or the theme tau=0.50, both of which have traced bases. The guardrail against outcome-tuning is
stated at the site; the width is not justified anywhere.

**S/D IDENTIFIER LINT SHIPPED** (`tests/test_state_identifiers.py`): uniqueness AND
dangling-reference resolution, since a duplicate makes a citation ambiguous and a dangling one makes
it empty — the same broken property from two sides. **Validated against the REAL defect, not a
synthetic**: at `c112f25` (the #303 merge, where the S10 collision was live and had already survived
four merged PRs) the lint reports `duplicates = ['S10']`; at HEAD it reports none across 37
headings. That is D22's counter-measure applied to the guard built in response to D22.
