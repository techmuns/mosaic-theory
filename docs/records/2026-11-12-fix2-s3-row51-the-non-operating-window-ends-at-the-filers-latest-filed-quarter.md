---
id: 2026-11-12-fix2-s3-row51-nonop-window-anchored-at-latest-filed-quarter
status: shipped
date: 2026-11-12
prs: [1038]
supersedes:
superseded-by:
---

# The non-operating window's four quarters end at the filer's latest filed quarter, and a window ending more than one quarter before it is flagged, never refused (STATE row 51 (2))

**WHAT.** This is coordinator default 9 under the operator's delegation, not an operator ruling
(`docs/records/2026-11-12-operator-delegation-and-defaults.md`): "the non-operating window is
anchored at the filer's latest filed quarter, with a stale flag, and a shown run on all 27 pages".
- **Before** (`mechanical._nonop_window`, as #916 left it): the window ENDED at the newest quarter
  carrying all three totals (operating income, pre-tax income, revenue), filed or derived, and the
  four were the calendar's quarters ending there. When a filer stopped tagging one of the three,
  the window read years back and said nothing: TJX's page read to 2019-02-02, ORKA's to
  2021-12-31, MVST's to 2025-12-31 and SMPL's to 2026-02-28 (STATE row 51 (2)).
- **Now:**
  - **The four end at the filer's latest filed quarter**: the newest period end a 10-Q or 10-K
    states as its own (`concepts.fiscal_calendar`), up to the reference date, from facts cut at
    the page's price date (the cut assembly takes). A quarter of the four that cannot be read
    leaves the window short and is named, as before; no older quarter is read in its place.
  - **Fallback, never a refusal.** Where none of the four can be read, the window is the newest
    quarter that can be and its own four, as before.
  - **The flag.** A window ending MORE than one quarter before the latest filed quarter carries
    *"STALE: the window ends <end>, N quarters before the filer's latest filed quarter <date>,
    which has no <totals> filed or derivable"*. It is in the count's cite
    (`quality.nonoperating_quarters.source_ref`), the prose (`quality.nonoperating_earnings`) and
    a `nonoperating:` QA flag. N is counted in elapsed quarters (days ÷ 91.3, rounded), not in the
    quarter ends a filing names between them (round-0 review, below).
  - **Words that name the four's own end.** The cite's "N of the trailing four quarters to <date>
    are read" and the prose's "of the N available quarters of the trailing four to <date>" name
    where the four END, which can now be later than the newest quarter read. A sentence with no
    material quarter says "in the latest read, <date>," when the two differ, and a single material
    quarter says "This is the latest quarter read". Where the two agree, every word is as before.
  - `quality.nonoperating_quarters` keeps its shape: `window` counts the quarters READ and
    `window_end` is the newest quarter read.
- **Vintage** `2026-11-12.nonop-window-anchored-at-latest-filed-quarter`; `mechanical.py` is
  re-pinned to it. MVST and SMPL join the frozen copies (`tests/fixtures/companyfacts_frozen/
  nonop_window/`, the tracking files at main `650057f3`).
- **No committed page is rewritten.** Like row 51 (1), it reaches each page at its next rebuild.

**WHY.** R4's condition 3 reads this count, and the figure a reader divides by is an LTM one. A
window ending two quarters, or seven years, before the filer's latest quarter is not that LTM, and
a page that does not say so lets the count stand for a period it does not cover.

**HOW VERIFIED.**
- **The 27 committed pages, base `650057f3` against head, $0 and offline.** Each page at its
  reference date, on its committed companyfacts (`tests/fixtures/companyfacts/<T>.json`), cut at
  its price date (`page_price_date`). **23 pages are byte-identical in count, prose and cite; 4
  move. R4's condition 3 and the full proposal flip on none.** R4 is judged on each committed page
  with only `nonoperating_quarters` replaced, R1 standing in as
  `tests/test_r4_machine_proposal._r1` builds it, as the 2026-11-05 record judged it.

| page | ref date | price cut | the four end at, base → head | window end (newest quarter read), base → head | quarters read | material | latest filed quarter | quarters behind | STALE flag | R4 c3/proposed, base → head |
|---|---|---|---|---|---|---|---|---|---|---|
| AMZN | 2026-10-16 | 2026-11-02 | 2026-09-30 → 2026-09-30 | 2026-09-30 → 2026-09-30 | 4 → 4 | 2 → 2 | 2026-09-30 | 0 | no | T/T → T/T |
| BRBR | 2026-10-16 | 2026-10-23 | 2026-06-30 → 2026-06-30 | 2026-06-30 → 2026-06-30 | 4 → 4 | 0 → 0 | 2026-06-30 | 0 | no | F/F → F/F |
| BURL | 2026-10-16 | 2026-10-23 | UNKNOWN both | — | — | — | — | — | — | —/F → —/F |
| CNXC | 2026-10-16 | 2026-10-28 | 2026-08-31 → 2026-08-31 | 2026-08-31 → 2026-08-31 | 4 → 4 | 0 → 0 | 2026-08-31 | 0 | no | F/F → F/F |
| EPAM | 2026-10-16 | 2026-11-06 | 2026-09-30 → 2026-09-30 | 2026-09-30 → 2026-09-30 | 4 → 4 | 0 → 0 | 2026-09-30 | 0 | no | F/F → F/F |
| FUBO | 2026-08-14 | 2026-08-17 | 2026-06-30 → 2026-06-30 | 2026-06-30 → 2026-06-30 | 4 → 4 | 0 → 0 | 2026-06-30 | 0 | no | F/F → F/F |
| GOOGL | 2026-10-16 | 2026-11-02 | 2026-09-30 → 2026-09-30 | 2026-09-30 → 2026-09-30 | 4 → 4 | 3 → 3 | 2026-09-30 | 0 | no | T/T → T/T |
| IT | 2026-08-14 | 2026-08-17 | 2026-06-30 → 2026-06-30 | 2026-06-30 → 2026-06-30 | 4 → 4 | 0 → 0 | 2026-06-30 | 0 | no | F/F → F/F |
| LLY | 2026-10-16 | 2026-11-02 | UNKNOWN both | — | — | — | — | — | — | —/F → —/F |
| MCK | 2026-10-16 | 2026-11-04 | 2026-09-30 → 2026-09-30 | 2026-09-30 → 2026-09-30 | 4 → 4 | 0 → 0 | 2026-09-30 | 0 | no | F/F → F/F |
| MVST | 2026-08-24 | 2026-09-16 | 2025-12-31 → **2026-06-30** | 2025-12-31 → 2025-12-31 | 4 → **2** | 4 → **2** | 2026-06-30 | 2 | **yes** | F/F → F/F |
| NCNO | 2026-08-14 | 2026-08-17 | UNKNOWN both | — | — | — | — | — | — | —/F → —/F |
| NFLX | 2026-10-16 | 2026-11-04 | 2026-09-30 → 2026-09-30 | 2026-09-30 → 2026-09-30 | 4 → 4 | 1 → 1 | 2026-09-30 | 0 | no | F/F → F/F |
| NKE | 2026-10-16 | 2026-10-28 | UNKNOWN both | — | — | — | — | — | — | —/F → —/F |
| ORKA | 2026-10-16 | 2026-10-23 | 2021-12-31 → 2021-12-31 | 2021-12-31 → 2021-12-31 | 3 → 3 | 0 → 0 | 2025-06-30 | 14 | **yes** | F/F → F/F |
| PARR | 2026-10-16 | 2026-10-23 | 2026-06-30 → 2026-06-30 | 2026-06-30 → 2026-06-30 | 4 → 4 | 0 → 0 | 2026-06-30 | 0 | no | F/F → F/F |
| ROST | 2026-10-16 | 2026-10-28 | 2026-08-01 → 2026-08-01 | 2026-08-01 → 2026-08-01 | 4 → 4 | 0 → 0 | 2026-08-01 | 0 | no | F/F → F/F |
| SMPL | 2026-10-16 | 2026-11-03 | 2026-02-28 → **2026-08-29** | 2026-02-28 → 2026-02-28 | 4 → **2** | 0 → 0 | 2026-08-29 | 2 | **yes** | F/F → F/F |
| TECX | 2026-10-16 | 2026-11-06 | UNKNOWN both | — | — | — | — | — | — | —/F → —/F |
| TGT | 2026-10-16 | 2026-10-23 | 2026-08-01 → 2026-08-01 | 2026-08-01 → 2026-08-01 | 4 → 4 | 0 → 0 | 2026-08-01 | 0 | no | F/F → F/F |
| TJX | 2026-10-16 | 2026-10-28 | 2019-02-02 → 2019-02-02 | 2019-02-02 → 2019-02-02 | 4 → 4 | 0 → 0 | 2026-08-01 | 30 | **yes** | F/F → F/F |
| UBER | 2026-10-16 | 2026-11-06 | 2026-09-30 → 2026-09-30 | 2026-09-30 → 2026-09-30 | 4 → 4 | 3 → 3 | 2026-09-30 | 0 | no | T/T → T/T |
| V | 2026-10-16 | 2026-11-06 | 2026-09-30 → 2026-09-30 | 2026-09-30 → 2026-09-30 | 4 → 4 | 0 → 0 | 2026-09-30 | 0 | no | F/F → F/F |
| VITL | 2026-10-16 | 2026-11-06 | 2026-09-27 → 2026-09-27 | 2026-09-27 → 2026-09-27 | 4 → 4 | 0 → 0 | 2026-09-27 | 0 | no | F/F → F/F |
| VRRM | 2026-10-16 | 2026-11-06 | 2026-09-30 → 2026-09-30 | 2026-09-30 → 2026-09-30 | 4 → 4 | 1 → 1 | 2026-09-30 | 0 | no | F/F → F/F |
| WERN | 2026-08-24 | 2026-09-16 | 2026-06-30 → 2026-06-30 | 2026-06-30 → 2026-06-30 | 4 → 4 | 0 → 0 | 2026-06-30 | 0 | no | F/F → F/F |
| WLK | 2026-10-16 | 2026-11-06 | 2026-09-30 → 2026-09-30 | 2026-09-30 → 2026-09-30 | 4 → 4 | 0 → 0 | 2026-09-30 | 0 | no | F/F → F/F |

  - **MVST moves.** Its 2026 10-Qs (filed 2026-05-11 and 2026-08-10) tag operating income and
    revenue but no pre-tax income. The four now run to 2026-06-30 and 2 are read (2025-09-30,
    2025-12-31), both material: −$14M and +$51M, netting +$38M. Base read 2025-03-31..2025-12-31,
    4 of 4 material. The count stays at R4's ≥2 bar; condition 3 is false on both sides, because
    MVST's P/E basis is not GAAP.
  - **SMPL moves.** Its two newest quarters, 2026-05-30 and 2026-08-29 (fiscal Q4), carry no
    pre-tax income. The four now run to 2026-08-29 and 2 are read; nothing material on either side.
  - **TJX and ORKA are flagged, their windows unchanged** (the fallback). TJX has tagged no
    operating income since 2019-02-02, 30 quarters before 2026-08-01. ORKA has tagged no revenue
    since 2024-06-30, and its window ends 14 quarters before 2025-06-30.
  - **Each missing total was checked on the filer's FULL companyfacts**, not only on the committed
    cut-down fixtures: the primary checkout's SEC cache, fetched 2026-10-27, read-only, under every
    alias the chain reads (`concepts.CONCEPT_ALIASES`).
- **The harness reproduces the committed pages where they are current.** Base reproduces the
  committed structured count on 14 of the 18 pages carrying one, and the committed sentence on 22
  of 27. The rest have not been rebuilt since #916 (row 51 (1)).
- **The pins** (`tests/test_nonoperating_earnings.py`), 8 new. 7 fail on base `650057f3`; the
  negative pin passes on both, as a negative pin should:
  - MVST moves and is flagged (positive); SMPL moves and names "the latest read, 2026-02-28"
    (positive); ORKA falls back and is flagged (positive).
  - GOOGL, ending on its latest filed quarter, carries no flag (negative).
  - The boundary: GOOGL's real facts without its latest 10-Q's two pre-tax rows read 3 of the four
    to 2026-09-30, ONE quarter behind, and are not flagged. Base read a year back for a fourth.
  - The gap (round-0 review): GOOGL without its Q1 and Q2 2026 10-Qs and its Q3 10-Q's pre-tax
    rows ends three quarters behind, and is flagged as 3.
  - The where-clause: UBER's real facts as filed by 2026-04-30, without the one row its FY2025
    10-K tags pre-tax income on, say "This is the latest quarter read".
  - **End to end**: #1031's NIKE assembly harness (`tests/test_statement_recon_build_date.py`,
    which gains a `companyfacts` parameter) serves MVST's frozen facts and writes the
    `nonoperating: STALE …` QA flag beside the page field's same words; GOOGL's writes none.
