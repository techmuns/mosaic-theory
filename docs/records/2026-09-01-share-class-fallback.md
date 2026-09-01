---
id:
status: shipped
prs: [543]
date: 2026-09-01
supersedes:
superseded-by:
---

# Share-class fallback — the last coverage gap was never an IFRS problem

**WHAT.** When a NON-depositary name has no share count in ANY XBRL tier (dei → us-gaap →
period-average), `build_universe` now falls back to the Polygon share-class reference count,
stamped `(FALLBACK - no filed count in any XBRL tier)` in the committed row and counted as
`polygon_count_fallback`. **Strictly a fallback**: a name WITH a filed count keeps it, so the
change can only add names and can never move a cap that is already admitted. Fetched one ticker at
a time and only for allowlisted instrument types, so the call is made only where it can pay. A
name with no count in any source still drops at `no_shares` — the reason now names both sources
it tried.

**WHY — THE MEASUREMENT RETIRED THE ORIGINAL PHASE 2.** The brief scoped this as "per-name
`ifrs-full` reads for IFRS-only filers". Measured after #541 instead of assumed:

| bucket | count | reading |
|---|---|---|
| still lost at `no_shares` | 1,240 | all non-depositary (ADRs no longer reach this gate) |
| …FUND / UNIT / WARRANT / RIGHT / SP / ETV | 711 | the instrument allowlist rejects them anyway |
| operating equity (CS) | 529 | the real remainder |
| **…with ADV > $100M** | **23** | the part worth paying for |

Diagnosing those 23 by namespace is what overturned the scope. The largest are **multi-class US
filers** — V, BRK.B, STZ, TSN, DUOL, PLNT, SEI, FWONK, ARES, BAM — whose cover-page count is
dimension-qualified and therefore never reaches the XBRL frames (the META shape from #529). They
are not IFRS filers at all. An `ifrs-full` branch would have recovered at most 5 of 23 and none
of the largest; **the share-class reference reaches 19 of 22 probed**, spanning both the
multi-class-US and IFRS-only cases with one mechanism the tree already had.

**HOW VERIFIED.**
- REAL RUNS, both bands at vintage 2026-08-24 from a cold DB. `no_shares` **1,240 → 889**;
  **351 names sized by the fallback** per pass (79 admitted rows in primary, 29 in theme).
  **19 of the 22 targeted names recovered**: V $651.7B · BRK.B $710.1B · BN $102.9B ·
  BAM $85.7B · RACE $75.2B · NU $56.2B · TRI $47.3B · NTR $35.5B · TECK $33.9B ·
  ARES $31.4B · VIK $29.1B · FWONK $23.9B · STZ $23.5B · TSN $16.3B · GFL $14.5B ·
  GRAB $14.0B (theme) and DUOL $5.9B · PLNT $4.1B · SEI $3.5B (primary).
  **AZN, BSP and JMKE remain absent** — no count in any source, dropped loudly, correctly.
- 3 pins in `tests/test_ads_denominated_cap.py`: the multi-class shape is admitted and stamped;
  the fallback NEVER displaces a filed count (a name with both keeps the filed one — this is the
  bound on the blast radius); a name with neither still drops at `no_shares`.
- The retention guard reddened on the new counter and was allowlisted WITH its reason: the
  failure case is not a new stage — a name with nothing still drops through `_drop`.
- ruff + `mypy --strict` clean; offline suite **3273 passed**, with one PRE-EXISTING failure
  (`test_run_weekly_takes_its_date_from_the_data_and_not_the_clock`) confirmed failing on
  origin/main before this branch existed: it dates a run from fixture prices that no longer reach
  the last ten days now that the clock has rolled to 2026-09-01. Not this change; recorded, not
  fixed here.

**REVIEW ROUND (2026-09-01, medium code-review — two findings, both applied).**
1. **A retention row asserted a lookup that never ran.** The fallback is consulted only for
   instrument types the universe would admit, so for a FUND/UNIT/WARRANT the reference call never
   happens — yet the drop reason said "and none from the share-class reference either". On the
   real run roughly **711 of the 889** `no_shares` rows are exactly those types. The retention row
   IS the evidence trail, so it now names which of the two sources actually ran, and the stamped
   input matches.
2. **One bad ticker could kill a ten-minute build.** `get_json` raises on a non-retryable status,
   and this PR calls the reference per-name from inside the universe loop — so a single 404 for a
   delisted-but-still-priced symbol would abort a run with no partial-progress recovery. The datum
   is OPTIONAL by design (absent already means "drop loudly"), so a failed lookup now yields the
   same already-counted outcome: same idiom as `mention_prefilter(skip_errors=True)`, a
   conservative gap and never a fabricated value.

Neither fix changes an admitted row, so the committed snapshots are unaffected: (1) touches only a
drop REASON (retention rows are written only under `--retain`, not by this build path) and (2) is
inert unless a lookup errors. No rebuild was needed and none was run.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **BAND MEMBERSHIP: PRIMARY 2,039 → 2,118 (+79), THEME 913 → 942 (+29).** Cumulatively with
  #541 the primary band has gone 2,000 → 2,118 — about **6% of the forward-validation
  population** — every one a name that had been dropped for want of a count that existed
  elsewhere. **This warrants explicit operator sign-off, not the coverage-repair default.**
- SOURCE TIER: these caps rest on a reference feed rather than a filing. That is why it is
  fallback-only and why the row says so; a consumer needing a filed count reads the `source`.
- ~529 per-ticker reference calls on a cold cache, once per build day.
- NOT DONE: the dual-class approximation. `universe.py` still multiplies an issuer's TOTAL
  shares by one class's price for names that DO have a filed count. Polygon's per-class count
  would fix that properly, but as a REPLACEMENT it would move caps already admitted — a larger,
  separate change. Recorded, not bundled.
