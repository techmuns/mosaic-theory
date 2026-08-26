---
id: 
status: shipped
date: 2026-08-24
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**A FAILED RUN NOW LEAVES A TRACE — SHIPPED 2026-08-24 (`feat/run-status-visibility`), and the
gate has ONE named exception because of it.** The four-week outage was invisible on the served
surface for a structural reason, not an oversight: the frontend reads COMMITTED snapshots, a
failed run commits nothing, so "the job died" and "nobody started one" rendered BYTE-IDENTICALLY.

**TWO FACTS, AND CONFLATING THEM IS WHAT HID IT.** *Queue age* — how old the committed queue is —
was always derivable and a chip already existed for it, on the RANKER ONLY, so learning the queue
was stale meant opening the queue: the screen you are least likely to open during an outage,
because it looks unchanged. *Run outcome* — whether the last attempt worked — is **not derivable
from committed data at all**.

**THE EXCEPTION, STATED SO NOBODY HAS TO INFER IT.** `weekly-screen.yml` gained an `if: always()`
step that writes `data/snapshots/run_status.json` and pushes it AFTER the gate has already
refused. That is deliberate. The gate exists to stop bad DATA reaching main; this writes one
machine-generated file carrying no analytical claim — attempt time, outcome, run URL, remediation
— and stages it **BY NAME**, so a red run cannot smuggle its half-built snapshots out through the
same door. Pinned: `test_the_reporting_step_stages_only_the_status_file` refuses
`git add data/snapshots`, `git add -A` and `git add .` in that step.

**ABSENT IS UNKNOWN, NEVER PASS** — a missing status is exactly the state the outage was in, so
rendering it as health would restate the blind spot as reassurance. Folded into `manifest.json`
(already fetched on every screen) rather than mirrored as its own file, and OMITTED when absent.

**SURFACES.** Queue age moved to `lib/format.js` as ONE definition with three consumers (overview,
ingestion, ranker) — the ranker's private copy is gone. Run health sits on the INGESTION dashboard,
which already declares itself the freshness/health surface, with the command named
(`Actions → weekly-screen → Run workflow`, or `python -m vinci run-weekly`); the home screen gets a
one-line chip and nothing more. Analysis screens are not an ops console.

**A WORDING FIX THAT IS A CORRECTNESS FIX.** The chip said "the weekly screen may not have run" —
a missed appointment, true only while a cron existed. It now states the queue's AGE and how to run
the screen. `test_queue_surface`'s page-level pin ASSERTED that obsolete phrase, so it was
re-pointed to the invariant it actually guards (stale says so and says how stale; fresh stays
quiet) — the phrase it pinned is now the thing forbidden.

**INVARIANT (INVARIANT RULE):** `tests/test_run_visibility.py`, 8 pins, the helpers executed under
node. Mutation-verified 7/7 — absent status rendering as OK, the missed-appointment wording
returning, the home chip emptied, the ranker re-declaring its own copy, the reporting step staging
the whole snapshot dir, the manifest emitting `run` unconditionally, the ops card dropping the
command. **The home-chip mutation survived the first sweep**: the pin checked that the view
IMPORTED the helper, which stayed true while the value was emptied — the pin-the-helper trap for
the third time this session. Re-pointed to the CALL SITE with its argument.

**WHAT THIS STILL CANNOT DO:** it reports the last attempt, not a missing one. Nothing on the
surface knows a run *should* have happened — deliberately, since there is no schedule to be late
against.
