---
id:
status: shipped
date: 2026-11-17
prs: [1096]
supersedes:
superseded-by:
---

# The monitor's stale-tag row is retired, not wired. It was empty on all 78 committed freshness rows that carried it. Wired to `stale_served`, it would have flagged two debt tags among the 2026-11-11 day's seven freshness names that no reader serves, while every flag on the 26 pages is already withheld where the value is read (STATE row 11's monitor half)

**WHAT.** Removed:
- `vinci/monitor.py`: `_stale_tags`, the `FreshnessRow.stale_tags` field, and its call in
  `freshness_row`;
- `frontend/views/shared/decision-log.js`: the panel's "stale tag(s), served but not current"
  caption.

`stale_served` (`vinci/edgar/concepts.py`) stays, as a MEASUREMENT with no production reader. Its
docstring now says so and why; it no longer promises a monthly sweep that shows a human.

Committed monitor days are not re-cut (RUNBOOKS §j). They keep their `stale_tags: []` and read back
without it.

Four pins, in `tests/test_trigger_state_surface.py`, replace the old falsifier
(`test_the_stale_tag_scan_cannot_match_and_says_so`) and the render pin
(`test_the_stale_tags_reach_the_page`):
- `test_the_retired_stale_tag_row_has_no_surface`: no field, no scan, no script under `frontend/`
  reading the field or the old caption, and a row built from SMPL's committed record and page
  writes no such key;
- `test_a_committed_day_reads_back_without_the_retired_field`: every committed day reads back,
  every carried list was empty, and every other field reads back unchanged;
- `test_stale_served_has_no_production_reader`: no import of, reference to or call of
  `stale_served` in the production Python of `vinci/`, `scripts/` and `frontend/`;
- `test_the_reader_scan_sees_every_way_to_reach_stale_served`: the forms that scan sees, and
  the docstring, comment and definition it must not count.

**WHY.** Before this, the row was ACCEPTED as dead by construction. `_stale_tags` scanned the
dossier for `status == "stale"`, a value `SourceStatus` never had (PRESENT, UNKNOWN, MISSING). The
falsifier waited for `SourceStatus` to gain a `stale` member, and the row's note said wiring it
needed companyfacts in the monitor. The audit asked what a wired row would actually report.

1. **The monitor reads no companyfacts today.** `vinci/monitor.py` imports nothing from
   `vinci.edgar`. `_cmd_monitor` does hold an `EdgarClient`, for `recent_filings` only. Wiring
   would add one companyfacts read per name per day through `EdgarClient.companyfacts`, an
   existing method on the existing cache. So it is not a new fetch path, and the audit did not
   stop on that ground.
2. **On the monitor's own names it would report only false alarms.** On the 2026-11-11 day's
   seven freshness names (BRBR, EPAM, IT, MVST, NCNO, SMPL, WERN), `stale_served` names two values, both `debt_current` on the tag `LongTermDebtCurrent`:
   - SMPL, 782d behind the filer's frontier;
   - BRBR, 1,397d behind.

   No reader serves either. Net debt reads every debt leg AT the cash instant (`net_debt._at`), so
   a stopped tag reads nothing there: SMPL's reads `LongTermDebtNoncurrent` at 2026-08-29, and
   BRBR's reads `LongTermDebt` and `LongTermDebtNoncurrent` at 2026-06-30. The maturity wall
   dates itself by its filing's own period end. Its fallback, `_latest_balance_date`, takes the
   later of the two debt instants, and both names' `long_term_debt` is current. The caption would
   have said "served but not current" twice, and been wrong both times. The day's book, its
   marked positions (IT, SMPL twice, VRRM), adds only VRRM, which has a page and no freshness row,
   and `stale_served` flags nothing on it.
3. **On the 26 committed pages, every flag is withheld where the value is read.** There are 13
   flags in 11 filers:
   - **annuals withheld by `current_annual`:** TJX operating income (FY ending 2019-02-02); ORKA
     revenue and D&A (2024-06-30);
   - **no annual line to serve:** LLY capex;
   - **share counts beyond the dossier's age bound** (`_SHARES_MAX_AGE_DAYS`, 180 days; 540 for a
     filer reporting only annually): NKE (2015) and V (2010), far past either;
   - **debt tags net debt never reads at the cash instant:** TGT, MCK, SMPL and BRBR
     `debt_current`; FUBO both debt tags; TECX `long_term_debt`.
