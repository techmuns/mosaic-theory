---
id:
status: shipped
date: 2026-10-27
prs: [823]
supersedes:
superseded-by:
---

# The monitor marks a row past its horizon at its horizon session's close, so the web and the scoring report read one resolved number; the three web views label that price "horizon close"

**WHAT.** `vinci monitor` (`cli._cmd_monitor`, `monitor.position_row`) and three web views.

1. **Once the run's session has reached a row's horizon, the row is marked at its horizon
   session.** The new helper `monitor.mark_session` returns the last session on or before the
   horizon, through the run's own `session_on_or_before`. The mark uses the name's close and the
   benchmark's close there, with dividends over entry → that session. A row short of its horizon
   still marks to the run's session.
2. **`resolved` is decided by the RUN's session, never by the marked one.** `position_row` gains
   `session_date`, defaulting to the marked session. A Saturday horizon therefore resolves on
   Monday's run and is priced at Friday's close, which is the scoring harness's rule 1 (#820).
   `days_elapsed` counts entry → the marked session: a resolved row reads 119/119, or 114/115 for
   a Saturday horizon priced on Friday. It is the window its return covers.
3. **A name missing from the horizon session raises, as the scoring report does.** The error names
   it as the horizon session. A resolved row is never marked on another bar, earlier or later. A
   name missing only AFTER its horizon no longer stops the run: a resolved row needs only its
   horizon session.
4. **The headline spread and `spread_open_only` read these marks.** They are computed from the
   rows, so no change was needed there.
5. **The web labels a resolved row's price as its horizon close.**
   - Decision log: the mark row reads "Horizon close" where it read "Current", and the spread card
     adds "resolved rows at their horizon close" beside its date.
   - Monitor panels: The call reads "horizon close" where it read "now". The panel payload carries
     `resolved: true` ONLY on a resolved row. A key on every payload would have made the latest
     committed day stop reproducing (`test_emit_is_deterministic_over_the_committed_corpus`).
   - Dossier: the implied-odds line reads "at its horizon close".
   - The terminal table tags the row "RESOLVED · marked at its horizon close <date>".

Not touched: the ledger, the scoring harness, the verdict mapping and every threshold.

**WHY.** Record `2026-10-27-score-on-the-horizon-close`, FOUND 1. The monitor passed the run's
close (`now_bars`) to `position_row` for every row, so a row past its horizon kept marking to the
latest session. That contradicts the module's own docstring ("the pre-registered read is at each
row's horizon date") and the 2026-08-12 ruling that a row marks "to its horizon". The mark reaches
the operator's web in four places:
- the decision log's BUY−AVOID headline and "Resolved n/N";
- each entry's "Current … @ date" and "Excess";
- the panels page's call and excess bars;
- the dossier's implied-odds line.

From the first monitor run after 2026-12-14, VRRM would have read RESOLVED there, with a different
number from the scoring report's.

**HOW VERIFIED.**

- *Fail first.* `tests/test_monitor_horizon_close.py` has 11 tests. They run end to end through the
  real `vinci monitor` command, against grouped-daily days served from the frozen real bars of #820
  (`tests/fixtures/horizon_close/vrrm_iwm_bars.jsonl`, VRRM and IWM, 2026-06-15 → 2026-10-16). The
  book is a ledger COPY holding VRRM's real row, with its horizon shortened. On main's code
  (`monitor.py` and `cli.py` reverted; tests written first), 5 of the first 7 were red and the 2
  negative pins green.
  - (+) A 2026-10-14 horizon run on 10-16 is marked at the 10-14 closes, 119 days. The spread reads
    that mark, and the table tag shows.
  - (−) The real 180-day row marks to the run's close.
  - (+) A Saturday 10-10 horizon resolves on Monday's run at Friday's close.
  - (−) Sunday's run, which reaches Friday's session, does not resolve it.
  - (+) VRRM missing on 10-14 alone raises, naming 10-14 as the horizon session.
  - (−) VRRM missing after 10-14 still marks at 10-14.
  - (+) An IWM dividend on 10-15 is outside the resolved row's window, while one on 10-13 is
    inside it.
  - The cross-surface pin: on the same bars and row, `score_ledger` and the monitor agree on the
    name's return, the benchmark's and the excess (to 1e-12).
  - The three views (node), fed the rows the real command wrote: resolved reads "horizon close" in
    each; unresolved keeps "Current" and "now".
  - Review round 0 (`/code-review high`) added 2 pins, each red before its fix:
    - a run whose own session IS the horizon names it as the horizon session when the name is
      missing (the note was keyed on `mark_day != now_date`);
    - the spread card notes horizon-close marks when only a followed row is resolved
      (`spread.resolved_n` counts screen-origin rows only).
