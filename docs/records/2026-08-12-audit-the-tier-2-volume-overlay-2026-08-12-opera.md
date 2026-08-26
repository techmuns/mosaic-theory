---
id: 
status: recorded
date: 2026-08-12
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

### AUDIT — THE TIER-2 VOLUME OVERLAY (2026-08-12, operator-prompted; NO CODE CHANGED)

Recorded before touching anything, per the operator's instruction. Prompted by a plain question about
the new queue column — *"what does 'very heavy' mean, relative to what, and is the volume buying or
selling?"* — which the column could not answer. Corpus: the 36 backdated queues + the committed
2026-07-29 queue; script `volaudit.py` in the session scratchpad, NOT committed.

**WHAT THE FIELD IS.** `volume_spike = latest session's SHARE volume ÷ the 90-calendar-day average
share volume` (`vinci/eod/features.py:214`). One day. No price direction, no multi-day trend. Banded
at 0.80 / 1.50 / 3.00 into +0.05 / 0 / −0.02 / −0.05 (`vinci/rank/ranker.py:252`).

1. **THE LABEL "heavy distribution" IS AFFIRMATIVELY WRONG, demonstrated on the live queue.**
   Distribution means institutions selling into strength; the input contains no direction, so the
   word is a guess. On the committed 2026-07-29 queue **2 of the 10 "heavy distribution" names
   closed UP that session — VRRM +22.0% on 3.6× (RANK 5) and SPRY +2.8% on 3.2×.** A +22% day is the
   textbook opposite of distribution, and the overlay docked it −0.05. This is a small
   free-conclusion welded into a label: the machine naming a MECHANISM (who traded, and why) from a
   MAGNITUDE that cannot contain one. "exhausted" is the same error in the quiet band, milder.
2. **THE BAND DOES NOT SURVIVE THE DAY — the most serious finding.** Across 78,984 adjacent session
   pairs, **43.1% change band**. Mean sessions a band had already lasted at the as-of: quiet 3.8
   (n=3,111) · normal 2.3 (n=4,339) · elevated 1.6 (n=1,135) · **very heavy 1.3 (n=191)**. The
   penalty bands are ONE-SESSION EVENTS. VRRM's label describes a single day (2026-07-29) and is
   read on 2026-08-12 — a one-day condition, two weeks stale, moving the score by which day the
   screen happened to run.
3. **DIRECTION SEPARATES AT EVERY BAND** (120d forward vs own sector, ex-sunk): quiet +2.07
   (1,084 up / 1,414 down) · normal +2.49 (1,522/2,082) · elevated +1.51 (389/550) · **very heavy
   +11.14** (55/104: up-day mean +6.15 vs down-day −4.99). CAVEAT ON THE HEADLINE CELL: n=55, median
   **−7.42**, up-rate 45% — tail-driven, like every other mean this session. The trustworthy part is
   the **consistent SIGN of the gap across all four bands**, not the size of any one cell.
4. **DOLLAR VOLUME BEATS SHARE VOLUME, and we ship shares.** Decile spread vs own sector at 120d:
   share-volume spike +1.28 (quietest −1.28, heaviest −2.56); **dollar-volume spike +3.07 (quietest
   **+0.78** — the only positive cell in the audit — heaviest −2.29)**. `adv_90d_usd` is already
   computed and unused here.
5. **FALSIFIED — my own hypothesis.** I expected the share ratio to be contaminated by the drawdown
   (a name down 80% trades more shares for the same dollar interest, so the ratio would partly
   re-measure the depth axis). `corr(drawdown %, share-volume spike) = −0.022` over 7,200
   name-months. **Withdrawn.**
6. **UNMEASURED AND STILL OPEN:** (a) **earnings** — a spike the day after results is mechanical and
   happens to every issuer 4×/yr; we hold 8-K item 2.02 dates and do not use them; (b) **index
   events** — Russell reconstitution / S&P adds produce enormous volume carrying nothing about the
   business; (c) **split-adjustment hazard** — the ratio spans 90 days and `adjusted=true` plus the
   24h netcache TTL can restate volumes inconsistently mid-window (the documented FUBO reverse-split
   incident class; a HAZARD here, not a confirmed live bug); (d) **coverage is lopsided** — 122/331
   names (37%) take the +0.05 bonus and 11/331 (3%) the −0.05 penalty, so the "bonus" is nearly a
   baseline and the penalty fires too rarely to establish (32nd pct in the 2026-08-12 panel = noise).

