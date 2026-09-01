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

# UNIVERSE REBUILT post-#119 + `--only-tickers` delta-scan primitive (2026-07-13, feat/scan-only-tickers; PR open, not merged).

*The one-line summary stays in STATE.md §2 with a pointer here. This is the detail that stood beneath it, verbatim.*

- **UNIVERSE REBUILT post-#119 + `--only-tickers` delta-scan primitive (2026-07-13,
  feat/scan-only-tickers; PR open, not merged).** (1) Rebuilt the cap-band universe with the post-#119
  builder (`vinci build-universe --ref 2026-07-06`, matching the committed snapshot's as_of so the delta
  isolates the shares recovery, not price drift): **in_universe 1760 → 1800 (net +40: +47 recovered,
  −7 dropped).** The +47 is dominated by the #119 us-gaap shares fallback clearing names past `no_shares`;
  it is FAR below the 213 "recoverable-past-`no_shares`" because the downstream cap-band ($300M–$10B) /
  ADV-floor ($3M) / security-type gates cut most recovered names — the #119 caveat, now quantified. The
  −7 (AGX/SUZ/TBRG/IRD/GLSI/OLPX/PAYP) are EDGAR-frame drift, NOT #119: the fallback only ADDS shares
  (dei wins on overlap) so it cannot drop a name — these reflect ~1 week of fresh 10-Q frame data between
  the Jul-6 snapshot and the Jul-13 rebuild (EDGAR frames are live; no historical frame snapshot to
  isolate against). The rebuilt universe_snapshot/securities/issuers are **NOT committed here** — the
  full-DB `export_snapshots` also rewrote `candidate_records.jsonl` (−275) and `decision_ledger.jsonl`
  (−1, a forbidden ledger-DELETE) from a stale working DB, so ALL snapshot changes were reverted to
  protect the append-only ledger; the counts above are the recorded FACT, the artifact refresh is left to
  the weekly cron / a clean artifact pass. (2) `themes-exposure` gained `--only-tickers T1,T2,…` /
  `--only-file <path>`: restricts a scan to the intersection of the named set and the universe
  (`_resolve_only_tickers` + `_partition_only`) — unknown names are printed and skipped, an EMPTY
  intersection ERRORS (never scans nothing silently). This is the **monitor's future DELTA-SCAN
  primitive** — restrict a scan to a named subset with NO new code path. Verified: ruff + `mypy --strict
  vinci` clean; network-free tests (subset / unknown-name fail-loud / empty-intersection error / argparse
  wiring). (3) **Theme-#3 delta scan of the 47 recovered names PENDING** (sanctioned, small; runs
  post-merge via `--only-tickers` against the restored rebuild); the theme-#3 FREEZE remains gated on
  delta completion — the recovered names must be scanned before the funnel is treated as complete.