4. **`stale_served` is a weaker check than the readers it would report on.** Over the whole
   cache it flags 719 values in 409 filers. For the flow concepts, 129 of those flags, in 39
   filers, are values `current_annual` still serves:
   - **92 flags in 14 filers: its clock is wrong.** `filer_frontier` takes any tag's period end,
     and one forward-dated context moves it years ahead: International Tower Hill's frontier is
     2033-10-31, in a blob fetched 2026-06-18. `current_annual`'s docstring already names this
     defect.
   - **20 flags in 20 filers: it disagrees with the readers by design.** In 12, `annual_line`
     reads the leg, current, from the tag the filer moved it to (Douglas Emmett's capex). In 8,
     the figure is one fiscal year behind the filer's newest, which the 2026-10-27 design keeps.
   - **17 flags in 5 filers: a real gap, upstream** (below).

So staleness is decided where a value is read, and the census shows those readers cover the
monitor's names and every page. The cases they miss are reader gaps, to be fixed in the reader as the annual
readers were on 2026-10-27, not reported downstream by the monitor.

**FOUND, NOT FIXED: two reader gaps, through which the screen serves stale values.** None of the
names is on a page, in the book or in a freshness row. Whether either reaches a screen row is
not measured.
1. **A filer that moved its statements to IFRS keeps a frozen us-gaap fiscal year.**
   `filer_fiscal_year` reads only the us-gaap flow concepts, so when a filer's flows move to
   `ifrs-full`, its last us-gaap year reads as its newest, and `behind_filer` passes it. This is
   5 filers and 17 flags. The screen's snapshot serves an operating-income sign as PRESENT for
   National Steel (FY2009) and Himax (FY2017). That is FPI-readiness territory (STATE row 4).
2. **Net debt's cash instant has no age bound.** PennyMac Mortgage Investment Trust's last cash
   point is 2018-12-31 against a FY2025 filer, and the snapshot serves its net debt as PRESENT at
   $5,958M. Its SIC group (67) is not one `net_debt.not_applicable` exempts. Of the 21 cash flags,
   net debt is served on 5. Four read cash on a 2026 balance sheet, so their flag comes from a
   forward-dated frontier. PennyMac's cash is from 2018.

(A third shape was seen but not measured. `mechanical._latest_balance_date` takes the later of the
two debt instants, so it is stale when both debt tags stopped, as at FUBO. It is only the wall's
fallback when no filing period end is read, and FUBO's page reads its 10-Q's.)

**HOW VERIFIED.**
- **The rendered surface, base against head.** Every committed day's freshness panel was rendered
  by each side's `decision-log.js` under node. All 10 days are identical once whitespace is
  collapsed, and no day at base carried the caption. The bytes that differ are the template's
  empty `${stale}` line: 63 on 2026-11-11, which is 7 rows × 9.
- **The JSON.** `test_a_committed_day_reads_back_without_the_retired_field` reads every committed
  day through head's `FreshnessRow`: 82 rows, 78 of them carrying `stale_tags: []`, and every
  other field round-trips unchanged. `python -m vinci.impact run` runs the monitor consumer at
  both refs on the 2026-11-11 store frontier; its section is in the PR body.
- **Mutations, one per pin, each restored to the commit.** Each turned red the pin it was aimed
  at:
  1. `FreshnessRow` regains `stale_tags`: the surface pin and the read-back pin;
  2. the panel reads `f.stale_tags` again, and separately another view under `frontend/views/`
     reads it: the surface pin, both times;
  3. `vinci/monitor.py` imports `stale_served`, under an alias: the no-reader pin;
  4. a committed day carries `["debt_current"]`: the read-back pin.

  Round 1 of #1096's review found two pins blind. Each case below left them green at
  `ff8a4b9c` and turns them red after the round:
  5. a script in `frontend/lib/` reads `f.stale_tags`: the surface pin, which scanned only
     `frontend/views/`;
  6. `c.stale_served` referenced without a call, 7. `getattr(c, "stale_served")`, and
     8. `frontend/build.py` importing it: the no-reader pin, which read only calls and imports in
     `vinci/` and `scripts/`. A module-attribute CALL (`c.stale_served(...)`) was already caught.
     The scan's forms are now pinned on their own, positive and negative.
- **Never-assert-absence searches.** Vocabularies: `stale_tags`, `_stale_tags`, `stale_served`,
  `stale tag`, `MC1`, and `CoverageStatus.STALE`. The last is the screen envelope's price
  staleness, produced in `vinci/eod/features.py` and `vinci/store/store.py`; no committed dossier
  carries a stale status at any depth, under `status`, `coverage_status` or `value_status`.
  `git log -S` was run for `_stale_tags` (#552, #556, #557, #910), `stale_served` (#531, #552,
  #556, #557, #561, #808, #817) and `stale_tags` (those, and the artifact days). `git log --grep`
  was run for `stale.tag|stale_served|MC1`.

**BOUNDARY.**
- **Cache.** The primary checkout's SEC cache: 1,078 companyfacts blobs, the latest per CIK,
  fetched 2026-06-17 to 2026-11-12. The seven freshness names' blobs were fetched 2026-11-11. All 26
  committed pages' CIKs are in it. Read directly, with no TTL and no network.
- **Code.** Main `4336b542`.
- **`stale_served`'s threshold.** More than 550d (`STALE_TAG_LAG_DAYS`) behind the filer's
  frontier, per concept in `CONCEPT_ALIASES`; units are flags, each one (filer, concept).
- **"Served" / "withheld".** `current_annual(facts, concept, filer_fiscal_year(facts))` for the
  eight flow concepts; for debt, whether `net_debt` read the tag at its cash instant; for shares,
  the newest count's age against the page's date.
- **Monitor days.** The 10 committed `data/monitor/2*.json`, 2026-07-20 to 2026-11-11: 82
  freshness rows, 78 carrying `stale_tags` (the four earliest predate the field), 0 non-empty.
- **Dossier status census.** The 26 committed dossiers at `4336b542`, `mechanical.<block>.<node>`
  as `_stale_tags` read them, 3,089 nodes: 2,276 present, 410 unknown, 1 suppressed, 0 stale,
  and 402 with no `status` key. Row 11 had
  quoted 1,471 / 233 / 3 / 0, at an earlier corpus.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The monitor never reports staleness.** A stale value a reader misses reaches the page with
  nothing on the monitor to say so. The two gaps above are exactly that, today on no covered
  name. Falsifier: a covered name's page serves a value its own filer has reported past, with no
  reader withholding it. Then fix the reader. A monitor row comes back only if it beats the
  readers on this census, and `test_the_retired_stale_tag_row_has_no_surface` names this record
  when it reddens.
- **Not touched.** The 52 combined annual figures whose legs stop a year apart stay refused,
  pending the operator's reading (`docs/records/2026-10-27-combined-annual-figures-read-one-fiscal-year.md`,
  WHAT IT COSTS 1). This record does not decide them.
