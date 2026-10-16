---
id: 2026-10-16-theme-intelligence-ntm-window
status: recorded
date: 2026-10-16
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — a next-twelve-months forecast covers the twelve months after it was read

**WHAT.** `timewindow.timing_of` now reads the window of an NTM forecast as the twelve months
after the figure was READ (`ntm_window`).
- An NTM forecast is one whose period, metric or quote names a next-twelve-months measure.
- The reading date is the claim's measurement date, else a period naming a single day or month,
  else the source's date.
- A period naming a longer window of its own ("2027") keeps it.
- With no reading date anywhere, the window stands as read.
- `window_of` and `timing_of` share one NTM pattern.

**WHY.** J.P. Morgan's "Software Shock" states NTM net margins "At Feb '26", read 2026-02-02. The
extraction wrote the period three ways across registries, and the timing test read three windows:

| Period written | Window read before | Now |
|---|---|---|
| `Feb 2026` (acceptance registry) | 2026-02-01..02-28: a one-month forecast, the reading date read as the period | 2026-02-02..2027-02-02 |
| `NTM` | the twelve months after the RUN's as-of, moving forward on every later reassessment: "near-term" for ever | 2026-02-02..2027-02-02 |
| `NTM at Feb 2026` (the committed fixture) | the union of both, 2026-02-01..2027-02-09 | 2026-02-02..2027-02-02 |

Closes STATE §5.0 row 32 item (8)(h2), opened by #730 as "not decisive for its action". That was
measured, not assumed — see the next section.

**HOW VERIFIED.**
- **Corpus first.** Every claim linked to every current thesis version was timed at that version's
  own as-of, under the previous code and under this change.
  - 1,773 timings changed in 12 places, all the same J.P. Morgan sentence as extracted in
    different registries.
  - Every one stays `near_term`; only its window corrects. No class moved, so no action on a stored
    record can move at its own date.
- **Actions, reassessed under both codes:**
  - J.P. Morgan acceptance copy (as of 2026-02-09): 0 of 3 actions change. 1 thesis gets a new
    version whose only change is the window text.
  - Pilot copy (as of 2026-10-14): 0 of 23 actions change, and 0 new versions.
- **The drift, pinned.** Reassessed in March 2027, the February 2026 figure is `historical`.
  Before, it read near-term.
- **Tests:** 8 in `tests/test_theme_intelligence_ntm_window.py`:
  - the committed fixture's real claims;
  - each period shape;
  - the drift;
  - the reading-date order;
  - three negatives: an own window, a non-NTM "Feb 2026", and no reading date.
  - 8 mutants, all killed.

**BOUNDARY.**
- Code: the previous branch (`claude/theme-intelligence-market-context`, dcc6e03b) against this
  change.
- The corpus: the current versions of 147 local registry copies made 2026-10-16, plus the pilot
  copy (md5 5fcc240d…) and the J.P. Morgan acceptance copy. 1,773 (claim, as-of) timings, deduped
  by claim id and version as-of.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A reassess writes a version for a thesis whose stated window text changes, with no change in
  action: 1 of 3 on the J.P. Morgan copy.
- An NTM forecast now leaves near-term once its own twelve months end, where it used to stay
  near-term for ever. *Falsifier: a thesis dropping out of RESEARCH NOW on a later reassess
  solely because its only near-term evidence was an expired NTM figure. That is the intended
  reading, but it should be seen when it happens.*
