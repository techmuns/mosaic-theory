---
status: open
date: 2026-11-02
prs: []
supersedes:
superseded-by:
---

# MNST is followed in the QUALITY book, but neither new page is built: MNST's assembly is refused on a share basis its 2-for-1 split moved, and CELH's exports are refused before assembly on a material LTM its quarters do not support

**WHAT.** The operator asked for two new pages on 2026-11-02, in these words: *"trigger following
assembly in a new session (files already added in manual folder) - MNST (quality) · CELH
(overshoot)"*. Neither page is written. One assembly ran (MNST, refused), CELH was stopped at the
export check before anything was spent, and nothing was re-rolled.

| name | sleeve | export check (2026-10-30 exports) | assembly | cost (run) | lean / proposal | R1 | UNTRACEABLE / caveats |
|---|---|---|---|---|---|---|---|
| MNST | quality | passes | **refused**: `FreshnessError`, share-basis mismatch | $3.33 (`373c8ffc`, 7 calls, 0 failed) | none (no page) | not computed on a page | none (no page) |
| CELH | overshoot | **refused**: material row Other Unusual Items, LTM ≠ its four quarters | not run | $0 | none | — | — |

**MNST — what landed and what refused it.**
- **Followed.** `data/followed.json` gains MNST under `quality`, `followed_since` 2026-11-02, the
  reason quoting the operator verbatim. The SEC ticker-file slice gains MNST's one row in each file
  (`tests/fixtures/sec_reference/`, `build_sec_reference_fixture.py`), as its pin requires of a new
  fleet name.
