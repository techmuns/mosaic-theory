---
id:
status: recorded
date: 2026-09-01
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §2 (capability entry, compacted)
date-source: the migration date — the capability is older and is dated in the body
---

# THE ENTITY MASTER ACCUMULATES FACTS, NOT JUST ROWS (2026-08-31, fix/sic-absent).

*The one-line summary stays in STATE.md §2 with a pointer here. This is the detail that stood beneath it, verbatim.*

- **THE ENTITY MASTER ACCUMULATES FACTS, NOT JUST ROWS (2026-08-31, fix/sic-absent).** `INSERT OR
  REPLACE` let an UN-ENRICHED `upsert_security` (the `vinci refresh` price-backfill path) null a SIC
  the enriched path had fetched — #464 destroyed IT/Gartner's `8741`, and `vinci monitor` then read
  the hole as a resolved sector of "Unknown" on a ledgered position for two weeks. The no-row-drop
  guard compares PKs, not fields, and the standing pin was on the MAPPING, not the artifact. `sic`
  now COALESCEs like `first_seen`; an ABSENT SIC returns `None` from `monitor.sector_for_display`
  (so "Unknown" keeps its one meaning — a SIC was read and did not map) and says ABSENT in words;
  IT's row repaired from live EDGAR. Incident→invariant (shipped Y):
  `test_an_unenriched_upsert_never_nulls_a_known_sic`,
  `test_a_real_sic_change_still_overwrites_and_a_new_row_still_writes_none`,
  `test_every_ledgered_name_carries_a_sic_in_the_committed_entity_master`,
  `test_it_row_still_carries_the_87xx_sic_the_sector_is_read_from`,
  `test_an_absent_sic_is_reported_as_absent_never_as_a_resolved_sector`,
  `test_the_issuer_row_lands_column_for_column` (the issuers INSERT is now three interleaved
  COALESCE sub-selects over ten positional parameters, and `_row_to_identity` reads the SECURITIES
  table only — so nothing else can catch a transposed column there).
  **ACCEPTED RISK, with its falsifier (review, 2026-08-31):** the COALESCE means a SIC EDGAR STOPS
  publishing can no longer be cleared through this path. An operating company converting to a BDC
  loses its SIC (40 issuers in the committed master already have none), and the stale code would
  keep resolving to a confident sector; nothing detects it, because
  `scripts/backfill_entity_master_sic.py` only fetches CIKs that HAVE a hole. Accepted over the
  silent and far likelier clobber it replaces. *Falsifier:* any name whose committed SIC is absent
  from a fresh `sic_for` fetch → make the backfill re-verify KNOWN SICs and report withdrawals.
  *Record: `docs/records/2026-08-31-sic-clobber-entity-master.md`.*
