---
id: 
status: recorded
date: 2026-07-31
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**SCREEN-PATH ITEMS — RECORDED 2026-07-31, ahead of the build (operator).** Four items that
existed only in conversation across three sessions that ended mid-queue. Durable-write-first.

**~~OPERATOR TO-DO — THE WEEKLY SCREEN CAN TURN THE FLEET RED WITH `[skip ci]`, AND NOTHING GATES
IT~~ — RULED AND CLOSED 2026-08-14 (PR #456). The ruling is at the foot of this entry; everything
between is the diagnosis as written on 2026-08-10 and is left unedited.**
(2026-08-10.) Recorded per the OPERATOR-ACTION RULE: this was raised in chat during #393/#394 and
chat is not a ledger.

**WHAT HAPPENED.** The scheduled weekly screen pushed `607e7d1 weekly screen: refresh snapshots
[skip ci]` to main at 08:06Z. The new screen snapshot moved **NCNO** out of the candidate band and
onto the MAINTENANCE route — and a maintained name needs COMMITTED price bars, because
`data/vinci.db` is git-ignored and CI has no store. NCNO had none, so five maintenance-path pins
failed **on every open PR regardless of its contents**: #393 is docs-only and went red identically
to #394, both having passed forty minutes earlier.

**THE `[skip ci]` IS THE HOLE, not the snapshot.** The one commit that changes the fleet's ROUTING
is the one commit nothing gates, so the breakage lands on main invisibly and first surfaces on the
next unrelated PR — where it reads as that PR's regression. Main's own last gate ran BEFORE it and
stayed green, which is what makes the misattribution so easy. **Diagnosis rule that worked: a
failure that hits a docs-only PR identically is not the PR's.**

**UNBLOCKED, NOT FIXED.** #393 carries `tests/fixtures/prices/NCNO.jsonl` — the remedy the failing
pin itself prescribes (`scripts/build_price_fixture.py`, whose docstring says to re-run it "in the
SAME PR that makes a new name maintained"). No HUMAN PR made NCNO maintained, so the obligation
fell to the next PR that happened to touch the fleet. **That is the defect: an automated commit
incurs an obligation only a human PR can discharge.**

**THE DECISION IS THE OPERATOR'S, because it is about the workflow and not about a test.** Options,
not a recommendation to act on unasked: (a) drop `[skip ci]` from the screen commit so main gates
itself and goes red at the CAUSE; (b) have the workflow run the fixture builder when its snapshot
changes the maintained set — it needs a populated EOD store, which the workflow has; (c) leave it
and accept that the next PR after a routing change pays the toll, now that the shape is written
down. **Nothing was changed in the workflow by the build that found this.**

**RULING (operator, 2026-08-14): (a), PLUS THE PREVENTION (a) ALONE DOES NOT BUY. (b) IS NOT
TAKEN.** PR #456.

**OPTION (a) WAS NEVER AVAILABLE — the 2026-08-10 options list above rests on a false premise, and
this is recorded rather than quietly dropped** (review finding on #456, 2026-08-14). "Drop
`[skip ci]` so main gates itself" cannot work: **a push authenticated with the workflow's own
`GITHUB_TOKEN` does not create a new workflow run** — GitHub's anti-recursion rule, `workflow_dispatch`
and `repository_dispatch` excepted — so `gate.yml`'s `on: push` never fires for a commit these jobs
make, whatever its message says. Main was never going to carry an attestation for the scheduled
commit, with or without the marker. **The marker was a decoy: it named a gate that was not being
skipped because it was never going to run.** The only real remedies were therefore (b), (c), or
gating BEFORE the push — which was not on the list.

**WHAT SHIPPED — THE GATE MOVED TO THE ONLY PLACE IT CAN RUN.** Each scheduled job now runs
`gate.yml`'s three checks — ruff, `mypy --strict`, `pytest -m "not network"` — on its freshly-built
artifacts **BEFORE the push**, so an artifact that breaks a pin fails ITS OWN job and never reaches
main. This is the **ARTIFACT-PASS RULE**, which has bound every human artifact pass since it was
written and did not bind the two passes no human runs. Three conditions make it real rather than
nominal:
- **the store is moved aside** (`data/vinci.db` → `$RUNNER_TEMP`) — a populated DB is precisely what
  let the maintenance-path pins pass on every laptop while main ran red for eleven consecutive merges;
- **`fetch-depth: 0`** — at the default depth 1 the pins that read historical blobs
  (`test_state_identifiers` reads `c112f25:STATE.md`; the new lint reads `607e7d1`'s workflow)
  SKIP, so the only gate these commits get would have been quietly WEAKER than the one every PR
  gets. Shipped in the same PR, off the same review;
- **`frontend/` is rebuilt and staged** — since #417 a stale mirror is itself a gate failure, and a
  scheduled commit that moved the data and not the mirror would have reproduced the same
  misattribution through a different door.

`[skip ci]` is still removed, now for the honest reason: it suppresses nothing today, it WOULD
suppress the gate the day this push moves to an App/PAT token, and a marker claiming a gate is
being skipped when none would have run is a lie in the record.

**THE CONSEQUENCE IS DELIBERATE AND IS A TRADE, NOT A FREE WIN. A broken artifact now FREEZES THE
QUEUE INSTEAD OF REDDENING MAIN.** The weekly job goes red, nothing is pushed, the served queue
stops advancing, and no PR is blocked. That is the better failure — it is loud, it is attributed to
the run that caused it, and main stays green for everyone else — but it needs an operator to look
at the Actions tab, which nothing forces. **OPERATOR TO-DO (standing): a red weekly-screen run means
the queue did not advance that week.** No notification ships with this entry.

**(b) WAS CONSIDERED AND REFUSED, with a reason that is not "scope".** Having the workflow run
`build_price_fixture.py` would discharge the obligation automatically — but the builder filters
bars to `_WINDOW_START` and fails only on an EMPTY result, so a run whose store happened to be
shallower would SILENTLY REWRITE every committed fixture shorter and the 52-week pins would start
meaning less than they say. Auto-generating the input a pin reads is also the shape where a guard
stops being able to fail. **UNLOCK TRIGGER: if queue freezes from a missing fixture happen more
than once, revisit (b) — scoped to names with NO fixture yet, never a fleet-wide rebuild.**

**INVARIANT SHIPPED (INVARIANT RULE) — `tests/test_scheduled_workflows.py`, 7 pins.** A text lint
over every workflow containing `git push`, asserting THREE properties: no skip-CI marker on a
non-comment line; a `python -m pytest` step at a LOWER line number than the push; and
`fetch-depth: 0` on the checkout. **Its negative pin is the real failure, not a mutation of its own
marker list** — it reads `607e7d1:.github/workflows/weekly-screen.yml` out of git and asserts all
three violations are reported. That pin CHECKS shallowness (`git rev-parse
--is-shallow-repository`) rather than inferring it from its own failure: as first written it
skipped on any `git show` error, which is a pin reporting green wherever it cannot read its
evidence — the defect class of this entry, one layer up. On a full clone an unreadable blob now
RAISES. Verified by mutating the LIVE files on disk — the incident file, the marker alone, the gate
step deleted, `fetch-depth` deleted from each file, and the monthly file — each producing exactly
one failure, on the live-corpus pin.

**MONTHLY-SCORE.YML GOT THE SAME TREATMENT, and this was not separately asked for.** The guard is
written class-wide over workflows that push, which is the only form that closes the class; scoping
it to the weekly file would have shipped a guard with an exemption, the exact shape that let this
live. `monthly-score.yml` had the identical defects and commits `scoring_report.md` — the surface
the BUY−AVOID spread is read from. Fixing it is entailed by the invariant, not adjacent cleanup,
but it is a second file and is recorded here as such.

**WHAT THIS ENTRY IS ALSO A RECORD OF: the first ruling shipped a claim that was false, and the
review caught it.** The PR as first pushed said main would carry its own attestation once
`[skip ci]` was gone — it will not, for the `GITHUB_TOKEN` reason above — and it checked out at
depth 1, so its own pre-push gate would have skipped the pin it had just shipped. Both were found
by review, not by the green suite: **the gate was green in exactly the condition where it was
weakest**, which is the same sentence as the incident this entry closes.
