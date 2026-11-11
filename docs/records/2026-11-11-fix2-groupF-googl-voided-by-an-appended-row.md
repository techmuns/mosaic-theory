---
status: open
date: 2026-11-11
prs: []
supersedes:
superseded-by:
---

# GOOGL's BUY is voided by an appended row (operator ruling 2026-11-11): the VOID event, its writer and command, every reader leaving a voided decision out, and a fresh-decision id scheme. Built here; the void itself is appended only after this merges, on approval

**WHAT.**
- **The ruling** (operator, 2026-11-11, relayed by the coordinator). In their words: "we want to
  remove the buy card/ buy verdict altogether given it was done based on really old and wrong
  data and we dont want this buy verdict to interfere in future at all".
  - Mechanism: "Void by appended row (Recommended)", the #947 record's option 4, built append-only.
  - Reason: "Your words + the stale entry (Recommended)".
- **The row.** `EVENT_VOID` (`"VOID"`), id `X-<decision suffix>` (`X-GOOGL`). It carries:
  - `voids_entry_id`, naming the decision;
  - `ruled_on`, the ruling's date;
  - the reason;
  - `void_mark`: the decision's **result to date, sealed at the void**. This is the monitor's own
    mark of the decision at the last session it could read (entry as read, price and date, total
    return, benchmark and its return, excess), so the removal is seen and can never read as a
    hidden loser.
  - The shape guards refuse a void without a target, reason, ruling date or mark; a void of itself;
    close or correction fields; facts; and the void fields on any other row.
  - `voids_by_decision` raises on a void naming no decision, or a decision voided twice.
- **The writer.** `ledger.correction.void_decision`, and `vinci void-decision ENTRY_ID --reason
  --ruled-on [--dry-run]`.
  - The mark is taken by running `vinci monitor` into a scratch root and reading back the
    decision's own row (`cli._void_mark`), never by a second computation. The mark's entry price
    is on the mark's split basis, so it is matched to the decision by its entry DATE. A monitor that
    cannot mark is a refusal, not a traceback (review round 0).
  - It refuses: an unknown decision; a second void; a closed decision (its outcome is realized); a
    blank reason; a mark taken on another entry date than the one the decision is read at; and a
    ruling dated after the void's own append (review round 1, below).
  - It re-seeds the store's ledger table from the committed snapshot first (additive), as
    `correct-entry` does.
