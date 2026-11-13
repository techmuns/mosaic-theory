---
id: 2026-11-13-ledger-safeguards
status: shipped
date: 2026-11-13
prs: [1052]
supersedes:
superseded-by:
---

# The ledger gets five safeguards, every one additive: the underwrite seal, a named origin and book on every new row, three pre-registered void reasons, one observation per name (SMPL's second BUY is a reaffirmation, the screen book's pending count 4 → 3), and a reading floor of 20 resolved per book; VRRM's scoring path is byte-identical

**WHAT.** Item 5 of #1004 (operator, 2026-11-13: *"yes need to do this reliably"*; the designs are
B's issuecomment-6847522000 with A's additions in -6847633111 and B's reply in -6848173835). New
fields are optional and written only when set; no committed row is rewritten.

1. **The underwrite seal.** `log-verdict` reads the live `scenarios/<T>.json`
   (`vinci/ledger/underwrite.py`) and seals `underwrite_ref` (the path), `underwrite_commit` (HEAD
   when read), `underwrite_sha256` (of the bytes, which must equal HEAD's blob — an edited or
   uncommitted record is refused) and `ratio_at_entry`, re-run by the record's own recipe at the
   entry price `log_verdict` freezes. A ratio undefined at that price seals None with the recipe's
   reason (`ratio_at_entry_undefined`). A decision with no live record is refused unless
   `--no-underwrite-reason` states why (sealed as `no_underwrite_reason`); a reason beside a live
   record is refused. **A record with no horizon loads** — read, hashed, its recipe re-run — and is
   refused only at the decision (B's reply: refusing at load would repeat #762). The record's
   stated limit is now read with the record, once; `cli._committed_limit` is gone and its
   corrupt-record pin moved to the reader.
2. **Origin and book on every new row.** `origin_ref` names the screen run (the candidate id, the
   run's `screen_run_at`, the screens fired) or the follow-list entry (its ticker and
   `followed_since`, read by the dated reader `vinci.followed`). A screen row's book is stamped
   (`overshoot`), so the book's vocabulary now applies to it: a screen PASS is refused, where an
   untagged row skipped the check. **No theme ID:** no route logs a theme-originated decision today
   (`vinci.themes` retired 2026-11-04; the `theme` book is not ledger-active), so the kind is added
   with the route that would write one.
3. **Pre-registered void reasons** (`VOID_REASONS`): `data_error_at_entry`, `wrong_instrument`,
   `wrong_identity`. `void-decision --void-reason` is required; the writer asks it before anything
   else and the schema refuses an unlisted code. A change of mind is a CLOSE, and a close stays
   scored. X-GOOGL (2026-11-11) predates the list, carries no code and stays as written. Voided
   rows' results now print on their own line beside the curve (`**Voided**`), no longer among the
   pending notes; X-GOOGL's is there.
4. **One observation per name** (`reaffirmations`). A decision on the same security, book and
   route, making the same call, entered before the earlier call's horizon date, is a
   **reaffirmation** — in no count, spread or curve, and named once. A close does not end the
   window (the 2026-08-12 ruling); a void does, from its ruling date. The one live case is SMPL:
   `V-SMPL-screen2-20260706` (BUY 2026-07-21, entry 2026-07-20, closed 07-24 and still scored to
   2027-01-16) and `V-SMPL-screen2-20260729` (BUY 2026-08-05, entry 2026-08-04). A later decision
   with the opposite call inside the window is a reversal, not covered: no row is in that state.
5. **The reading floor** (`READING_FLOOR = 20`): a book's curve in the per-sleeve section, and
   each per-sector cut, prints only once it holds 20 resolved observations; below it the count
   prints and nothing else. The primary line is never withheld and prints its count beside it
   ("3 of 20 resolved").
   **Why 20, recorded at coin time:** with a handful of names one outcome moves a mean by tens of
   points; at 20 each name carries a twentieth of an equal-weight mean, the face-validity point at
   which no single outcome is the reading. Set by face validity with no resolved outcome in
   existence. A display rule: `ScoreReport` and its JSON keep every number, and **the primary line
   is never withheld** — A's note: "the primary metric is unchanged"; the coordinator, asked
   before build: "it never withholds the primary BUY−AVOID line".

**WHY.** B's read-only diagnosis (at `dad8f441`, re-derived at `12764514`): no ledger row linked to
its underwrite — `underwrite_ref` and `ratio_at_entry` existed and no code wrote them; a followed
name's candidate id was its bare ticker; any reason could void a decision; SMPL sat in the spread
twice; and a curve on three names would read as a result.

**HOW VERIFIED.**
- **Fail-first pins**, `tests/test_ledger_safeguards.py` (31 nodes), at the seats (`log_verdict`,
  `void_decision`, `_cmd_void_decision`, `score_ledger` → `to_markdown`), on the real committed
  records (SMPL, IT) and the real committed ledger, each refusal with its negative pin.
- **Mutation: 22 of 22 killed** (each a one-line mutant of production, run against the new file
  in a copy of the tree). The first 17: the no-record refusal, the ratio struck at the entry, the
  horizon refusal, the blob check, the screen book stamp, the followed-origin refusal, the void code
  (writer, command, schema), the window's end, the call in the key, the reaffirmation skip, the
  per-sleeve floor, the void line, the omit-while-unset list, voids ending the window, and a reason
  beside a record; one survived (the writer's void-code check, backstopped by the schema) until a
  pin that the code is asked before the decision is looked up. Five after review round 0: the
  per-sector floor, the primary's count, the repository-root resolution, a passed origin on a
  screen candidate, and the no-reason fallback; one survived (the fallback: no committed record
  reaches it) until a pin on the recipe's own `Result` with both fields cleared.
- **The scoring report, before and after, on the committed 10-row ledger.** Base `origin/main`
  `0d8a2a43` against head, the same inputs, `score_ledger` with no dividends and no splits (both
  sides identical), three cuts:

  | cut | screen book pending, base → head | resolved BUY / AVOID | spread |
  |---|---|---|---|
  | real store, bars to 2026-11-10, `as_of` 2026-11-13 | 4 → 3 | 0 / 0 both | n/a both |
  | committed ledger on flat bars, `as_of` 2026-12-16 | 3 → 2 | 0 / 1 both | n/a both |
  | committed ledger on flat bars, `as_of` 2027-01-20 | 1 → 0 | 2 / 1 both | +1.88% both |

  On every cut **VRRM's per-row score is byte-identical** (`json.dumps` of the dataclass,
  sorted keys), and so are IT's and SMPL-0706's; the only row gone is `V-SMPL-screen2-20260729`.
  The report fields that differ are exactly `n_pending`, `row_notes` (the void and SMPL's pending
  note leave them), `void_notes`, `reaffirmation_notes` and `reading_floor`. At 2027-01-20 SMPL's
  second BUY was still pending at base (its 549-day horizon runs to 2028-02-04): from then on it
  would have entered the spread as a third BUY.
- **The spread's N, before and after:** the screen book's observations are 4 (IT, SMPL-0706,
  SMPL-0729, VRRM) at base and 3 at head; BUY leg 3 → 2, AVOID leg 1 → 1.

**BOUNDARY.** "31 nodes": `tests/test_ledger_safeguards.py` at this PR's head. "22 of 22": the
mutants listed above, each run against that file alone, in a copy of the tree at this PR's head.
"10-row ledger": `data/snapshots/decision_ledger.jsonl` at `0d8a2a43` (5 decisions, 2 closes, 2
corrections, 1 void). Pending counts: SCREEN-ORIGIN decision rows not voided (and, at head, not
reaffirmations) whose horizon session has not resolved at the stated `as_of`. The real store: an
impact store built 2026-11-12 from the primary's HTTP cache, bars to 2026-11-10 for every
committed page's ticker and IWM, MDY, SPY (sha256 `24f0f88c2bf7c6a8…`), read-only on a copy. The
flat-bar store: `tests/test_per_row_benchmark._committed_ledger_store`, every name flat at the
price it is read at, IWM/MDY/SPY flat at 50, through 2027-03-19 — a structural check, not a
reading. Spread +1.88%: mean BUY return minus mean AVOID return on those flat bars, both refs.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Every new verdict now needs a committed record or a stated reason,** and a record with no
  horizon cannot be logged against: IT and WERN today. B's reply rules that their re-underwrite
  after the rebuild states a horizon with a verdict, or moves the name to watch.
- **The monitor's interim spread** (a diagnostic, never the result) does not apply the
  reaffirmation rule yet: its BUY leg still holds both SMPL rows. Recorded on STATE row 5.
- **The reading floor covers the per-sleeve and per-sector curves, never the primary line**
  (coordinator, 2026-11-13: "Build (b)"; reversible under the delegation record). Below the floor
  the per-sleeve overshoot row prints a count while the primary above it prints a figure with its
  count against the floor — by design, since the primary is exempt.