- **The export check passed** (main `60151ccc`'s own readers, read-only on Drive):
  - 11 files, one export per kind (`CiqBundle.from_files`);
  - all 18 money panels state USD / US Dollar (`stated_currency`);
  - no press-release column as the newest IS, BS or CF column of either Financials export (#868/#872);
  - `estimates_as_of` ≥2026-10-27;
  - LTM against its four quarters (`ltm_quarters.check`): 6 rows checked, 4 agree, 2 unverified
    (Impairment of Goodwill −86.3 and Asset Writedown −38.4, each in one quarter only, both
    reconcile). No row is material, so none could refuse.
- **Synced** to `mosaic-theory-ta/data/manual/ciq/MNST/`, a new folder, so nothing was archived. All
  11 files hash-equal to Drive, with no symlinks. The primary checkout's `data/manual` IS a symlink to
  the Drive folder, so "the primary's copy against Drive" is one copy read twice, not a comparison.
  The comparison made is Drive against `-ta` after the copy.
- **Prices.** The `-ta` store held MNST's security but no bars. `vinci refresh MNST --aggs` wrote
  499, from 2024-11-04 to the 2026-10-30 close ($47.34): Polygon serves two years on this plan. SPY,
  the ≥$25B benchmark, already reached 10-30.
- **The refusal.** Assembled once, extraction version `2026-11-01.small-items`. The build ran its
  LLM phases (covenant terms 1, operating drivers 1, framing draws 5), then `_freshness_check` raised:
  *market cap implies $92.70/sh against a $47.34 close — a ratio of 0.5107x … a SHARE-BASIS
  mismatch*. No page and no mirror were written. The run record is committed.
- **Why the basis disagrees.** It is a split, and EDGAR is the side behind:
  - CIQ's comps cap is $90,802M on 1,959,100,000 shares (as of 2026-10-30), which implies $46.35, in
    line with Polygon's split-adjusted closes.
  - EDGAR's newest cover count, which `stock_info.shares_out` reads, is **979,525,882**
    (`dei:EntityCommonStockSharesOutstanding`, counted 2026-07-31, 10-Q filed 2026-08-07,
    `0001104659-26-092193`). $90,802M over it is the $92.70.
  - Polygon's splits reference lists a **2-for-1 executed 2026-08-11**, four days after that 10-Q.
    1,959.1M is 2.0000 × 979.5M.
  - So no CIQ re-export can clear it, as the error says. EDGAR's next cover count, on the Q3 10-Q,
    can.
- **The refusal fires after the spend.** The LTM check runs before any LLM call (`assemble.py`
  ~1029), but the cap reconciliation runs after them (`_freshness_check`, ~1156), though it reads
  only `stock_info`. That is why this refusal cost $3.33. Found, not fixed: it is a code change
  outside this pass.

**CELH — refused at the export check, not synced, not followed.**
- Bundle, currency (USD on all 18 panels), press-release columns (none) and `estimates_as_of`
  (≥2026-10-27) all pass.
- **Material row Other Unusual Items ($M).** It clears 5% of LTM revenue (3,047.274 $M). Its LTM
  reads **−418.8**, but its four quarters add to −246.7 (Q3-25) − 86.8 (Q4-25) + 9.373 (Q1-26) −
  80.9 (Q2-26) = **−405.0**: 3.29% apart, over the 2% tolerance. The assembler refuses this before
  it spends, so the brief's rule stopped the name here, with no sync and no follow entry.
- **Where the gap is.** The quarterly export's 2025 quarters do not add to its annual FY25:
  - Merger & Related Restruct. Charges: FY25 −57.9 against quarters (−, −21.7, −15.3, +4.2) =
    −32.8, **25.1** apart;
  - Other Unusual Items: FY25 −347.3 against (−, −, −246.7, −86.8) = −333.5, **13.8** apart;
  - 25.1 + 13.8 = **38.9**, exactly EBITDA's and EBIT's gap (LTM 671.7 against quarters 632.8; FY25
    569.7 against 530.8). The annual books 38.9 $M as unusual items that the quarterly columns
    carry inside operating income.
  - The quarterly Q3-2025 column is restatement type "NC", calculation "RUP", with a 2026-08 filing
    date. Q4-2025 is a derived "Q4" column from the 10-K, and its restructuring reads **+4.2**, a
    credit.
- Which side is right is not settled here. `ltm_quarters.refusal_message` asks that both exports be
  read before re-exporting; NKE's restructuring was the quarterly side.
- The follow entry the operator asked for, ready for the build that can use it:
  `{"followed_since": "2026-11-02", "sleeve": "overshoot", "reason": "Celsius Holdings, the
  energy-drink company, followed under the OVERSHOOT book by operator decision 2026-11-02, in the
  operator's words: \"trigger following assembly in a new session (files already added in manual
  folder) - MNST (quality) · CELH (overshoot)\". …"}`.
  Its `followed_since` is the decision's date, not the build's.

**BOTH NAMES REPORT Q3 IN EARLY NOVEMBER.** Each filed its Q3 2025 10-Q on 2025-11-07 (MNST
`0001104659-25-107944`, CELH `0001341766-25-000144`), and both reported Q1 and Q2 2026 on the same
days (May 07, Aug 06). The 2026-10-30 Key Developments exports announce no Q3 date, so the Q3 2026
10-Qs are ESTIMATED at about 2026-11-06 from the prior-year pattern. Any page built on these exports
is therefore a quarter behind its next 10-Q from about then. For MNST that 10-Q is also what clears
the refusal. One build per name after its Q3 10-Q, on a fresh export, gives a current page at the
cost of one run, where a build today would need a second one.

**WHY.** The brief's rule: a name that fails a check stops, and a refusal is reported, never
re-rolled without the operator. Both stops are data, not code: a corporate action between two
sources, and two CIQ exports that disagree with each other.

**HOW VERIFIED.**
- The export check ran main's own readers (`CiqBundle.from_files`, `stated_currency`,
  `press_release_income_columns`, `ltm_quarters.check` with `mark_material_rows`) on Drive.
- The sync compared every sha256 between Drive and `-ta`.
- MNST's refusal is the assembler's own output; the run record is
  `data/snapshots/assembly_runs/2026-11-02T12-48-42Z-373c8ffc.jsonl`.
- The share basis was re-read at $0 through the assembler's readers: `comps_market_cap`,
  `comps_shares_outstanding`, `_edgar_shares_outstanding` and `default_splits`.
- A MNST follow entry with no page leaves `tests/test_panel_emit.py` green (the grid adds a followed
  name only through its panel declarations), so no monitor day is owed. It turned
  `tests/test_sec_reference_fixture.py` red until the slice was rebuilt.

**BOUNDARY.**
- Exports: the operator's Drive folders `MNST/` and `CELH/`, 11 files each, exported 2026-10-30,
  read 2026-11-02.
- Materiality: the revenue floor alone (5% of the table's LTM revenue). The 10% market-cap floor
  can add a row only where the cap is under half of revenue; it is not here (MNST $90.8bn against
  $9.2bn, by CIQ's comps cap).
- LTM check: the annual summary's additive rows against the quarterly export's four quarters ending
  2026-06-30, tolerance 2% or 0.5 $M.
- Price bars: the `-ta` store, MNST 2024-11-04 → 2026-10-30.
- EDGAR: companyfacts through the `-ta` cache, read 2026-11-02.
- Splits: Polygon's reference, read 2026-11-02.
- Cost: list price, one run.
- Code: main `60151ccc`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $3.33 for a refused build.
- MNST is followed with no page until its Q3 10-Q. The page that answers the quality book's question
  does not exist until then.
- CELH is not followed in the machine until its exports agree. The operator's decision stands in
  this record and in STATE §5.0 row 32 (27).
