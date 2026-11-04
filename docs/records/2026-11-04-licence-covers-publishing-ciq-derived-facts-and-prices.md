---
id: 2026-11-04-licence-covers-publishing-ciq-derived-facts-and-prices
status: shipped
date: 2026-11-04
prs: [894]
supersedes:
superseded-by:
---

# The licence covers publishing CIQ-derived facts and Polygon and Tiingo prices: the workbook files stay out, the values may be published with their source and knowable date

**WHAT.** The operator ruled on 2026-11-04, verbatim: *"our licence covers publishing CIQ-derived facts and Polygon & Tiingo prices"*. CLAUDE.md's Security section now says so, in a new bullet, PUBLISHED DATA:
- CIQ-derived facts and Polygon and Tiingo prices may be published in this public repo and in the shared fact store (Parquet on Cloudflare R2, its manifest in git).
- Each published value carries its source_ref. For CIQ that is the workbook's sha256, its sheet and its row/column; for prices, the vendor, the symbol and the bar date.
- Each also carries its knowable date. A CIQ fact is knowable from its export date, or from the column's own stated filing date, never from its period end.
- The raw workbook FILES stay git-ignored, and they never enter the bucket. CLAUDE.md's "Never commit" bullet keeps them, and replaces "Pasted licensed CIQ tables are never committed" with a pointer to the new bullet.

**WHY.**
- The fact layer must be shared by both coding agents, which work from different machines. A store kept on one machine's git-ignored disk serves only that machine.
- Measured 2026-11-04: EDGAR alone is 34,582,442 facts over 2,253 companies, about 8.5 GB as JSONL. That is why the store is object storage with a manifest in git, rather than files in git.
- CLAUDE.md's rule before this ruling allowed derived analysis (pages, the exposure map) but barred pasted licensed CIQ tables. A fact store of CIQ values sat on the barred side, so an agent following CLAUDE.md would have refused to publish it.
- **Why CIQ facts take the export date:** an export carries history as restated up to the day it was taken. A CIQ fact dated by its period end would let a page priced earlier read a later restatement, which is the look-ahead the price-date cut (#884, #885, #888) exists to stop.

**HOW VERIFIED.** A policy change with no code path. The record checks are `tests/test_record_legibility.py` and `tests/test_state_identifiers.py`, run on this branch.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- Everything published is world-readable for good: this repo's history, and a public bucket's copies.
- The ruling is the operator's reading of the licences. No agent re-checks the vendor terms.
- What stays out is a choice made here, not something the ruling states: the workbook files themselves, and an article's or transcript's text beyond short quotes. The operator can widen it with a later record.
