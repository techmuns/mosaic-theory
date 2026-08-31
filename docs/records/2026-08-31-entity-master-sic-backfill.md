---
id:
status: shipped
date: 2026-08-31
prs: [525]
supersedes:
superseded-by:
---

# The entity master's SIC holes are filled, and the ones that remain are the ones EDGAR does not publish

**WHAT.** Operator ruling on STATE.md §5.0 row 7 (opened by the #523 clobber record): backfill the
516 committed `securities.jsonl` rows carrying no SIC. `scripts/backfill_entity_master_sic.py`
fetches EDGAR submissions for every CIK with a hole and writes through the REAL store path
(`Store.upsert_security` → `export_snapshots`), so the no-row-drop guard, the schema and the new
COALESCE semantics all apply exactly as in a pipeline run. **516 → 60** CIK-bearing rows without a
SIC; 456 security rows and 638 issuer fields filled across 378 issuers.

**THE RESULT SPLITS CLEANLY, and the remainder is the interesting half.**

| outcome | CIKs | what it means |
|---|--:|---|
| RESOLVED | 378 | fetched and written |
| ABSENT AT EDGAR | 40 | **EDGAR publishes no SIC for them** — stays NULL, never inferred |
| FETCH FAILED | 0 | — |
| RE-CLASSIFICATIONS | 0 | none found; would have been reported, never applied |

**39 of the 40 are BDCs** (Prospect, Main Street, FS KKR, Golub, Blue Owl, Blackstone Secured
Lending, Hercules, Barings, Goldman Sachs BDC, Capital Southwest …) and the fortieth is Invesco QQQ
Trust (`entityType: investment`). That is not a gap — it is the *true state*, and it independently
corroborates the comment already sitting in `vinci/universe.py`: *"a blank SIC is exactly how a
BDC/fund slips a denylist (`None` is never `in` the exclude set — CION, OTF)"*. The universe gate
fails closed on exactly this population. After the backfill, a NULL SIC in the entity master means
something specific — EDGAR has none — instead of "nobody ever looked", which is what made IT's
destroyed value invisible for two weeks.

**IT FILLS HOLES; IT DOES NOT RE-CLASSIFY.** If a CIK already carries a SIC (issuer row or a
sibling share class) and EDGAR now reports a different one, that is a re-classification event, not
a hole: reported and SKIPPED. A backfill silently rewriting known values would be an unreviewed
data migration wearing a repair's name. Zero were found, so nothing was skipped on this ground.

**TWO THINGS THE VERIFICATION CAUGHT that the first draft got wrong.**
1. **An empty CIK reached the fetcher.** The synthetic benchmark ISSUER row (`issuer_id "IDX"`,
   `cik ""`) has no `IDX-` prefix to exclude it the way the securities rows have, so it reached
   `sic_for("")` and raised a bare `ValueError: invalid literal for int()`. Caught by running the
   10-CIK `--limit` cost gate before the full pass — which is what the cost gate is for. An empty
   CIK is now the structural mark of a synthetic identity in BOTH tables.
2. **The write RENAMED four issuers.** `upsert_security` writes one `Identity.name` to BOTH tables,
   and four CIKs hold two securities under two different names — a renamed company still carrying
   its old ticker's row (DCOM/DCBG, SHOE/SCVL, DMC/FDP, HAPN/LC). Writing the null-SIC row of such
   a pair moved the issuer's name, because the lagging row happened to be written last. A SIC
   backfill renaming issuers is scope creep with a data migration attached, so each touched
   issuer's name is now preserved by re-upserting the sibling security whose name the issuer row
   already carried — public API only, reasserting the prior state rather than patching a column
   behind the store's back. **Found by diffing the artifact field-by-field, not by review.**

**NO DOWNSTREAM DRIFT — measured, not assumed.** The cohort medians read this exact map, so the
backfill could in principle have moved every industry median and staled the committed queue. It did
not: SIC coverage of the current screen run's 1,755 screened names was **100% before and 100%
after**, and **0 screened names changed industry bucket**. The reason is structural — every
screened name is in-universe, and `build_universe` cannot admit a name whose SIC it could not read.
The whole 516 sat outside the screened set. No re-rank needed.

**THE FIELD-LEVEL DIFF IS SIC-ONLY.** `securities.jsonl`: fields changed anywhere = `['sic']`, 456
null→value, **0 other changes**. `issuers.jsonl`: `['sic', 'sic_description']`, 638 null→value,
**0 other changes**. PK sets identical in both (2,485 / 2,315 rows).

**ADJACENT CORRECTION, shipped rather than left wrong.** #523's ABSENT note told the reader to
"repair the entity-master row". This build proved that is false for 40 issuers — there is no value
to fetch. The note now names both causes and asks the reader to check which.

**VERIFIED.**
- `--limit 10` cost gate → full `--dry-run` (418 CIKs, ~1 min cold, cached after) → applied run.
  Re-runs are free and idempotent.
- `test_an_issuer_never_half_carries_its_sic` run against the **pre-backfill committed corpus** →
  FAILED with **59 real violations** (`ASB 6022 / ASBA null`, `SLNH / SLNHP`, `ZION / ZIONP`,
  `WSBC / WSBCO`, `VSEC / VSECU` …); passes after. The guard was shown finding live violations.
- Face validity on the fills: AMAT/INTC → 3674 → Technology; PFE/BMY → 2834 → Health Care; RTX →
  3724 → Industrials; ASBA/HWCPZ → 6022 → Financials. **Zero** filled rows resolve to "Unknown".
- ruff clean; `mypy --strict vinci` clean; full `pytest -m "not network"` **3268 passed, 0 failed,
  138 network-skipped** — run on the freshly-written artifacts, per the ARTIFACT-PASS RULE.

**INCIDENT → INVARIANT (shipped Y).** `tests/test_entity_master_sic.py`:
`test_an_issuer_never_half_carries_its_sic` (**the clobber's signature** — one CIK, one EDGAR SIC,
so a partial hole is only reachable by a writer that half-knew the fact),
`test_a_cik_never_disagrees_with_itself_about_its_sic`,
`test_every_present_sic_resolves_to_a_real_industry`,
`test_synthetic_benchmark_rows_never_carry_a_sic` (the negative pin — a SIC on SPY would be
invented), `test_no_name_in_the_current_universe_lacks_a_sic` (the universe half of the decision
surface; the ledger half is pinned in `test_monitor.py`).

**STILL OPEN, unchanged by this build.** Whether `vinci refresh` should resolve with
`enrich=True`. It can no longer DESTROY a SIC (#523), but it still stores NULL for a name it
introduces, and enriching would make a price backfill depend on an EDGAR fetch per ticker that the
command's `ResolutionError`-only catch would turn into an aborted backfill. Operator ruling.