- *Mutation.* 13 mutants were run, and every one turned at least one pin red:
  - the run's session always marked (7 red);
  - `on_or_before(run_date)` (7 red);
  - resolved from the marked session (1 red);
  - presence checked at the run's session (2 red);
  - dividends through the run's session (1 red);
  - the terminal tag dropped (1 red);
  - each of the 4 web labels reverted (1 red each);
  - the payload's `resolved` never emitted (1 red);
  - the two review-round conditions reverted (1 red each).
- *The rehearsal* (decision path; real data):
  - Setup: `vinci monitor --ref 2026-10-26 --out <scratch>` in a scratch root, on an APFS clone of
    the primary checkout's price cache. Tiingo dividends came from the primary's `.env`. The ledger
    was a COPY of `data/snapshots/decision_ledger.jsonl`. BEFORE is `origin/main` 56500bb1; AFTER
    is this branch.
  - The real ledger copy (M0): the written day is byte-identical before and after.

  | variant (ledger copy) | BEFORE | AFTER |
  |---|---|---|
  | M1 VRRM horizon 119 days (Wed 2026-10-14) | RESOLVED, marked 10-26: $3.09, −34.39%, IWM −4.20% | RESOLVED, marked **10-14**: $2.94, **−37.58%, IWM −6.14%**, excess −31.44%, 119 days |
  | M2 VRRM horizon 115 days (Sat 2026-10-10) | marked 10-26 | marked **Fri 10-09**: $2.94, −37.58%, IWM −3.52%, 114 days |
  | M3 M1 with VRRM absent from the 10-14 session | marked 10-26, silently | raises: "VRRM: no position bar for VRRM (2026-06-17 / 2026-10-14) … 2026-10-14 is its HORIZON session, and a row is never marked on another bar" |

  - Cross-surface, on the same data: `score_ledger` ran on the store copy refreshed through
    2026-10-26 (#820's rehearsal store), with Tiingo dividends, the same row, and as of 2026-10-26.
    For 119 days it gave −0.37579617834394907 / −0.061390244603395705 / excess
    −0.31440593374055337. For 115 days it gave −0.37579617834394907 / −0.035207262518595184 /
    −0.3405889158253539. Both match M1 and M2 AFTER to every printed digit.
- *Restatement.* The 6 committed monitor days (`data/monitor/2026-07-20` … `2026-10-23`, and their
  `frontend/monitor/` mirrors) hold 27 rows and 0 resolved. No committed day carries a mark this
  change would move, so none is restated or regenerated.
- *Screenshots (PREVIEW RULE).* There are 8, before and after, in
  `docs/monitor/horizon-close-2026-10-27/screenshots/`, with a README stating the provenance. The
  rehearsal day was written from a ledger copy with VRRM at 119 days and IT at 80 days, and served
  from scratch copies of the frontend.
- `decision_ledger.jsonl` sha256 `43d77c50…` is unchanged in the worktree and the primary.
- *Suite.* `pytest -m "not network"` on this branch (base 56500bb1): 6,995 passed, 533 skipped,
  38 deselected; ruff and `mypy --strict vinci` clean.

**FOUND, NOT FIXED.**
- The follow-basket comparator (`baseline.basket_return`) still has no stale-exit check (#820's
  FOUND 2). It was not in this lane.

**BOUNDARY.**
- Fixture: VRRM's and IWM's bars over 2026-06-15 → 2026-10-16, 87 sessions each, cut at 987d2b4e
  (#820).
- Rehearsal: the primary's grouped-daily cache, cloned 2026-10-27, read at `--ref 2026-10-26`. The
  ledger copy holds the 7 committed rows (5 decisions), with horizons shortened only where a
  variant names it. Returns are total return.
- Committed days: `data/monitor/*.json` dated files at 56500bb1, 6 days, 27 position rows.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A resolved row now needs the grouped-daily of its horizon session on every run. That is one more
  cached fetch per resolved row, and a failed fetch stops the run as any failed fetch does.
- A resolved row's `days_elapsed` stops at the marked session. On the web a resolved row reads
  "119/119d", not the days since entry.
