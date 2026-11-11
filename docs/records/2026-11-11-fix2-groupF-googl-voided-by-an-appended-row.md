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
    blank reason; a mark taken on another entry date than the one the decision is read at.
  - It re-seeds the store's ledger table from the committed snapshot first (additive), as
    `correct-entry` does.
- **The readers.** A voided decision, its correction and its void leave:
  - scoring (`scoring/harness.py`): no score, so no count, spread, sleeve curve or listing. The
    report names the void ONCE, with its sealed result;
  - the monitor: `decision_rows` (so the book, the spread, `live_verdicts` and the supersede guard
    at `cli.py`) and `apply_corrections`, the first thing `vinci monitor` does, which names the void
    once in the day's notes. Committed monitor days are dated artifacts and stay as they are;
  - `close_position`, which refuses to close a voided decision;
  - `correct_entry`, and `vinci correct-entry`, which refuse to correct one.
  - Input-provisioning reads (`orchestrator.run_monthly`, `vinci score`: which benchmarks to
    ingest, how far back) still see the decision. They only widen what is fetched (GOOGL's SPY) and
    change no value.
- **A fresh decision after a void, or after a close** (the id scheme the #947 record's option 3
  needed).
  - `log_verdict` takes its id from `next_decision_id`: `V-{candidate}` first, then
    `V-{candidate}-{n}`. It refuses while an earlier decision of the candidate is still open.
  - A close, correction or void is named from its DECISION's id (`follow_up_id`): `C-GOOGL-2` for
    the second decision. Every committed row keeps its id (pinned over the corpus).
  - `close_position` by candidate names the one open decision.
  - `log_verdict` changes in its one id line only. The vote-rule session's step-4 PR changes the
    same function, so one rebase is expected.

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
- **The dry run on a `.backup` of the primary's store** (sha256 `07575ae4…` at the copy). It used
  the real `vinci void-decision V-GOOGL` on a scratch tree, appending and exporting there only.
  Live reads were the seven ledger names and benchmarks: Polygon 12, Tiingo 7.

  | Reader | Before | After |
  |---|---|---|
  | Monitor, `--ref 2026-11-06` | GOOGL BUY, followed/quality, 340.65 @ 08-27, −16.35%, excess −11.94 pts | no GOOGL row; one "VOIDED by X-GOOGL" note |
  | Quality-sleeve rows | `['GOOGL']` | `[]` |
  | **Primary screen-origin spread** | **+66.89 pts** (price +66.88) | **+66.89 pts** (price +66.88) |
  | Scoring report (store copy, as of 2026-11-11) | GOOGL pending (the store holds no SPY bars); screen pending 4 | GOOGL gone, the void named once; screen pending 4 |
  | Snapshot | 9 rows | 10 rows: `X-GOOGL` added, the 9 byte-identical |
  | `frontend/build.py` | — | no file changes: the twins skip event rows, so GOOGL's card still reads BUY until V3 |

  - The result to date the void would seal: **−15.36% vs SPY −2.15%, excess −13.21 pts**,
    total return, marked 288.15 on 2026-11-09.
  - The scoring report's `by_sleeve` is empty both ways, because no row has resolved; the quality
    curve's only member was GOOGL. On flat synthetic bars to 2027-03-19, GOOGL resolves into
    `by_sleeve["quality"]` before the void and is in no score or curve after, with the PRIMARY
    spread equal (`test_scoring_leaves_a_voided_decision_out_and_the_primary_spread_does_not_move`).

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The void is permanent.** The ledger refuses an UPDATE or DELETE, and the rule is one void per
  decision. It is appended only after this PR merges and the operator approves the dry run, as an
  artifact-only PR with the store's sha256 before and after.
- **Timing.** The scoring path changes before VRRM is scored on 2026-12-15, and VRRM's
  monthly-scoring rehearsal (STATE row 38, by 2026-12-07) must run on `main` with the void in. The
  plan is: this PR, then the void's artifact PR, then the web twin (V3), all well before
  2026-12-07.
- **The frontend still shows GOOGL's BUY until V3.** `frontend/build.py` and `snapshots.js` skip a
  VOID row (any `event` row), so nothing breaks, but they do not yet apply the void. V3 takes GOOGL
  off the live book and the card, and shows the voided call once in an audit tier.