- **The readers.** A voided decision, its correction and its void leave:
  - scoring (`scoring/harness.py`): no score, so no count, spread, sleeve curve or listing. The
    report names the void ONCE, with its sealed result;
  - the monitor: `decision_rows` (so the book, the spread, `live_verdicts` and the supersede guard
    at `cli.py`) and `apply_corrections`, the first thing `vinci monitor` does, which names the void
    once in the day's notes. Committed monitor days are dated artifacts and stay as they are, and
    each one still reproduces (below);
  - `close_position`, which refuses to close a voided decision;
  - `correct_entry`, and `vinci correct-entry`, which refuse to correct one.
  - Input-provisioning reads (`orchestrator.run_monthly`, `vinci score`: which benchmarks to
    ingest, how far back) still see the decision. They only widen what is fetched (GOOGL's SPY) and
    change no value.
- **A void is in effect FROM ITS RULING DATE, as a close is from its exit** (review round 1:
  Codex P1 on #984). The operator answered on 2026-11-11: "From 2026-11-11 on (Recommended)".
  - A report cut before `ruled_on` reads the decision as it was live then:
    `score_ledger(as_of=2026-11-06)` and `vinci monitor --ref 2026-11-06` keep GOOGL. One cut on
    or after 2026-11-11 leaves it out.
  - `voids_by_decision(entries, as_of=…)` returns only the voids ruled by then.
    `apply_corrections(raw, as_of=…)` and `decision_rows(raw, as_of=…)` keep a decision whose void
    is not yet in effect. `decisions_as_of` and `live_verdicts` pass their date through.
  - Where the date comes from: scoring reads its own `as_of`, and `vinci monitor` its `--ref`.
  - The orphan and double-void checks still run on every void.
  - Without `as_of`, every void counts. That is the ledger as it stands now, which is what the
    writers read: no close or correction of a voided decision, ever.
  - **The web needs no date.** Its twins (V3) key on the void row's presence, and the writer
    refuses a ruling dated after the void's own append (local date). So every committed void is
    already in effect on the day any page is built.
  - **This reverses one result of the first dry run.** That run showed GOOGL gone from
    `monitor --ref 2026-11-06`. That no longer holds: at 2026-11-06 GOOGL is in the book, and it is
    gone from 2026-11-11 on (the dry run below).
- **A fresh decision after a void, or after a close** (the id scheme the #947 record's option 3
  needed). This is the operator's ruling of 2026-11-11, asked by the coordinator, whose answer was
  "After a close or a void (Recommended)". A new decision on a name is allowed once its earlier
  decision is CLOSED or VOIDED, and refused while one is open. Each new decision is a separate
  call, scored from its own entry.
  - `log_verdict` takes its id from `next_decision_id`: `V-{candidate}` first, then
    `V-{candidate}-{n}`. It refuses while an earlier decision of the candidate is still open.
  - A close, correction or void is named from its DECISION's id (`follow_up_id`): `C-GOOGL-2` for
    the second decision. Every committed row keeps its id (pinned over the corpus).
  - `close_position` by candidate names the one open decision.
  - `log_verdict` changes in its one id line only. **The vote rule (#982) merged first**, adding
    its ten-draw confirmation, `machine_tally` and the transcript check to `log_verdict` and
    `log-verdict`. Main merged here with no textual conflict, and both hold: `log_verdict` carries
    `next_decision_id` and `machine_tally`, and none of #982's lines is dropped.
  - **The confirmation's paid draws never run for a log the id scheme refuses.** `log-verdict`
    drew the ten syntheses BEFORE `log_verdict`'s write, so a log on a candidate with an open
    decision would spend them and then be refused. `next_decision_id` is now asked first.
    - `test_a_log_on_an_open_decision_is_refused_before_the_confirmations_draws` failed on the
      merge: the confirmation was reached.
    - Once the decision is voided, the same log reaches the confirmation, as any fresh decision
      does.
  - **A void needs no confirmation.** It is not a verdict and never calls it. A fresh GOOGL
    decision goes through it like any other. GOOGL's committed page is one of the backfilled pages
    the confirmation refuses ("cannot identify" its transcripts; #982 pins exactly this), so a
    fresh GOOGL decision needs that page rebuilt first.

**WHY.** The operator's ruling above. The mechanism is generic, but only a ruling applies it:
`--reason` and `--ruled-on` are required, and the void is appended through the command, never by
hand.

**HOW VERIFIED.** See the PR's "Cross-setup validation (deterministic)".
- **Fail first.** On `946943ec` the 31 tests in `tests/test_ledger_void.py` cannot import
  (`EVENT_VOID`, `VoidMark`, `void_decision` and `next_decision_id` do not exist). Each reader and
  guard was then mutated out in turn on head, and its own test went red:
  - scoring keeps a voided decision;
  - `decision_rows` keeps one;
  - `apply_corrections` keeps one;
  - `close_position` closes one;
  - `correct_entry` corrects one;
  - the writer seals a mark on another entry;
  - a void row needs no ruling date;
  - the open-decision refusal is removed;
  - a close is named from the candidate, not the decision.
- **The sealed mark is the monitor's own row.** End to end, `_void_mark` matches the GOOGL row of
  a `vinci monitor` day on the same wired vendors.
- **The dry run on a `.backup` of the primary's store**, re-run for review round 1 at both refs.
  - The copy's sha256 is `b66a6979…`, of the primary at `b237f3a0…`; the primary was the same
    before and after.
  - It used the real `vinci void-decision V-GOOGL` on a scratch tree, appending and exporting there
    only.
  - Live reads were the seven ledger names and benchmarks: Polygon 12, Tiingo 10.

  | Reader | Before the void | After the void |
  |---|---|---|
  | Monitor `--ref 2026-11-06` (before the ruling) | GOOGL BUY, followed/quality, 340.65 @ 08-27, −16.35%, excess −11.94 pts; primary spread +66.89 | **the same, byte for byte**: GOOGL in the book, no void named; primary spread +66.89 |
  | Monitor `--ref 2026-11-11` (marks 2026-11-10) | GOOGL BUY, −15.58%, excess −13.08 pts; quality rows `['GOOGL']`; primary spread +71.64 | no GOOGL row; quality rows `[]`; one "VOIDED by X-GOOGL" note; primary spread **+71.64** |
  | Scoring, store copy, as of 2026-11-06 | screen pending 4; GOOGL's correction noted | the same; no void named |
  | Scoring, store copy, as of 2026-11-11 | screen pending 4; GOOGL's correction noted | GOOGL out, the void named once; screen pending 4 |
  | Snapshot | 9 rows | 10 rows: `X-GOOGL` added, the 9 byte-identical |

  - **The first dry run's 2026-11-06 result no longer holds.** It showed GOOGL gone from
    `--ref 2026-11-06`. Under the operator's answer ("From 2026-11-11 on"), GOOGL stays in every
    report cut before 2026-11-11 and leaves from 2026-11-11 on.
  - The result to date the void would seal, appended today: **−15.58% vs SPY −2.51%, excess −13.08
    pts**, total return, marked 287.38 on 2026-11-10. The first run marked 288.15 on 2026-11-09.
    The real append (V2) seals its own day's mark.
  - The scoring report's `by_sleeve` is empty, because no row has resolved. On flat synthetic bars
    to 2027-03-19, GOOGL resolves into `by_sleeve["quality"]` before the void and is in no score or
    curve after, with the PRIMARY spread equal
    (`test_scoring_leaves_a_voided_decision_out_and_the_primary_spread_does_not_move`).
- **Every committed monitor day reproduces with the void appended.** For each of the 9 committed
  `data/monitor/<day>.json` (2026-07-20 to 2026-11-02), the book the code derives at the day's
  `as_of` from the ledger plus GOOGL's void names the day's own rows
  (`test_every_committed_monitor_day_reproduces_with_a_void_ruled_after_it`). On `b377795e`, 7 of
  them (2026-09-16 to 2026-11-02) lost GOOGL.
- **Round 1's pins fail first.** On `b377795e` (its two readers shimmed to accept and ignore
  `as_of`), 4 tests fail on base behaviour:
  - the monitor in both directions;
  - the committed days;
  - the 2026-11-06 report;
  - a ruling dated after its append.
- **The suite reads a committed void** (found while fixing round 1, as #955 found for corrections).
  It was checked on a simulation of V2: this round's code, GOOGL's void appended to the committed
  ledger, and the frontend rebuilt.
  - **Before:** 21 tests in 8 files went red only with the void committed:
    - the correction tests and the void command's own (both act on V-GOOGL, which the writers
      rightly refuse once voided);
    - six monitor tests whose synthetic bars left out a voided decision;
    - two that enumerate the committed decisions.
  - **The fix.** Each now reads the ledger its subject needs: as sealed, without VOID rows, or
    every decision with `as_of=date.min` (before any ruling). Coverage is kept: SPY's only
    resolved row is still GOOGL's.
  - **After:** all 37 test files that read the ledger or the monitor pass on the 9-row ledger and
    on the 10-row one. V2's artifact commit therefore turns nothing red.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The void is permanent.** The ledger refuses an UPDATE or DELETE, and the rule is one void per
  decision. It is appended only after this PR and V3 merge and the operator approves the dry run,
  as an artifact-only PR with the store's sha256 before and after.
- **Timing.** The scoring path changes before VRRM is scored on 2026-12-15, and VRRM's
  monthly-scoring rehearsal (STATE row 38, by 2026-12-07) must run on `main` with the void in.
  The ORDER is V1 → V3 → V2 (coordinator, 2026-11-11):
  - this PR (V1);
  - then the web twin (V3);
  - then the void's artifact PR (V2), the append itself, only after V3 merges.

  All three land well before 2026-12-07. The reason for V3 before V2 is that the web never shows a
  voided BUY, which serves the ruling ("remove the buy card").
- **The frontend does not apply a void until V3.** `frontend/build.py` and `snapshots.js` skip a
  VOID row (any `event` row), so nothing breaks; they just do not take the decision off the page.
  Because the void is appended only after V3 merges, no committed void ever meets that frontend. V3
  takes GOOGL off the live book and the card, and shows the voided call once in an audit tier.
