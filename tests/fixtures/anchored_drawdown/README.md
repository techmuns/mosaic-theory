# Anchored-drawdown fixtures

SMPL's real drawdown inputs, recorded 2026-11-04 for `tests/test_anchored_drawdown.py`. Refreeze only
together with the pins that read them.

| file | what | from |
|---|---|---|
| `SMPL-bars.jsonl` | SMPL's daily bars 2025-08-01..2026-11-03, one `PriceBar` per line (vendor Polygon, `polygon-aggs`; symbol in `internal_id`; the bar date on each row) | a copy of the primary's store, SMPL refreshed by `vinci refresh SMPL --aggs --start 2021-07-01 --end 2026-11-03` on 2026-11-04 |
| `SMPL-edgar.json` | the 10 `Filing` rows `EdgarClient.recent_filings(cik, forms=("8-K", "8-K/A"), since=2025-09-01)` returned, and the three documents the drawdown reader fetches for 8-K 0001702744-26-000010 (the 8-K, its index headers, its Ex-99.1), each cut after the part its reader reads — `parse_8k_events` and `_extract_revised_guidance` give identical output on the cut and the whole document (checked when cut) | EDGAR via `vinci.sec.build_sec_http`'s cache, 2026-11-04 |
