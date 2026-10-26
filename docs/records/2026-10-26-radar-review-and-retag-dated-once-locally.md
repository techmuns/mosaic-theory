---
id: 2026-10-26-radar-review-and-retag-dated-once-locally
status: shipped
date: 2026-10-26
prs: [802]
supersedes:
superseded-by:
---

# A radar review is dated on the analyst's calendar, and `anchor-retag` reads its date once: the two follow-ups #794 left

**WHAT.** Two changes in `vinci/cli.py`. Both apply #794's ruling: a HUMAN decision is dated on
the operator's LOCAL calendar (`docs/records/2026-10-24-operator-decision-dated-local.md`).

- **The radar review is dated locally.** `_cmd_themes_review` wrote
  `"reviewed": datetime.now(UTC).date()` into `frontend/radar/reviews.json`. It now writes
  `date.today()`. A review recorded between local midnight and UTC midnight (00:00–05:30 IST) had
  been stamped with the day before.
- **`anchor-retag` reads the date once.** `_cmd_anchor_retag` read `date.today()` for the default
  `decided_on` and the future-date check. After the machine's EDGAR read it read the date AGAIN,
  to ask whether the decision is made now (`decided_on == date.today()`). It now reuses the first
  read (`today`). If local midnight passed during the EDGAR call, a decision made now had been
  read as backdated, and its `machine_recipe_at_decision` was dropped. That happened whether the
  date was defaulted or typed as today.
  - **Other date reads in that command: none.** The command has exactly these two `date.today()`
    reads. It has no other clock read that produces a calendar date. The `computed_at` instant
    in `_machine_anchor` and the `layer_refreshes` log entry are machine instants and logs, in UTC
    by the convention #794 recorded.
- `tests/test_themes_draft.py::test_review_happy_writes_analyst_entry` had expected UTC's date. It
  now expects `date.today()`. Left on UTC, it would have gone red every night from local midnight
  to UTC midnight, the same failure #794 fixed.

**WHO READS `reviewed`, AND WHAT THE CHANGE DOES TO EACH.** Found by `git grep` over `vinci/`,
`frontend/`, `scripts/`, `tests/` and `.github/` for the field (`"reviewed"`, `.reviewed`,
`get("reviewed")`) and for consumers of `reviews.json`.

- **`frontend/build.py` `emit_radar_inbox_log`** copies each review into `frontend/radar/log.json`
  (`{**r, …}`). It sorts by `key`, never by `reviewed`. Effect: none. The new date passes through.
- **`frontend/views/themes/radar.js:256`**, the Log tab's "Reviewed" column, shows the string. The
  Log tab filters by decision and by name or ticker, and sorts nothing by date. Effect: the column
  shows the analyst's own day.
- **`vinci/themes/drafts.py` `_recent_precedent`** orders the drafter's few-shot precedent, most
  recent first, by the `reviewed` string. The sort is stable, so reviews on the same day keep file
  order. Effect: a review made after local midnight now sorts on the day it was made.
  - Old entries keep their UTC dates, so the two calendars sit side by side in one sort key. In a
    zone ahead of UTC, as IST is, the local date is never earlier than UTC's, so no later review
    can sort before an earlier one.
  - In a zone behind UTC, an old entry stamped just before UTC midnight could carry the next day
    and sort ahead of a newer local-dated review made that same evening. The 46 committed reviews
    hold two dates (2026-07-13 ×35, 2026-07-15 ×11) and none falls in such an evening, so nothing
    committed is affected.
- **Nothing compares `reviewed` with a scan date.** The scan date lives in the key
  (`<scan_date>:<cluster_id>`). `draft_targets` and the `--include-reviewed` path match on the
  key. The regression pin `!= "2026-07-14"` still holds the line that `reviewed` is the review day,
  not the scan day.
- **The committed reviews need no re-dating.** Of the 46, the 35 dated 2026-07-13 were seeded
  with #127. The 11 dated 2026-07-15 were written by the command and committed in #132 at
  14:22 IST, which is outside the window, and they carry the date both calendars agree on.
  - Git does not keep the time the command ran, only the commit time.
  - A run before 05:30 IST that day would have stamped UTC's 2026-07-14, and they read 2026-07-15.
    So none of them can be a mis-dated review.

**WHY.** #794's record listed both as found and not fixed. #794 changed no production code. The
radar review is an analyst's decision, in the same class as the stamp #780's review fixed. The
double read is a race between the two reads. The EDGAR call sits between them, so the race window
is as long as the network call.

**HOW VERIFIED.**

- **Fail first.** Three new pins ran against the unfixed code, in IST at 16:23 IST on 2026-10-26,
  and all three failed.
  - `test_a_review_made_now_is_dated_on_the_local_calendar_under_a_real_zone` (radar) failed with
    `'2026-10-26' == '2026-10-25'`: UTC's date was written under a UTC−12 zone.
  - Both cases of `test_a_decision_made_as_local_midnight_passes_is_still_made_now` (retag) failed
    with `KeyError: 'machine_recipe_at_decision'`.
- **The pins, as #794 writes them.**
  - The radar pin drives the real command under the process's REAL zone (`TZ` + `time.tzset()`,
    reusing #794's `_process_zone`). It always runs in the divergent case: UTC−12 before
    11:00 UTC, UTC+14 from then on. It asserts that the local and UTC dates disagree before it
    runs the command.
  - The retag pin runs the command on a copy of a committed page. The EDGAR read is stubbed, and
    the process's real zone moves to UTC+14 inside that read. It starts at UTC−12, or at UTC
    from 11:00 to 13:00 UTC, so the start zone's own midnight is at least an hour from the run.
    The local date then steps forward by one or two days at any hour, and the pin asserts that it
    did. It is run both with no `--decided-on` and with `--decided-on` typed as the start date.
