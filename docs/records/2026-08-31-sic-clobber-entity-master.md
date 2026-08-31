---
id:
status: shipped
date: 2026-08-31
prs: [523]
supersedes:
superseded-by:
---

# A partial upsert nulled Gartner's SIC, and the monitor read the hole as a sector

**WHAT HAPPENED.** IT (Gartner, CIK 0000749251) carried `sic 8741` in the committed entity master
from 2026-07-06 (#83, the "dead write" fix) through 2026-08-13. At **bc442cb (2026-08-17, #464)**
it became `null` — in both `securities.jsonl` and `issuers.jsonl`. From then on every `vinci
monitor` run re-resolved IT's sector to `"Unknown"` and printed
`IT: sector re-resolved to Unknown for display` on a LEDGERED position. Surfaced by the 2026-08-31
code review of #520/#521, correctly downgraded there from "regression in those PRs" to a standing
absent-vs-broken gap.

**THE MECHANISM, and why exactly one name.** `_cmd_refresh` (`vinci/cli.py`) resolves with
`resolve_ticker(t)` — **no `enrich=True`** — and hands the resulting `Identity` (whose `sic` is
therefore `None`) to `store.upsert_security`. That statement is `INSERT OR REPLACE`, which rewrites
EVERY column, so an un-enriched writer silently overwrote a SIC the enriched path had already
fetched. #464's diff shows the fingerprint plainly: it regenerated `tests/fixtures/prices/IT.jsonl`
and `NFLX.jsonl` (an operator price backfill for those two names) and, in the same commit's
`issuers.jsonl`, **five names GAINED a SIC** from that run's `build_universe` while **Gartner alone
LOST one**. NFLX had no SIC to lose (it has never been in the cap band, `first_seen: null`), and
every other name is re-upserted WITH its SIC by the next `build_universe`. IT is the exposed class:
**ledgered but out of the cap band**, so no enriched write ever came back for it — and that is
precisely the class whose label a human reads on the decision surface.

**WHY NOTHING RAISED.** The no-row-drop guard (`_assert_no_row_drop`) compares **PKs**, not field
values, so a row that keeps its key while losing a fact passes. And the standing pin,
`test_it_sector_resolves_industrials_not_other`, asserts `sector_for_sic("8741") == "Industrials"`
— it pins the MAPPING, and stayed green for two weeks while the INPUT to that mapping was
destroyed. A helper pin cannot see a hole in the artifact its consumer actually reads.

**SCOPE, measured before fixing.** 526 of 2,485 committed `securities.jsonl` rows carry no SIC (517
CIK-bearing + 9 synthetic `IDX-` benchmarks). Of those, **0 are in the current universe** (the
`unknown_sic` gate excludes a name it cannot confirm, so an admitted name always carries one) and
**exactly 1 was ledgered — IT**. The other 516 are names that left the universe or were only ever
price-backfilled; they reach no decision surface today, and `vinci/cohort.py`'s `MIN_SIC_COVERAGE`
guard already refuses medians on a thin map. Left alone deliberately, recorded as an operator row
rather than swept: a ~500-call EDGAR backfill is the operator's call, not a bug fix's.

**THE FIX, three parts.**
1. **The write stops destroying facts.** `upsert_security` now COALESCEs `sic` (and the issuer's
   `sic_description`) onto the stored value exactly as it already did for `first_seen`: a writer
   that does not KNOW the fact leaves the known one standing. Nothing real is lost —
   `build_universe` EXCLUDES a name whose SIC it cannot read, so it never writes a NULL SIC for an
   admitted name, and a genuine re-classification is a non-NULL value that still overwrites.
2. **ABSENT is no longer dressed as a label.** `resolve_label(None).sector` answers `"Unknown"`,
   and so does a PRESENT-but-unmappable SIC — collapsing the two is what let a broken lookup read
   as a resolved sector. `monitor.sector_for_display` returns **`None`** for an absent SIC (the
   artifact records that nothing was read) and `monitor.sector_note` says so in words that cannot
   be mistaken for a reading; `"Unknown"` keeps exactly one meaning — a SIC WAS read and did not
   map. The forward-only re-resolution note is unchanged when a SIC is present.
3. **The data is repaired.** IT's `securities`/`issuers` rows restored to `8741` /
   `"Services-Management Services"` — fetched LIVE from EDGAR submissions in this build, and
   identical to what the snapshot held before #464.

**VERIFIED (real runs, previously-broken case shown).**
- Live EDGAR `sic_for("0000749251")` → `('8741', 'Services-Management Services')`. *(The review
  brief said 8742; the record says 8741 — same 87xx family, same Industrials sector either way.)*
- `vinci monitor --ref 2026-08-11` end-to-end on live Polygon: prints
  `IT: sector re-resolved to Industrials for display (the frozen row logged Other — never
  rewritten)`, restoring the pre-regression reading. The regenerated day differs from the committed
  one only in unrelated freshness drift (newer filings) — **no `sector` field changed** — so the
  verification artifact was reverted rather than committed.
- Both artifact pins were run against the UN-REPAIRED committed snapshot and FAILED
  (`ledgered name(s) with NO SIC in the entity master: ['IT']`); the store pin was run against the
  PRE-FIX `store.py` and FAILED. Guards shown finding the real live violation, not just passing.
- ruff clean; `mypy --strict vinci` clean; full `pytest -m "not network"` **3259 passed, 0 failed,
  138 network-skipped**.

**INCIDENT → INVARIANT (shipped Y).**
`test_an_unenriched_upsert_never_nulls_a_known_sic` (the exact failure shape, on the real name) +
`test_a_real_sic_change_still_overwrites_and_a_new_row_still_writes_none` (the negative pin —
preserving must not become freezing); `test_every_ledgered_name_carries_a_sic_in_the_committed_
entity_master` (**the pin at the right layer** — over the real committed artifacts, the one that
would have caught this) + `test_it_row_still_carries_the_87xx_sic_the_sector_is_read_from` (pinned
at the FAMILY level, matching the mapping test's own stated discipline, so an in-family EDGAR
re-classification does not rot it while a NULL still fails);
`test_an_absent_sic_is_reported_as_absent_never_as_a_resolved_sector`.

**NOT FIXED, deliberately — reported, not swept.**
- `_cmd_refresh` still writes an un-enriched identity. With the COALESCE fix it can no longer
  DESTROY a SIC, but it still stores `null` for a name it introduces (NFLX's class). Adding
  `enrich=True` would make a price backfill depend on an EDGAR submissions fetch per ticker, and
  the command catches only `ResolutionError` — an HTTP failure would abort the whole backfill.
  That trade is the operator's ruling, not a bug fix's.
- `vinci/orchestrator.py:152` writes `resolve_label(sic_by_id.get(...)).sector` into candidate
  records with the same absent-reads-as-"Unknown" collapse. Same class, different surface; out of
  this fix's scope.
