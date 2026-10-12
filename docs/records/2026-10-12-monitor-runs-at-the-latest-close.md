---
id:
status: recorded
date: 2026-10-12
prs: [708]
supersedes:
superseded-by:
---

# The monitor runs at the latest close, and a past day is never re-cut — operator ruling on #707's open question

**WHAT.** The operator ruled option 1 of the three in
`docs/records/2026-10-11-monitor-reads-nothing-after-its-day.md` (2026-10-12, "go ahead"): **a
moved page gets a NEW monitor day; a past day is never re-cut.** Stated so it needs no judgment:
**`vinci monitor` is run at the LATEST close.**
- **Later than the newest committed day:** the run writes a new day.
- **The newest committed day itself:** the run is the same-session re-run `write_snapshot` already
  allows.
- **A day that a later close sits after is never re-run.**

Where it lives:
- **`docs/RUNBOOKS.md` §j MONITOR DAY** — the loop, with its five steps (date, run, mirror, check,
  commit as an artifact).
- **The failure the operator meets.** `tests/test_panel_emit.py::
  test_emit_is_deterministic_over_the_committed_corpus` goes red whenever a page moves after the
  latest day. Its assertion message now names the remedy and the section, so the tempting fix — re-run
  the day it names — is answered where it is tempting. The assertion itself is unchanged.
- **STATE.md §5.0 row 5 (c)** is closed: the ruling is made.

**WHY.** #707 bounds every DATED input a day reads, but the panels, the measured rows and the
record-read fields read today's pages, records and cards. None of those has a per-item date to
filter on, so a re-cut after a later close writes later information into an earlier date; the 09-22
re-cut drew UBER's 10-09 multiple. Of the three options, the rule costs no code and was already the
practice (#705 wrote `2026-10-09.json` rather than re-cut `2026-09-22`). Versioning every document
by commit date (option 2) is kept for the day past days are re-cut for analysis. Stamping (option
3) would only label the lookahead.

**"Latest close" rather than "a new day"** is the operational form. It also settles the cases a
plain "new day" leaves open:
- **A page re-assembled Monday morning on Friday's prices:** the latest close is still Friday, so
  Friday's day is re-run on the same session.
- **A page refreshed Monday evening on Monday's close:** the latest close is now Monday, so the run
  writes a new day, and re-running Friday is out.

**HOW VERIFIED.** The changed message was shown on the real failure shape, in a worktree at
`9b426cdc`. `data/monitor/2026-10-09.json` was set aside, which makes `2026-09-22` the latest day:
the state #705 was in after UBER's page moved. The pin then fails on UBER's two panels and prints
the remedy. The file was restored and the pin is green again. Output in the PR.

**BOUNDARY.** The demonstration ran on the committed corpus at `9b426cdc`, 2026-10-12, with the
`2026-10-09` day withheld and every other file as committed. "UBER's two panels" are
`multiple_and_price` and `dilution`, out of 124 rows.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The rule rests on the operator; nothing refuses an early `--ref`.** `write_snapshot` refuses only
  when a later day FILE exists. A re-cut of the newest day after a later close, but before that close
  has a file, goes through.
  - Falsifier: a committed day file last modified in a commit made after a later session's close —
    visible in `git log -- data/monitor/<day>.json` against the session calendar.
  - A machine check is possible: refuse to write day D when any page the panels read is struck on a
    session after D. It is not built here; the ruling chose the rule.
- **A moved page can leave the panel-emit pin red until the next close** when the page is struck on
  a session later than the latest committed day and that session's file has not been written yet.
  The remedy is to run the latest close, which needs that close's prices.