- **In five zones.** The 7 date pins are the two radar pins plus five retag pins: #794's three,
  and the new pin's two cases. On the fix they were run under `Asia/Kolkata`, `UTC`,
  `America/Los_Angeles`, `<-12>+12` and `<+14>-14`: 7 passed in each zone.
- **Mutants.** Each mutant was applied to `vinci/cli.py`, run against the 7 date pins in `TZ=UTC`
  (as CI runs) and in `TZ=Asia/Kolkata`, and restored byte for byte (sha256 checked). All were
  killed in both zones. The script is in this session's scratchpad: `mutate.py`.
  - M1, the radar review back on UTC's calendar: killed by the radar real-zone pin.
    `test_review_happy_writes_analyst_entry` cannot tell the clocks apart outside the window, and
    the real-zone pin can.
  - M2, the retag re-reading `date.today()` after the EDGAR call: killed by both cases of the new
    pin.
  - M3, the retag re-reading the local clock as `datetime.now().date()`: killed by the new pin and
    by #794's `_Day` pin.
  - Runs at 10:54 and 10:58 UTC took the real-zone pins' UTC−12 branch, and a run at
    11:00:03 UTC took the UTC+14 branch. The same kills held in both.
  - After the pre-PR review moved the retag pin's start zone off UTC−12 between 11:00 and
    13:00 UTC, a rerun at 11:02:42 UTC (the UTC start branch) killed all three again.
- **Real runs, on old and new code.** Each was run once on `origin/main` `545403de` (exported with
  `git archive`) and once on this branch, in a scratch directory.
  - **`anchor-retag`, the committed BRBR page, the REAL EDGAR companyfacts fetch.** The zone moved
    from UTC−12 to UTC+14 when the fetch returned, so the local date went from 2026-10-25 to
    2026-10-27 during the call. Both versions recorded `decided_on: 2026-10-25`. The old code
    dropped `machine_recipe_at_decision`. The fix kept it as `R1_midcycle_margin_evebitda`.
    Script: `retag_across_midnight.py` in the scratchpad.
  - **`themes-review --amend 2026-07-14:T004` on a copy of the committed `reviews.json`**, under
    UTC+14 (UTC date 2026-10-26, local date 2026-10-27). The old code wrote `reviewed=2026-10-26`
    and the fix wrote `2026-10-27`. In both runs the other 45 of 46 entries were unchanged, and
    `_recent_precedent(k=1)` led with the amended review. Script: `radar_review_real.py`.
    - The component-a snapshot is git-ignored and absent from this machine. The scan's 11 matched
      clusters were therefore rebuilt from the committed `frontend/radar/log.json` match blocks:
      the review's members, plus `added`, minus `dropped`.
- **The full offline suite** ran through `bin/commit`'s gate under `TZ='<+14>-14'`, where the
  local and UTC calendars disagree. The counts are in the PR body.

**BOUNDARY.**

- **The `reviewed` readers.** A `git grep` of `vinci/`, `frontend/` (the committed JSON data
  files excluded), `scripts/`, `tests/` and `.github/` at `545403de`. Theme-intelligence hits are
  a different `reviewed`, the card review, and were read and set aside.
- **The committed reviews.** `frontend/radar/reviews.json` at `545403de`: 46 entries, and their
  `git log` commit times.
- **The other date reads in `anchor-retag`.** `_cmd_anchor_retag` at `545403de`: 2 `date.today()`
  reads. In `_machine_anchor`, 1 UTC instant (`computed_at`).
- **The mutation runs.** 2026-10-26 at 10:54 and 10:58 UTC, when the real-zone pins took their
  UTC−12 branch, and at 11:00:03 and 11:02:42 UTC, when they took the UTC+14 branch (the
  retag pin's UTC start zone at 11:02:42). All on the operator's Mac, on this change over
  `545403de`.
- **The five-zone run.** Only the 7 date pins, not the full suite.
- **The real runs.** One page (BRBR) and one review key (T004), on 2026-10-26 at about
  10:57 UTC. The EDGAR fetch was live and uncached in a fresh scratch directory.

**FOUND, NOT FIXED (outside this change's scope).**

- **`_cmd_monitor` reads the date three times** (`vinci/cli.py:2261`, `:2274` and `:2275` on
  this branch). It reads the default `ref`, then `ref < date.today()` to refuse a past day, then
  the message. No network call sits between the reads, so the window is microseconds. But a run
  with no `--ref` that straddles local midnight is refused as "a past day".
- **`_cmd_themes_forward` reads it twice** (`:3885` `ratify_date` and `:3897` `freeze_ts`, on
  this branch). A worksheet read sits between the two. A freeze that straddles local midnight
  would stamp `freeze_ts` one day after its `ratify_date`.
- **Still open from #794:** the decision ledger's `decided_at` column holds two naive clocks.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **Two calendars in one field.** Earlier reviews keep their UTC dates and are not re-dated (see
  WHO READS above). The falsifier would be a review made in a zone behind UTC, inside that zone's
  evening window, sorting out of order. Nothing committed is in that position.
- **The new pins change the process's zone while they run.** #794's `_process_zone` restores `TZ`
  in a `finally`. The retag pin's own step to UTC+14 happens inside that context, so it is
  restored as well. `time.tzset()` is POSIX-only, as #794 accepted.
- **`tests/test_themes_draft.py` now imports `_process_zone` from `tests/test_operator_decision.py`.**
  The suite already imports helpers across test modules, for example
  `from tests.test_dossier import …`.
