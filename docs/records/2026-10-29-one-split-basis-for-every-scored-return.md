---
status: shipped
date: 2026-10-29
prs: [855]
supersedes:
superseded-by:
---

# Every scored return divides two prices on one split basis: the sealed entry is read on the exit's basis through Polygon's splits reference, a split needs its volume, and dividend coverage is checked session by session (audit items F-D1, F-D5, F-D3)

**WHAT.** Four surfaces divided a close on Polygon's CURRENT split basis by the entry price the
ledger sealed on the ENTRY date's basis: `score_ledger`, the monitor's position marks, the
monitor's realized view (`pair_closes`) and `close-position`'s printed return. The store has been
on one basis since #796 (`adjusted=true` bars, `restate_held` rescaling held ones; #835/#846
repaired the primary), and nothing ever touched the ledger, so after a split the sealed price was
the one value left on the old basis. On main 0fa8ce4a, reproduced here: a flat stock that split
2-for-1 inside its window scored −0.5000, resolved, no note; a 1-for-10 scored +9.0000; VRRM's
real AVOID row, its frozen bars halved, marked about −50 points too low in `vinci monitor`; a
close across a 2-for-1 printed "−50.00% realized". No ledger window holds a split today (below).

- **`vinci/eod/splits.py` (new)** — `entry_on_basis` sets the series' own close for the entry
  session beside the sealed price, f = close ÷ sealed. With no split recorded after the entry
  session, f must be ~1 (`RESTATE_TOL`, 0.5%) and the sealed price is used unchanged. With splits
  recorded, f must equal their product and the return divides by the series' entry-session close,
  with a note naming the sealed price, f and each split. Anything else raises `SplitBasisError`:
  a gap no recorded split explains, or a recorded split the series was never restated for.
  `close_on_basis` puts a close's sealed entry on the exit date's basis by the splits in
  (entry, exit], the exit being a quote on its own date. The evidence is Polygon's
  `/v3/reference/splits` (`PolygonEodClient.splits_reference`, cached a day; `parse_splits`
  pinned on the four ledger names' real responses).
- **Scoring** (`score_ledger(..., splits=)`, required like `dividends`): basis = the name's newest
  stored bar. A resolved row whose reference cannot be read raises `SplitsUnreadError`; a resolved
  contradiction raises `SplitBasisError`; an unresolved one is pending and named in `row_notes`.
- **Monitor** (`_cmd_monitor`): each row's entry on the mark's basis (`PositionRow.entry_price` is
  that entry; the day's notes name the sealed price and the split); `pair_closes(..., splits=)`
  for the realized view; an unreadable reference stops the run, as unknown dividends do.
- **`close-position`** reads the splits BEFORE it appends: unreadable → refused, nothing written.
  All three paths ask the reference by the store's `eod_symbol` for the row's `internal_id`, so a
  line renamed since its decision is asked under its current ticker (review round 1).
- **F-D5** (`restatement_factor`): a split now also needs volume to move inversely by the same
  factor. A bar with no volume on either side restates nothing; a bar that moved like a split in
  price alone is NAMED (`price_only` in the ingest summary, printed by `restate-prices`), never
  dropped in silence (review round 1).
- **F-D3** (`ex_date_yields(..., sessions=)`): every session in a window on which the NAME traded
  needs a Tiingo row — its bars in the store for scoring (`eod.client.store_calendar`), its Polygon
  bars for the monitor, so a full-day halt owes no row (review round 1). An empty or unreadable
  calendar is unknown dividends, never a pass (round 0). The four-day gap rule stays as a second
  check.

**WHY.** The ledger is append-only and its sealed price is a fact; the series it is divided into
is restated by design. The fix changes how the sealed field is READ, never what is stored — the
ledger's sealed price after scoring and a close row's stored prices are both pinned unchanged. The `+restated`
tag the brief proposed as evidence is named in the note when present but does not decide: a bar
re-served after a split is on the new basis with no tag (`Store.write_prices` replaces the row,
source column included — every session inside a refresh's 30-day window, and every bar of a store
built after the split). Requiring it would refuse a correct store, pinned by
`test_a_store_read_after_the_split_needs_no_restated_tag`. F-D5 lands here because the fix trusts
restatements; F-D3 because a missing ex-date row read as no dividend.

**HOW VERIFIED.**
- *Fail first, by mutation* (`tests/test_one_split_basis.py`, 32 tests). Each fix put back to
  main's behaviour in a scratch copy reds its pins with main's values: the scoring entry (−0.5 and
  +9.0 where 0 is true; −0.4 where a move across the split is +0.2; the monitor −0.6879 where
  −0.3758 is true; every refusal "DID NOT RAISE"); the close ("= −50.00% realized"); F-D5 (the
  1.04 correction read as a split, in the unit pin and through `ingest_prices`, and bars with no
  volume restated); F-D3 (the missing ex-date row DID NOT RAISE). Negative pins: no split → the sealed
  price exactly (100.20 against a store close of 100.00, inside the tolerance, scores 120/100.20);
  the committed closes' realized returns unchanged; a market holiday owes no row.
- *Review round 1* (the coordinator's `/code-review high`). Each FIX's pin red on the head
  `b67a2467` first: a halt day raised `TotalReturnUnknownError` (the market calendar owed a row on
  2026-02-11); `KeyError: 'price_only'` twice; close-position on a line whose store symbol differs
  from its ledger ticker printed "−50.00% realized"; `pair_closes` took no `symbols`. The ledger
  names' real windows hold no halt — each name's own sessions equal the market's (VRRM 91,
  IT 70, SMPL 70 and 59, GOOGL 51, IWM 91 in (entry, 2026-10-26]) — so the halt exemption is shown
  only on the synthetic pin; the real scoring and monitor runs stay identical to main's.
- *Corpus before synthetic — F-D5.* The 2026-08-05 whole market, held bars from a copy of the
  primary store before #846's `restate-prices` against Polygon's grouped-daily for that day as the
  run fetched it: 2,341 held bars, 2,331 identical, 10 changed. The price-only rule restates 10 and
  the volume rule the same 10 by the same factors (AIXI ×7, BYND ×30, ETHA ×3, IESC ×0.5, IMMP ×20,
  LHSW ×8, NVX ×10, REAX ×10, SCNI ×10, SFBS ×0.5), each with volume inverse to 1e-6. The ten pairs
  are frozen (`tests/fixtures/splits_reference/restated_2026-08-05.json`). The corpus holds no
  correction for the volume half to catch; that half is shown only on the synthetic 1.04 bar.
- *Real runs on the committed ledger, main vs this branch, same inputs.*

  | row | surface | main | this branch |
  |---|---|---|---|
  | V-VRRM-screen2-20260617 | score 10-26 (total / price) | −0.343949 / −0.343949 | same |
  | V-IT-screen2-20260706 | score | +0.637814 / +0.637814 | same |
  | V-SMPL-screen2-20260706 | score | −0.076007 / −0.076007 | same |
  | V-SMPL-screen2-20260729 | score | −0.109444 / −0.109444 | same |
  | V-GOOGL | score | −0.083533 / −0.084128 | same |
  | VRRM · IT · SMPL · SMPL · GOOGL | monitor 10-28 position return | −0.333333 · +0.553665 · −0.007326 · −0.043248 · −0.060130 | same |
  | C-IT-screen2-20260706 · C-SMPL-screen2-20260706 | realized | +0.000000 · −0.035714 | same |
  | book | BUY−AVOID 10-28 | +0.513655 | same |

  Scoring: identical rows and report markdown, 4 pending, spread n/a; the monitor day files are
  byte-identical, and both equal the committed `data/monitor/2026-10-28.json`'s rows and spread.
  Every row's store close on its entry date equals its sealed price (4.71, 141.06, 10.92, 11.33,
  345.9). The live splits reference: VRRM and SMPL none; IT 1994–96 (three 2-for-1); GOOGL
  2022-07-18 (20-for-1) — the frozen responses exactly, so no split falls in any of the seven
  rows' windows (5 decisions, 2 closes).
- *Constructed split on real data.* The same store clone with VRRM's whole series restated as
  Polygon serves it after a split (`Store.restate_bars`, 1,293 bars): main scores the 2-for-1 at
  −0.671975 and the 1-for-10 at +5.560510; this branch scores both at −0.343949, the unsplit value,
  with the note. The other four rows are unchanged in all four runs.
- `ruff`, `mypy --strict vinci` clean; the full offline suite green (count in the PR).

**FOUND, NOT FIXED (each with its date or owner in STATE §5.0).**
1. **GOOGL's row cannot score, and IT's scores off another benchmark than the monitor's.**
   `score_ledger` applies one benchmark; GOOGL's row seals SPY. Reproduced on a store clone given
   one constructed session past 2027-03-01: `BenchmarkMismatchError` the moment GOOGL resolves. IT's
   row seals IWM while its committed assignment says MDY, so from 2027-01-16 the report scores IT
   against IWM while the monitor marks it against MDY (by reading; no guard fires). A per-row
   benchmark needs a ruling first — the sealed field or the assignment — and the store to carry
   SPY (and MDY) through each horizon: `run-monthly` ingests IWM only, and the rehearsal store's
   SPY ends 2026-07-22. Not a small change, so recorded, not built.
2. **The web's realized return divides across a split** (`frontend/lib/snapshots.js`,
   `exit_price / entry_price − 1`), outside this batch's files. No committed close spans a split.
