---
status: shipped
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# A monitor day keys a void on the SESSION it files, as it keys a close — never on the run's `--ref`; and the web twin's freshness pin reads a fixed monitor day, not the latest

**WHAT.**
- **The monitor's void, keyed on the filed session** (`vinci/cli.py` `_cmd_monitor`).
  - #984 made a void effective from its ruling date (operator, 2026-11-11: "From 2026-11-11 on"),
    but the monitor read it with `apply_corrections(…, as_of=ref)`, the run's `--ref`.
  - Every other date-bound read of the LEDGER in the command uses the session the day is filed
    under, `now_date`: closes, entries, live verdicts. (Filings and evidence read through `ref` by
    design; they are not the ledger.) So a run on the ruling day, before that session
    closes, filed the previous session without the voided decision. A re-cut of that session keeps
    it, so the committed day did not reproduce.
  - Now the ledger is read once with no void in effect (`as_of=date.min`), for the checks made
    before the session is known (the benchmark assignments: a superset of every decision any day
    could hold). Once `now_date` is known it is read again with `as_of=now_date`, and the book,
    notes and counts read that.
  - `rows_raw` is recomputed from it, so a voided decision is never counted among those "entered
    after" the session.
- **The web twin's freshness pin** (`tests/test_web_twin_corrections_and_voids.py`, from #1001).
  - It read whichever monitor day `frontend/monitor/index.json` calls `latest`, and refused to
    pass unless that day carried a voided name. That held only until the first post-void day
    landed.
  - It now serves the page the committed 2026-11-02 day, cut before the ruling, as `latest`, and
    reads that day's freshness. The pin tests the label on a day that predates a ruling, however
    many days follow.

**WHY.** V2's first gate (2026-11-11) caught it on real data. The routine `vinci monitor` (`--ref`
2026-11-11, run at 05:xx ET, before that session closed) ran right after GOOGL's void. It filed
day 2026-11-10 with GOOGL out of the book and the freshness panel.
`test_every_committed_monitor_day_reproduces_with_a_void_ruled_after_it` re-derived it at its own
`as_of` (2026-11-10, before the ruling) and kept GOOGL. The operator's ruling says the 11-10
session keeps it. That day was discarded and never committed; V2 landed without a monitor day.

**HOW VERIFIED.**
- **Fail first, on the real case.**
  `test_a_day_filed_before_the_ruling_keeps_the_voided_decision_and_reproduces` runs the real
  `vinci monitor` three times over the suite's wired vendors, with the void row the real
  `vinci void-decision` wrote:
  - the routine run (11-11 not yet closed, so 11-10 is filed);
  - a re-cut of 11-10;
  - a run filing 11-11.

  With `cli.py` as on `main`, the routine day's book is `['IT', 'SMPL', 'SMPL', 'VRRM']`, GOOGL
  gone a session early. With the fix, the 11-10 day keeps GOOGL, equals its re-cut and names no
  void; the 11-11 day leaves GOOGL out and names the void once.
- **The pin, fail first against a real post-void day.** The discarded 2026-11-10 day (GOOGL out)
  was placed locally as `latest` and never committed. The old pin failed ("the committed monitor
  day carries no voided name — the pin is vacuous"), and the new one passes.
- The full offline suite is green (`bin/commit`).

**BOUNDARY.**
- The real case is 2026-11-11: GOOGL's void, `ruled_on` 2026-11-11.
- The routine run was at 05:xx ET on 2026-11-11, and the session it filed was 2026-11-10.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The ledger is read twice in `vinci monitor`.** The checks made before a session is known see
  every decision, voided or not (a superset). The day itself sees the decisions in effect on its
  session.
- **A voided decision's ticker keeps its benchmark assignment.** The pre-session check now covers
  every decision, voided or not. That is right: a re-cut of any day before the ruling still marks
  that decision against its benchmark.
- **A ledger whose every decision is voided now files a day with no rows and the void notes**, where
  it used to print "nothing to monitor" and write nothing. The emptiness check reads the
  no-void-in-effect ledger.
- **Found, not fixed** (outside this diff, in the void writer): a back-dated `--ruled-on` on or
  before the latest committed monitor day would silently make that committed day unreproducible.
  `void_decision` refuses only a ruling after its own append, and the reproduction pin skips days
  on or after a ruling. The fix is for the writer to refuse a ruling date on or before the latest
  committed monitor day's `as_of`. GOOGL's void (ruled 2026-11-11, latest committed day
  2026-11-02) is not affected.
- **Scoring keys a void on its own `as_of`, the report's date,** as it keys a close
  (`exit_price_as_of <= as_of`). Each surface is consistent with its own close rule, and both read
  "From 2026-11-11 on".
- **The first GOOGL-free monitor day is the 2026-11-11 session's.** It is filed once Polygon
  serves 11-11 and this PR has merged.