- **Mutations.** 13 mutants of the new code, all killed: the threshold either way (`>= 1`, `> 2`),
  the QA flag dropped, the prose's or the cite's flag dropped, the four's end replaced by the
  newest quarter read, the latest quarter's missing totals dropped, the anchor at the newest end
  instead of the newest filed quarter, the where-clause either way, the no-material sentence's
  date, and the lag counted in named ends or floored.

- **The impact run, base `650057f3` against head `8c1880c6` on ONE UTC day (2026-11-12T15:13:34Z), $0.** The report reads `VALID` under `vinci.impact verify`.
  - **Fail first:** 7 of the 42 tests in the two changed files fail on base code and pass on head; none fails on head.
  - **Builds:** the $0 build ran on 17 of the 27 pages. The other 10 (BURL, GOOGL, LLY, MCK, NFLX, ROST, TGT, TJX, UBER, V) have no price history in the impact store, on either side.
  - **3 of the 17 move: MVST, SMPL and ORKA.** No other field moves, and the extraction version moves on all 17.
  - **Why its numbers differ from the 27-page run:** the impact build reads different inputs. It uses the frozen HTTP cache's companyfacts, which are newer than the committed fixtures, and it cuts at the impact store's price frontier, 2026-08-05, not each page's own price date.
    - **MVST:** at that cut its Q2 10-Q (filed 2026-08-10) is not yet filed. The four end at 2026-03-31 and 3 are read; material goes 4 → 3. The window is ONE quarter behind, so it is not flagged.
    - **SMPL:** the four end at 2026-05-30 and 3 are read. It is one quarter behind, not flagged.
    - **ORKA:** flagged, 17 quarters before 2026-03-31, its latest quarter in the cache. Its `nonoperating:` QA flag reaches the page's caveats.
    - R4's condition 3 holds or fails as in the 27-page run: MVST's 3 is still at the ≥2 bar.
  - **Synthesis requests:** each of the 3 moved requests differs in its FACTS section only. System and tool schema are the same: USER −5 +5 (MVST), −4 +4 (SMPL) and −3 +3 (ORKA).
  - **The frozen panel replays identically:** 0 of 6. The report asks the operator about the row-53 panel check, because SMPL is a panel page. This is a facts-only request move, the same shape as #1034's, so no paid panel check is run (fix request 2, batch 3 item 2).
  - **Rendering:** no committed `dossier.md` re-renders differently. The one frontend file that differs is `snapshots/extraction_versions.json`, the new vintage. No consumer (screens, ledger, scoring, monitor, theme desk, frontend build) is reached.

