---
id: 2026-10-26-fundamental-snapshot-as-of
status: open
date: 2026-10-26
prs: []
supersedes:
superseded-by:
---

# The fundamental snapshot takes an as-of date: a replay reads only what was FILED by it, and the alias it reads is chosen from that too

**WHAT.** `compute_fundamental_snapshot(cik10, facts, *, as_of=None)` and
`EdgarClient.fundamental_snapshot(cik, *, as_of=None)` (`vinci/edgar/client.py`). With a date, every
companyfacts row FILED after it is removed before anything is read, by one new helper,
`vinci.edgar.concepts.facts_as_of`. With `None` the read is the old one, byte for byte. **No caller
passes the date yet.** The three call paths are listed below with a recommendation each, and none
of them changes behaviour in this PR.

**WHY.** `close_as_of` already refuses a lookahead on prices (`docs/engineering.md`, as-of
discipline), but the fundamentals the screen reads had no cut-off. The function took
`latest_annual(...)` of each concept over the whole blob, so a replay at a past date served the
figures EDGAR holds TODAY. The 2026-10-22 research report flagged this as the blocker for any
historical replay or extraction-eval loop (its Stage 1, the extraction gold corpus).

*The cut is on `filed`, never on the period `end`.* A `ConceptPoint` carries both. `filed` is the
day the number became public, and the docstring already calls it "the knowable / as-of date".
`end` is when the period closed, weeks before the 10-K that reports it. Later filings also
re-report the same period as a comparative, restated or not. So a cut on `end` admits two kinds of
future data: figures not yet filed, and every later restatement of a period that had already closed.
On real data (section 2 below), a cut on `end` reads WOR's restated FY2023 operating income, NFLX's
post-split FY2024 EPS, and HWM's FY2020 operating income on 2020-12-31, which no filing carried
until 2021. `filed == as_of` is kept (`<=`), as in every other as-of reader here
(`annual_eps_point_as_of`, `basis_breaks`, `_latest_quarter_ocf_positive`). A row carries a date,
not an acceptance time, so a 10-K accepted after the close on `as_of` is admitted that day.

*The cut prunes the whole blob, not the points the function returns.* `extract_points` chooses an
alias by comparing it with its sibling aliases' reach, and net debt reads a dozen tags at one
balance-sheet date. Both would still see the future even if every point they finally returned had
been filed in time. One prune before any reader runs makes all of them point-in-time without
threading a date through each one. A row with no `filed` is dropped, because its knowable date
cannot be shown. A unit, tag or namespace left empty is dropped too, so it cannot shadow another
(`points_for_tag` takes the first namespace present).

**HOW VERIFIED.** Every run used the worktree's `vinci` (`PYTHONPATH` set) on the committed
companyfacts fixtures, 43 names: 30 in `tests/fixtures/companyfacts/` and 13 in
`tests/fixtures/net_debt_shapes/`.

1. *`None` is unchanged.* All 43 snapshots were dumped as JSON on `545403de` before the edit, then
   after it with the argument omitted and with `as_of=None`. The three files are byte-identical
   (SHA-256 `b258c2e0…5600`). The prune is also lossless when nothing is cut: `as_of` = the blob's
   newest `filed`, and `as_of = 2026-10-26`, each equal the `None` read on 43 of 43 names. That holds
   on three FULL companyfacts blobs too (AMZN, WOR, NFLX, from the primary checkout's HTTP cache,
   fetched 2026-08-06 to 2026-10-19, 505–612 tags each). The fixtures are tag subsets.
2. *Restated names.* Each is read as of a date between the original 10-K and the one that restated it:

   | name | as of | read (filed cut) | latest (`None`) | a cut on `end` would read |
   |---|---|---|---|---|
   | WOR | 2024-01-15 | FY2023 op income **$212.4M**, filed 2023-07-31 → EBITDA $325.2M; net leverage 0.60x | EBITDA $133.5M; net leverage 2.14x (as of 2026-07-30) | **$29.8M**, the FY2023 figure restated after the steel spin-off (2024-07-30 10-K; max filed 2025-07-30) |
   | NFLX | 2025-06-30 | FY2024 EPS **$19.83**, filed 2025-01-27 | FY2025 EPS $2.53 (2026-01-23) | **$1.98**, restated for the 10-for-1 split, filed 2026-01-23 |
   | HWM | 2020-12-31 | FY2019 op income **$1,035M**, filed 2020-02-27 → EBITDA $1,571M; FCF sign −1 | EBITDA $2,329M (2026-02-12); FCF sign +1 | **$626M**: FY2020, which no filing carried until 2021 (max filed 2023-02-14) |

   *Boundary.* WOR as of 2024-07-29 (the day before its FY2024 10-K) still reads FY2023 as filed:
   EBITDA $325.2M dated 2023-07-31. As of 2024-07-30 it reads FY2024: EBITDA $7.2M, operating-income
   sign −1. NFLX and HWM behave the same way on their restating dates (2026-01-23, 2021-02-16).
3. *Sweep: nothing after the cut.* 43 names × 15 year-ends (2012-12-31 … 2026-12-31) = 645
   snapshots and 4,515 fields. 2,160 are present, and none is dated after its cut.
