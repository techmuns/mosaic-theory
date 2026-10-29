---
status: shipped
date: 2026-10-29
prs: [856]
supersedes:
superseded-by:
---

# Each ledger row is scored against its own benchmark: IT against MDY on the operator's ruling "Use MDY", GOOGL against SPY, and `run-monthly` ingests both — STATE §5.0 row 39 closed

**WHAT.** `score_ledger` measured every row against ONE series (IWM) and refused a resolved row
that had sealed another (#512). Two rows were exposed, both found in #855's record:

- **GOOGL** (followed BUY, sealed SPY, assigned SPY) raised `BenchmarkMismatchError` the moment it
  resolved — at its horizon, 2027-03-01, scoring would have stopped.
- **IT** (screen BUY, sealed IWM, assigned MDY) would have been scored against IWM from its horizon,
  2027-01-16, while the monitor marks it against MDY.

The changes:

- **`scoring.harness.row_benchmark`** chooses each row's series. The committed assignment
  (`data/monitor/benchmark_assignments.json`, keyed by ticker, as the monitor reads it) governs.
  A row without one is measured against the benchmark it sealed. A sealed benchmark and an
  assignment that disagree are measured on the assignment only when an operator ruling stands on
  it for THAT decision (the assignment's `entry_date` is the row's — review round 0: a ticker-keyed
  ruling would otherwise govern a later decision nobody ruled for); otherwise the disagreement is
  named and neither series is chosen (`BenchmarkMismatchError` once the row resolves, pending with
  a note before).
- **The ruling's carrier is the assignment, not the ledger.** `BenchmarkAssignment` gains
  `ruled_on` and `ruling` (both or neither). IT's assignment now carries `"ruled_on": "2026-10-29",
  "ruling": "Use MDY"`. The ledger row's sealed `benchmark` (IWM) is read, never rewritten — the
  ledger is append-only, and the assignment already recorded that it supersedes that field
  (`"supersedes": "ledger row benchmark IWM"`). This is a ruling-level mapping: one record per
  assigned name, beside the row it governs.
- **A row's series must hold the calendar's sessions** at the entry and the scoring date (the
  calendar is `benchmark_internal_id`, IWM): a series the store holds only in part — the primary's
  SPY ended 2026-07-22, its MDY 2026-08-05 — raises `BenchmarkMissingError` once the row resolves,
  rather than lending its last close as the exit.
- **`run-monthly` ingests every benchmark a row is measured against** (IWM, MDY, SPY today), where it
  ingested the calendar alone. `vinci score` and `run-monthly` both pass the assignments.
- `VerdictScore.benchmark` names each row's series. The β/α pool pairs each screen BUY's daily
  return with its own benchmark's.

**THE BASIS OF THE RULING.** The operator ruled 2026-10-29, verbatim: "Use MDY". IT is measured
against the benchmark its committed assignment names — its cap band at entry: 141.06 ×
69,965,000 shares = $9.87B, mid ($4–25B), so MDY (assigned 2026-07-21). The basis is that
assignment, **not the returns**. IT's interim marks against both series were already visible when
the ruling was made (below), and the never-tune-on-outcomes rule is honoured by grounding the
choice on the cap band, fixed at entry, alone.

**WHY.** The assignment model already said what scoring should do ("SUPERSEDES the ledger row's
`benchmark` field for scoring"); the harness never implemented it, and #512's guard refused
rather than choose. A per-row series makes both surfaces read one benchmark per row. The ruling is
the operator's because a sealed value and a later assignment are two records, and which one counts
is not the code's to pick.

**HOW VERIFIED.**
- *Fail first, on main's own code* (`c51c286a`, a scratch copy): a row sealed SPY raised
  `BenchmarkMismatchError` at resolution; IT's shape was measured against IWM (bench +0.0000 where
  MDY's move is +0.1000; main has no `assignments` parameter); `run_monthly` raised on the SPY row
  and ingested IWM alone (IWM 50 bars, MDY 0, SPY 0). `tests/test_per_row_benchmark.py`, 10 tests,
  green on this branch: a SPY row against SPY; the ruled assignment against MDY with the sealed field
  unchanged; an unruled disagreement refused when resolved and pending before; a part-held series
  refused when resolved and pending before; the negative pin (an agreeing assignment and a row
  without one score exactly as before); the committed ledger reads its committed assignments
  without a conflict; a ruling needs its date and words and governs only the decision it was made
  on; `run_monthly` end to end ingests IWM, MDY
  and SPY and measures the screen BUY against MDY (excess −10% where IWM gives 0); both production
  callers pass the assignments.
- *Real run on the committed ledger* (sha `43d77c50…`), as of 2026-10-26, interim (no row resolves
  before 2026-12-14). Store: a clone of #820's rehearsal store with MDY and SPY topped up to
  2026-10-26 from Polygon's per-symbol aggregates (one call each; IWM, MDY and SPY then hold the same
  91 sessions in 2026-06-17 → 2026-10-26):

  | row | main (`c51c286a`) | this branch |
  |---|---|---|
  | V-IT-screen2-20260706 | vs IWM: name +0.637814, bench −0.049916, excess **+0.687730** | vs MDY: bench −0.024542, excess **+0.662356** |
  | V-GOOGL | vs IWM: name −0.083533, bench −0.089715, excess **+0.006182** | vs SPY: bench −0.011686, excess **−0.071847** |
  | V-VRRM-screen2-20260617 | vs IWM, excess −0.301997 | same |
  | V-SMPL-screen2-20260706 | vs IWM, excess −0.026091 | same |
  | V-SMPL-screen2-20260729 | vs IWM, excess −0.029927 | same |

  Both IT figures are stated, as the brief asked: against IWM (the sealed series) +68.77 points,
  against MDY (the ruled series) +66.24 points. On the same store with the assignments as committed
  BEFORE the ruling was recorded, IT was held PENDING with the disagreement named and neither series
  chosen — the refusal working on the real ledger. 4 pending (screen origin), spread n/a, in all.
- *The monitor* (`vinci monitor --out`, session 2026-10-28): the day file is byte-identical on main
  and this branch — it already measured each row against its assignment, so scoring now agrees with
  it (IT +0.572384 excess over MDY, GOOGL −0.057405 over SPY).
- The full offline suite green; ruff and `mypy --strict vinci` clean.

**BOUNDARY.** Ledger: the committed `decision_ledger.jsonl`, 5 decisions and 2 closes (closes are
not scored). Scoring: `as_of` 2026-10-26, Tiingo dividends and Polygon's splits reference read
2026-10-29, the per-symbol MDY/SPY bars read 2026-10-29 for 2026-06-01 → 2026-10-26. Monitor:
session 2026-10-28, the HTTP cache a clone of the primary's taken 2026-10-29. Main: `c51c286a`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **An assignment is keyed by ticker**, as the monitor reads it, so SMPL's re-entry (2026-08-04)
  shares the assignment derived at its first entry (both IWM; no cap-band change). A re-entry whose
  band differed would need its own assignment; none exists to date.
- **A data dir without the assignments file** scores each row against its sealed benchmark, with
  no note (review round 0, skipped): the file is committed in every checkout, and refusing on its
  absence would change both callers' contract. Falsifier: a scoring report from a checkout missing
  `data/monitor/benchmark_assignments.json`.
- **The β/α regression now pools pairs against different benchmarks** (IT against MDY beside the
  small-cap rows against IWM). The pool is screen-origin resolved BUYs and holds none today.
