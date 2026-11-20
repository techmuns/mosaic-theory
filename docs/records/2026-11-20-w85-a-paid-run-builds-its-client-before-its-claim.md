---
id:
status: shipped
date: 2026-11-20
prs: [1167]
supersedes:
superseded-by:
---

# A paid run builds its client, its key read, before it claims its draw, and a claim that drew nothing can be voided: W85's panel registration 2f2314b0 was claimed and stopped with no key, and is drawn again once its void is committed ($0, harness + record)

**WHAT.**
- **The incident.** W85's panel check, registration `2f2314b07ebf7402`, approval "Yes, as recommended (2026-11-20): measure W85 no-worsening on the panel, cap $35". The operator ran `run-compare --paid` from a scratch checkout of `origin/main` with no `.env`. Main's order was:
  1. the $0 refusals passed;
  2. `registry.claim_draw` wrote a `drawn` row to that checkout's index (`drawn_at` `2026-11-20T12:55:17Z`);
  3. `run_compare` wrote the ledger's claim row `{"out_dir", "registration", "usd": 0.0}`, `registration.json` and `requests.jsonl`;
  4. only then did `run_request` build the client, which raised: `Required environment variable 'ANTHROPIC_API_KEY' is not set`.
- **What it left.** Nothing was spent and no call was made: no `draws.jsonl`, and the ledger's last row is the claim. But a registration is drawn once, so it could never be drawn again: the index refuses it ("already drawn"), and so does the ledger ("already drawn under this approval").
- **The ruling.** Coordinator B proposed the fix, and the operator approved it: "Yes, void it and fix". The operator also approved editing `vinci/evals` for it in W85's session: "Yes, approve it".
- **(i) The client before the claim.**
  - `replay.paid_client` builds the client for one request and turns a failure to build it into a refusal: "nothing is claimed or drawn".
  - `run_compare` builds every request's client before it calls the claim, and hands each to `run_request` (new `client=` argument).
  - `builds.run_build` does the same for its one request.
- **(ii) A void.** `python -m vinci.evals void-claim --registration R --budget-ledger L --out-dir D --ruling "<the operator's words>"`, $0, writes two rows under the ledger's lock (`compare.void_claim`):
  - `{"void": sha, "out_dir", "folder", "usd": 0.0, "ruling", "voided_at"}` to the ledger, directly after the claim. `out_dir` is the claim's own spelling; `folder` is that folder resolved;
  - `{"event": "void", "registration", "approval", "voids", "claimed_at", "ruling", "voided_at"}` to the checkout's index. `voids` is the sha256 of the claim's own row, and `claimed_at` is its `drawn_at`. The row is merged to main with the run's record, and it is honoured only once it is there.