**THE STATISTICAL USE AND THE DECISION USE ARE DIFFERENT JOBS, and the field is fit for one.** The
same one-day input produced the only technical result that cleared the panel's full bar (`≤0.80×` →
+3.58 pts at 180d sector-relative, 100th pct, same sign in all four phase blocks). A noisy signal can
carry a real mean effect across thousands of observations. It does not follow that a condition which
lasted 1.3 sessions two weeks ago belongs on a row a human reads to decide where to spend a week.

**⚠ GUARDRAIL — THESE NUMBERS MUST NOT SET THE PARAMETERS.** Every figure above is measured against
FORWARD RETURNS. CLAUDE.md §Project guardrails: *"Never tune on forward returns … set by
FACE-VALIDITY — NEVER by what would have paid."* So findings 3 and 4 may NOT be used to add a
direction term, re-band the thresholds, or switch the unit *because those readings paid better*.
They say the column is worth fixing; they may not say what it becomes. **The fixes that are
legitimate stand on face-validity ALONE, with no return data:** a reading that flips 43% of the time
is too noisy to call a state (a property of the INPUT); "distribution" claims a mechanism the input
cannot contain (semantics); dollar volume is the right unit for a series whose price moves
(measurement principle). Anyone implementing this must carry that justification, not this table.

**BEARING ON PR #420 (the queue column), stated plainly by its own author:** #420 does not create
the wrong label — `"heavy distribution"` has been in the snapshot and the CLI all along — but it
**does put it in front of the analyst on rank 5**, where it was previously invisible. That is a real
increase in exposure to a known-wrong string, and it is the operator's call whether #420 merges as
built (faithful to what the scorer emits today, labels corrected in a follow-up) or waits for the
label fix. Recommended sequence if it waits: emit `volume_spike` structurally (item 9) → retire the
band words and lead with the number + its date → only then revisit the scorer, separately and on
face-validity grounds.

**OPERATOR CHOSE: HOLD #420, FIX THE LABELS FIRST (2026-08-12).** Done, in the same PR:
`volume_spike` emitted structurally on `RankedCandidate`; `volume_overlay()`'s bands renamed to
plain magnitudes that state their basis (`quiet / normal / elevated / heavy`, each `"(N× vs 90d
avg)"`) — which also answers the question that opened the audit, *"relative to what?"*, everywhere
the string appears including the CLI; the queue cell now LEADS WITH THE RATIO (`0.39×`) per the
page's own "columns lead with the interpretable quantity" rule, with the band word demoted to the
hover and a one-session disclosure on the column header. **Every ± value and every threshold is
untouched** — re-banding on the audit's forward-return numbers would be tuning on outcomes.
Guarded by `tests/test_rank.py::test_the_volume_label_describes_magnitude_and_never_names_a_mechanism`
(positive: each band states ratio + basis; negative: `distribution`/`exhausted`/`accumulation`/
`panic`/`smart money` can never come back) and by two end-to-end render pins, one per path.

**THE FIX IS DORMANT UNTIL THE QUEUE IS REGENERATED — AND A REGEN IS NOT A REFRESH (found while
checking whether it could just be re-run).** `vinci rank` reads committed snapshots with no DB and
no network, so regeneration looked free. It is not: the committed **queue is 331 rows stamped
2026-07-29**, while the committed **`candidate_records.jsonl` is 280 records stamped 2026-08-10**.
Re-ranking from today's records would **ADD 44 names, DROP 95, keep 236** — that is ADVANCING the
queue to a newer screen, with ~40% turnover and analyst workflow states keyed to tickers, not
refreshing a label. The frontend therefore keeps a legacy fallback that renders the old string
verbatim rather than digging the ratio out of it, so a pre-field snapshot stays correct-but-old and
pinned by its own test.

**REGENERATED ON THE OPERATOR'S INSTRUCTION, 2026-08-12 (separate artifact commit).** `vinci rank`
with defaults — matching the replaced artifact's exact configuration (no `--cause-file`: all 331 old
rows were already `unclassified`; no `--structural`: the old queue carried 0 disqualifiers, so the
scan has NOT been applied and this regen does not change that; `--md-top` 50). Blast radius checked
BEFORE overwriting: of the 95 names dropping out, exactly **one (NCNO) has a committed dossier and
none has a ledger entry** — no verdict is orphaned. Result: **280 rows @ 2026-08-10**, all carrying
`volume_spike`, bands quiet 109 / normal 121 / elevated 39 / heavy 11, and **zero rows carrying a
retired word**. Full offline suite green ON the freshly-written artifact (2,220 passed; skips 59→60
as the legacy-fallback pin correctly steps aside). **#420's merge precondition is now satisfied.**