3. **Not examined:** scenario records' per-share figures compared with a later close.
4. **`pair_closes` now needs a splits source** (review round 1, deferred). It was a pure view of
   the ledger; the realized return now depends on Polygon's splits reference, which its caller
   passes in. That coupling is why the web's stdlib twin (2) cannot follow without a source of its
   own — the realized row a monitor day carries is the one surface that has read it.

**WHICH STORE SCORES VRRM (brief item 5).** The primary checkout's `data/vinci.db`, refreshed by
`run-monthly` itself, from a clean worktree of `main` wired to the primary's store and cache
(RUNBOOKS §l). It ends 2026-08-05; the run's ingest refreshes it (~30 min at the plan's rate) and
its anchor restatement — now volume-checked — keeps the held bars on Polygon's basis. GOOGL
gets bars from 2026-08-05 on (the rehearsal store shows the same 58-bar shape). The monitor keeps
no store (it reads Polygon's grouped-daily through the HTTP cache), so only scoring depends on it.
The run now also reads Polygon's splits reference, four requests.

**BOUNDARY.** Scoring: a clone of #820's rehearsal store (the primary's `data/vinci.db` refreshed
through 2026-10-26; bars for the ledger names and IWM through 2026-10-26, GOOGL from 2026-08-05),
`as_of` 2026-10-26, the committed ledger (sha `43d77c50…`, 7 rows), main `0fa8ce4a` against this
branch, Tiingo read live 2026-10-29, the splits reference read live 2026-10-29 13:08–13:09 IST.
Monitor: `vinci monitor --out` with no `--ref`, run 2026-10-29, session 2026-10-28, a clone of the
primary's `data/cache` taken 2026-10-29 (main's run refreshed the entries older than a day; this
branch read the same). F-D5: the bars dated 2026-08-05 in a copy of the primary store (2,572,227
bars, the latest 2026-08-05) against Polygon's grouped-daily for 2026-08-05 fetched 2026-10-28
22:04 IST. Fail-first: this branch's head with each fix reverted in a scratch copy.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **A bar with no volume cannot restate.** A name whose anchor bar has none keeps its older basis;
  scoring refuses a ledger name in that state (`SplitBasisError`, pinned), and the price
  scorecard's split-step check flags the step for any other name. Falsifier: a ledger row refused
  on a split Polygon recorded while its store bars carry volume.
- **The monitor's day-old cache.** A grouped day cached before a split executed can sit beside one
  fetched after it; the check cannot see a response's fetch time. The run's own day is left out of
  the splits it counts, so most such mixes refuse; one does not (an entry cached before the split,
  a mark fetched after, on the split's own day). Falsifier: a monitor day whose split note names a
  split executed on the day of the run.
- **Scoring and the monitor now need Polygon's splits reference** (and `close-position` before it
  writes). Without `POLYGON_API_KEY` a resolved row stops, never scores unchecked.