- **When a void is allowed.** It refuses unless all of these hold:
  - no other run under the approval holds the ledger's lock (`builds._claim`, non-blocking). `run_compare` holds it for the whole of a run;
  - the ledger holds exactly one live claim of the registration, into that folder;
  - the claim recorded $0.00 and is the ledger's last row (nothing recorded after it);
  - the folder holds the registration's `registration.json` and no `draws.jsonl` (`compare.void_unspent_claim`). A call that fails, or is answered with its usage, writes its draws row (`GuardedSdk`). The two shapes that write none are under WHAT IS ACCEPTED;
  - the index holds the registration as one comparison (its own `registered` row's `kind`), with exactly one live claim, under the same approval, not yet voided in this checkout or on main; and the operator's words are given (`registry.record_void`). A build's unit is never voided.
- **When a void is honoured, re-checked as it is read.**
  - `registry._live` (inside `_rows_everywhere`, so `claim_draw`, its twins check and `_drawn_pins` all read it) honours a void ONLY WHEN ITS ROW IS ON MAIN. It cancels the one claim the void names by that claim's row. It refuses the whole index when a void on main names no claim, or when one claim is voided twice.
  - `compare.voided_claims` (`run_compare`'s ledger `prior` check and its design loop) honours a ledger void only while all of these hold. Otherwise it refuses:
    - its row directly follows a $0.00 claim of that run;
    - the folder the void recorded, resolved, still holds that registration;
    - that folder holds no draws.
  - The two halves are both needed: an index void alone leaves the ledger's claim live, and a ledger void alone leaves the index's claim live until the index void is on main.
- **A folder is drawn into once.** `run_compare` refuses a folder that already holds a run's `registration.json`, a voided claim's folder included.

**WHY.**
- **(i).** A claim is spent the moment it is written. Anything that can fail before the first send must fail before the claim, and building the client is where a missing key fails. The claim's own refusals are unchanged and still come before any send.
- **The cost of (i) in the existing pins.** Ten existing tests assumed the old order: their spy raised when the client was built, as proof the claim had come first. They now use `_SendSpy`, which builds and stops at the first send, and they assert sends instead of builds. Every refusal they expect is unchanged. A refusal AT the claim (design, pins, approval, disagreeing row) now follows an offline client build, and it still comes before any send. The affected tests:
  - `test_evals_order8_round2.py`: 4 tests, 7 cases;
  - `test_evals_order8_gaps.py`: 1;
  - `test_evals_replication_default.py`: 2, whose client counts are now 4 and 6, and the refused single run's queue is shown untouched.
- **(ii).** Voiding is not re-drawing. The fund's rule is that a registration is drawn once, so its result cannot be shopped. A claim that sent nothing has no result to shop. The void is therefore allowed only where the ledger and the folder prove nothing was sent, and it is checked again every time it is read: draws written into the voided folder later refuse the next run.
- **Round 2: coordinator A's independent review of #1167** (B's usage ran out, and the operator handed the PR on: "Yes, take it over"). A's probes, run on `3fbd246b`, showed:
  - **The blocker, item 1.** `_live` read this checkout's index and main's alike. Probe P3: a void row written by hand into the working copy, plus a fresh ledger file holding only the approval's first line, re-opened a registration that DREW (its `drawn` row committed on main, a priced call recorded), and the re-draw reached the send. Probe P6: `void-claim` run while the run's first call was in flight was accepted; the call then completed; approval 1's ledger refused, but a twin of the same design under approval 2 reached the send.
    - **Fix (a):** an index void is honoured only once its row is on main, as RG-D14 does for a registration. The module's claim, that a second draw is refused "whether the earlier row is in this checkout or on main", holds again.
    - **Fix (b):** `run_compare` holds the ledger's existing non-blocking lock (`builds._claim`) for the whole run, and `void-claim` takes it. A void is never written while a call under its claim is in flight. This closes round 0's accepted "not locked" limit, which is removed below.
  - **Item 2.** The folder check read only `draws.jsonl`. After a void, re-running the failed command into the SAME folder passed (probe P1), and its draws then refused every later read of the approval's ledger. A folder holding a run's `registration.json` is now refused.
  - **Item 7.** A void named its claim by `drawn_at`, to the second, and the index merges byte-identical rows. A re-claim in the voided claim's second was the same row, so the void erased it, and a third claim was accepted (probe P7). Every claim now carries a random `claim_id`, and a void names its claim by the sha256 of the claim's row. The 2f2314b0 claim, written before `claim_id` existed, is named the same way.
  - **Item 8.** A void row now records the operator's words (`--ruling`, required) and when.
  - **Item 9.** The read-time check looked for `draws.jsonl` under the claim's own path. A run drawn into a relative folder and read from another directory, or a voided folder moved, passed vacuously. The void now records the folder resolved, and is refused when that folder no longer holds the voided registration.
  - **Item 4.** Six of the void's conditions had no pin: A's mutants M5, M8, M12, M13, M14 and M18 passed all 62 tests. Each is pinned now.
  - **Item 5.** B's "real 2f2314 shape" pins were synthetic. The stopped state is now produced by the real `run_compare`, stopped by a send spy at its first send. The index half is pinned on the real registered row of main's index.

**HOW VERIFIED.**
- **Pins.** `tests/test_evals_void_zero_draw_claim.py`, 10. All fail on `bbbd3d4b` (origin/main, the branch's base): 4 fail and 6 error at setup because `registry.record_void` does not exist there. The two key pins fail with the incident's own error, `RuntimeError: Required environment variable 'ANTHROPIC_API_KEY' is not set`, raised after the claim. What they pin:
  - **(i), end to end through the CLI.** `run-compare` and `run` with no key are refused with nothing claimed: no `drawn` row, no ledger row after the approval, no run folder.
  - **(ii) positive: 2f2314's shape is voidable.** A re-draw is refused before the void. After `void-claim` and the commit of its row, the registration is claimed again into a fresh folder and reaches the send.
  - **(ii) negative: a run that drew is never voided,** with nothing written. Three cases: one failed draw, one priced call, a claim that is not $0.00.
  - **A void is re-checked when read.** Draws written later refuse, and a second void is refused.
  - **One half alone draws nothing:** an index void alone leaves the ledger's claim live.
  - **The index refuses a bad void:** one naming no claim, or a claim voided twice.
  - **A build's claim is never voided.**
- **Suite.** `tests/test_evals*.py`: 410 passed, 20 skipped. `ruff` and `mypy --strict vinci` are clean.
- **Corpus check, read-only on the real files.** A scratch script imported this branch's `vinci` and ran on the actual 2f2314 state, with nothing written:
  - **The folder:** it holds `registration.json` and `requests.jsonl`.
  - **The ledger:** an approval line and a claim; spent $0.0000.
  - **The void's checks:** `void_unspent_claim` accepts the claim and returns the row it would record. With that row, `run_compare`'s `prior` is empty.
  - **The index half,** on a temporary repo holding main's index plus the uncommitted `drawn` row:
    - `claim_draw` refuses, "already drawn (at 2026-11-20T12:55:17Z)";
    - `record_void` writes `voids: 2026-11-20T12:55:17Z`;
    - `claim_draw` then accepts.
  - **The real files:** ledger, `registration.json` and the index are unchanged by sha256.

- **Round 2 (A's review), how verified.**
  - **A's probes P1–P7, run on `3fbd246b`, reproduce every finding.** P1: a re-draw into the voided folder reaches the send. P2: a void not yet on main is honoured. P3: a DRAWN registration is re-drawn under a copied ledger and a working-copy void. P4: a refused key strands its claim. P5: a response with no usage writes no row and is voidable. P6: a void while a call is in flight, then a twin under approval 2, reaches the send. P7: a third claim is accepted in the voided claim's second.
  - **Item 9's own probe, run on `3fbd246b`:** a run drawn into a relative folder and read from another directory reaches the send, both when draws are written into it later and when it is moved.
  - **Pins.** `tests/test_evals_void_zero_draw_claim.py` now holds 26: B's 10, reworked, and 16 new. At `3fbd246b`, 23 of the 26 fail. Most fail on the new `--ruling` flag or `record_void`'s new signature, so the behavioural fail-first is the probes above. The 3 that pass at both are the two key pins of (i) and the pinned item-3 limit.
  - **Mutants at head, 27 of 27 killed** across the six harness test files. These are A's 17 adapted to round 2's code, including M5, M8, M12, M13, M14 and M18, which survived at `3fbd246b`, plus 10 for round 2's own conditions:
    - a void honoured from this checkout alone;
    - no lock in `run_compare`, and none in `void_claim`;
    - a voided folder drawn into again;
    - no `claim_id`, and a claim matched by `drawn_at`;
    - a second void accepted;
    - empty words accepted;
    - the folder not re-checked, and the claim's own path read instead.
  - **Suite.** `tests/test_evals*.py`: 426 passed, 20 skipped. `ruff` and `mypy --strict vinci` are clean.

**BOUNDARY.**
- **10 pins:** the new file at this PR's head, failing on `bbbd3d4b`.
- **410 passed, 20 skipped:** every `tests/test_evals*.py` node not marked `network`, at this PR's head, on 2026-11-20.
- **10 moved tests:** the ones that failed at head before their spy changed, counted by case, i.e. by pytest node, parametrized cases included.
- **The corpus check:** one registration (2f2314b0), its one approval's ledger (2 rows) and its one run folder, read on 2026-11-20.
- **Round 2's counts.** All measured on 2026-11-20, on this checkout's round-2 working tree, which was then committed unchanged except for two docstrings and the printed key step (the code review's one fix). The 26 pins passed again after those edits.
  - **26 pins:** the file's pytest nodes, parametrized cases counted, at round 2's head.
  - **23 failing at base:** the same 26 nodes run on `3fbd246b`'s `vinci/`.
  - **27 mutants:** each a one-condition edit of `vinci/evals/{compare,registry,builds}.py`, run against `tests/test_evals_{void_zero_draw_claim,order8,order8_gaps,order8_round1,order8_round2,replication_default}.py`.
  - **426 passed, 20 skipped:** every `tests/test_evals*.py` node not marked `network`.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Building every client up front.** A run of the panel builds 12 clients before its claim rather than one at a time. Building a client is offline and free.
- **A void is a reviewed operator action, not an automatic one.** Its index row is honoured only once a reviewed PR has merged it to main with the run's record. Falsifier: a void honoured for a run with any draw, or any ledger row between its claim and its void. Both are refused when the void is written and when it is read, and both are pinned.
- **One run under an approval at a time** (round 2). `run_compare` now holds the ledger's lock for the whole run, as `run` held it for its check and claim. A second `run-compare`, `run` or `void-claim` under the same approval while one runs is refused at once, never queued. Before, one approval ran one command at a time by habit; now the lock says so.
- **ACCEPTED: a void sees a RECORDED call, not every call that was MADE** (`/code-review high`, round 0; narrowed in round 2, A's item 6). A call writes its draws row when it fails, or when it is answered with its usage. Two shapes write no row, and the ledger's last row is then still the claim:
  - a run killed after its request left and before the response returned;
  - a response that carries no usage: `GuardedSdk` raises `BudgetStop` before it writes any row (A's probe P5).

  In both, the run is voidable although that request may have been billed. The records cannot tell these apart from a run that sent nothing; a pre-send row per draw would, and is not built here.
  - **What keeps it narrow.** The void is an operator action on a run the operator saw stop. 2f2314b0 stopped at client construction, before any send could exist.
  - **Falsifier:** an Anthropic usage line for the approval's key at a time with no draws row.
- **ACCEPTED: (i) refuses an ABSENT key, not a REFUSED one** (round 2, A's item 3; pinned by `test_a_key_the_api_refuses_is_claimed_and_its_run_is_never_voided`). Building a client reads the key but sends nothing. A key that is present but refused is claimed like a good one, and every draw is sent and refused. The key may be revoked (401), or its account out of credit (400). Each draw writes its failed draws row and $0 is spent. The run then holds draws, so it is never voided, and the registration is spent as W85's was.
  - **Why no check before the claim.** It would have to be free, and none is shown to answer for an account's credit. The free endpoints (`models`, `count_tokens`) authenticate a key; whether they refuse an account that is out of credit was NOT tested, because no real key is run in this $0 work. A check built on that guess could pass a key the draws then refuse, so none is built.
  - **What covers it instead: the procedure.** The re-draw checks the key FIRST, from the same checkout, with `check_anthropic` in `.github/scripts/validate_keys.py`. That is one call to `claude-opus-4-8`, the model the panel's requests name, capped at one output token on a one-word prompt. At that model's list price ($5 in, $25 out per million tokens) it costs under $0.001, outside the approval's ledger. It fails on a revoked key, on no access to the model and on a 400 such as "credit balance too low". `void-claim` prints the step, and a test pins the print.
  - **Falsifier:** a registration claimed with a key that `check_anthropic` passed, and whose every draw then failed with a 401, 403 or 400 from the API.
- **Not changed: the judge.** The judge's TEST claim (`claim_judge_test`) still precedes its client. A stop there does not spend it: the approval that holds the read resumes it into its own folder (`judge.run_half`).
- **After this merges: the procedure for 2f2314b0.**
  1. **The void, $0.** From the scratch checkout that holds the uncommitted `drawn` row, fetched to main with this PR, run `void-claim --registration <its registration.json> --budget-ledger <its ledger> --out-dir <run1> --ruling '"Yes, void it and fix" (operator, 2026-11-20)'`.
  2. **Merge the two index rows.** The `drawn` row and the `void` row go to main in a docs-only PR with W85's panel record. The re-draw is refused until they are on main.
  3. **Keep run1 where it is.** The ledger's void is re-checked on that folder, at its resolved path, every time the ledger is read.
  4. **Check the key, from the checkout that has it.** Run `check_anthropic` (`.github/scripts/validate_keys.py`), with the checkout's `.env` loaded and never printed. It costs one call of one output token.
  5. **The re-draw, paid, by the operator in a terminal.** Draw the same registration into a fresh folder (`run2`), never `run1`.
  6. **The score, $0.** STATE.md's row 53 item for W85 (on #1157) records the outcome.