4. *The alias effect is real.* 43 names × 17 mid-years (2010-06-30 … 2026-06-30) × 8 concepts (the 5
   snapshot flows plus cash, long-term debt and current debt) were compared. In **159** cases,
   filtering the RETURNED points would read a different tag, or nothing at all, than pruning first.
   Example: AMZN capex resolves today to `PaymentsToAcquireProductiveAssets`, and nothing under that
   tag was filed by 2015-06-30. Filtering after the fact leaves AMZN's FCF UNKNOWN for every replay
   from 2010 to 2018. Pruning first reads the `PaymentsToAcquirePropertyPlantAndEquipment` AMZN was
   actually filing ($4,684M; FCF sign +1, dated 2015-04-24). This was confirmed on the full AMZN blob.
5. *Pins* (`tests/test_fundamental_snapshot_as_of.py`, 137 cases, end-to-end on the real fixtures).
   Positive: the WOR, NFLX and HWM values above, each with its trap shown to be IN THE DATA (both
   filings of one fiscal year asserted), plus the filing-day boundary and the AMZN alias. Negative:
   the 645-snapshot sweep; the pruned blob keeps exactly the rows filed by the cut, in every
   namespace, and nothing empty; a row with no `filed` is never kept. Lossless: the 43-name
   equality, and the client passing the date through. Values read as of a past date do not move when
   a fixture is refreshed, because a refresh only adds later rows, and the cut drops exactly those.
6. *Mutation: 10 of 10 killed.* (M1) `<` for `<=`; (M2) cut on `end`; (M3) prune skipped; (M4) cut
   the returned points after alias resolution; (M5) client drops `as_of`; (M6) keep rows with no
   `filed`; (M7) keep empty units; (M8) keep empty tags; (M9) prune `us-gaap` only; (M10) drop the
   blob's top-level keys. M4 was re-run with net debt still pruned, so only the alias effect
   differed: exactly one pin failed, the AMZN alias pin.

**CALLERS — none changed; each recommendation is the operator's call.**

| caller | reads | date in scope | recommendation |
|---|---|---|---|
| `vinci/screens/assemble.py:438` `enrich_with_fundamentals`, reached by the screen (`screens/run.py:157`, `vinci screen [--ref]`) | FCF sign, op-income sign, net leverage, net debt/OCF: Screen-2's non-distress inputs | `reference_date` | **Pass `as_of=reference_date`.** The same record's P/E already reads `annual_eps_as_of(..., filed <= reference_date)`, so today its two halves sit on different dates. A default run (`--ref` omitted = today) cannot read a future filing, so it would not change. Only a `--ref <past>` replay would, which is the fix. It is still a decision-path change, so it needs its own shown run. |
| the same function, reached by the dossier's maintenance route (`dossier/assemble.py` `_standalone_record` → `build_data_record`) | the same four fields, onto a committed page | `reference_date` | **Pass it.** This route already truncates PRICES to `reference_date` ("a record whose own vintage mark contradicts its value"), so the fundamentals beside them are the one unclamped read left in the record. Wiring it can move a re-assembled page, so it belongs with an artifact pass. |
| `vinci/dossier/mechanical.py:1692` (adjusted EV/leverage from the 99.1 guide) | `snap.net_debt` | `reference_date` | **Pass it**, for the same reason, with the same artifact-pass caveat. |

**Wiring the snapshot alone does not clamp those records.** The same callers read companyfacts a
second time without any cut. `enrich_with_fundamentals` builds `share_count_change_730d` from
`extract_points(facts, "shares")` over the whole blob. `mechanical._adjusted_facts` takes its
`share_pts` the same way and bounds them by period age only, not by filing date. Its P/E is the one
read that is already clamped (`annual_eps_as_of`). The follow-up should read `facts_as_of(facts,
reference_date)` once per call site and pass that blob to every reader there.

Five `EdgarClient` fakes in the suite (`tests/test_screen2.py`, `tests/test_dossier.py`,
`tests/test_orchestrator.py`, `tests/test_net_debt_one_builder.py`, `tests/test_progress.py`)
define `fundamental_snapshot(self, cik)`. Wiring a caller means adding the keyword to them as well.

**BOUNDARY.** Corpus: the 43 committed fixtures at `545403de`. They are TAG SUBSETS
(`scripts/build_companyfacts_fixture.py` `FIXTURE_TAGS` / net-debt `READ_TAGS`), so the alias count
of 159 is measured on subsets: 43 names × 17 dates × 8 concepts = 5,848 comparisons. The sweep covers
645 snapshots / 4,515 fields / 2,160 present. The restatement scan found 177 restated
(tag, fiscal-year) groups across the 5 snapshot flow concepts on the same 43 fixtures. Full-blob
confirmation covers 3 names; HWM is not in the cache. All counts were measured 2026-10-26.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The lookahead is still live wherever a caller omits the date.** That is every caller today, so
  a `vinci screen --ref <past>` replay and a maintained-name re-assembly still read today's filings.
  This PR makes the fix one keyword per call site and leaves turning it on to the operator.
  Falsifier: any replay or eval loop built on these callers before they are wired.
- **The as-of view is reconstructed from TODAY's blob.** If EDGAR ever removes or rewrites a row it
  had already served, the prune cannot restore it. This is not observed and not tested: no
  historical companyfacts snapshot is kept to compare against.
- **Day granularity.** `filed == as_of` is admitted even when the filing was accepted after that
  day's close.