*A demonstration of finding 2, unplanned:* **VRRM** — the +22%-on-3.6× name that made "heavy
distribution" demonstrably wrong — reads **`quiet (0.63× vs 90d avg)`** on the 2026-08-10 tape. Same
name, opposite band, twelve days apart. That is the 43% flip rate in a single observation.

**WHY THE QUEUE LAGGED — a structural gap, not a sync bug (found while regenerating).** The weekly CI
job runs `python -m vinci run-weekly` → `run_weekly()` (`vinci/orchestrator.py:31`), which refreshes
the universe, runs the SCREEN and exports snapshots — **it never runs the ranker.** `ranked_queue.jsonl`
is written only by the manual `vinci rank` (`cli.py:273`), and no CI workflow invokes it (searched
`.github/` for both `vinci rank` and bare `rank`). So `candidate_records.jsonl` advances every week
and the served queue does not move until a human runs the ranker — which is exactly how it came to be
12 days behind. **Today's regen closes the instance, not the mechanism: the next weekly screen will
leave the queue behind again.** Options for the operator: add `rank` to `run_weekly()`; add a rank
step to `weekly-screen.yml`; or accept the manual step and add a staleness banner to the queue page.
Recorded per the OPERATOR-ACTION RULE.

**CLOSED 2026-08-12 — the operator chose option 1; `run_weekly()` now ranks.** The screen exports
its snapshots, then the queue is written from that snapshot through
`orchestrator.rank_from_snapshots()` + `write_queue_snapshots()` — **the ONE ranking path, which
`vinci rank` was refactored onto in the same change**, so a CI-built queue and a hand-built one are
provably the same object rather than two implementations that agree today. Verified by re-running
the CLI after the refactor and byte-diffing: `ranked_queue.jsonl` and `.md` came back **IDENTICAL**
to the committed artifact, so the extraction changed no behaviour.
- **Defaults reproduce the manual invocation.** No cause annotations (they need an operator-supplied
  file) and **NO `--structural`** — that is a network 8-K scan, it is off by default in the CLI, and
  it SINKS names. Putting a demote channel on a cron is a decision-path change, so it stays an
  explicit human act. `QUEUE_MD_TOP` / `QUEUE_ADV_FLOOR` now live in the orchestrator and argparse
  reads them, so the two callers cannot drift on the numbers either.
- **A bug the new test caught before it shipped:** `load_candidates_from_snapshot` RAISES on a
  missing file, so the first draft made `run_weekly` die between the screen export and the queue
  write on any fresh checkout. An absent `candidate_records.jsonl` is now read as "nothing screened
  yet" → return `[]` → caller skips the write and leaves the existing queue untouched. Only the
  missing FILE is tolerated; a malformed one still raises, and `run_weekly` returns `ranked` in its
  result dict so a screen that found candidates while the rank found none is visible in the job log.
- **Guards, each mutation-tested:** the weekly job calling the ranker at all; both callers sharing
  the one path (AST over the unparsed function bodies, so a mention in a comment cannot satisfy it);
  the writer-side sector/industry enrichment surviving — a weekly job that called `rank_candidates`
  directly would have emitted a queue with both fields `None` and quietly broken the frontend's
  industry column and cluster roll-up; and the missing-file case above.
- **Option 3 ALSO taken, 2026-08-12 — the staleness banner is in.** Option 1 fixed the mechanism but
  not the failure it leaves: the weekly job is the only automated writer, so a week where CI does not
  run still freezes the queue, and the page's as-of was a date the reader had to do arithmetic on.
  A queue older than **10 days** (the weekly cadence plus slack — face-validity, tuned on nothing)
  now renders `⚠ queue is N days old — the weekly screen may not have run`, with the remedy on hover.
  Pinned positive AND negative against the RUNNING clock (a 40-day-old queue warns; one screened
  today stays quiet), so neither pin rots as the committed snapshot ages; both mutation-tested.