**ROUND 0** (`/code-review high --fix`, 3 findings):
- **FIXED: the lag counted only quarter ends some filing names**, so a run of missing filings
  hid a stale window (the gap pin above, flagged as 1 before the fix). It counts elapsed quarters
  now; no page's value moves.
- **FIXED:** the window's three new fields were optional with defaults, though they are always
  set; they are required now.
- **SKIPPED:** assembly builds the window a third time for the QA flag (the prose and the count
  each build it). It is a pure function of facts already in memory; carrying one window through
  would change the quality builder's signature.

**BOUNDARY.** Every count above is over the 27 committed `data/dossiers/*/dossier.json` at main
`650057f3`, each at its own reference date, on the committed companyfacts at that commit, cut at
the page's price date. The impact run's counts are over the 17 pages it could build, from the
frozen HTTP cache and the impact store (frontier 2026-08-05), both sides at 2026-11-12T15:13:34Z.
The units are quarters (calendar quarter ends, two ends within 7 days counted as one) and $M.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **MVST's count halves (4 → 2) at its next rebuild.** It is exactly at R4's ≥2 bar. One more
  unread quarter takes it under, and today its condition 3 is false on its EPS basis anyway.
- **SMPL's count reads 2 quarters, and its sentence says so.** Row 36 already waits on SMPL's
  Q1 FY27 10-Q.
- **The flag is a FLAG.** A stale window still feeds R4. Promoting it to a refusal is a separate
  decision (the HARD/FLAG default, row 48).
