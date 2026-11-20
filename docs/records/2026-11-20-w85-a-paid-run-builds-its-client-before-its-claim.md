---
id:
status: shipped
date: 2026-11-20
prs: [1157]
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
- **(ii) A void.** `python -m vinci.evals void-claim --registration R --budget-ledger L --out-dir D`, $0, writes two rows:
  - `{"void": sha, "out_dir", "usd": 0.0}` to the ledger, directly after the claim;
  - `{"event": "void", "registration", "approval", "voids": <the claim's drawn_at>, "voided_at"}` to the checkout's index, to be committed with the run's record.
- **When a void is allowed** (`compare.void_unspent_claim`). It refuses unless all of these hold:
  - the ledger holds exactly one live claim of the registration, into that folder;
  - the claim recorded $0.00 and is the ledger's last row (nothing recorded after it);
  - the folder holds the registration's `registration.json` and no `draws.jsonl`. Every API call writes a draws row, failed calls included (`GuardedSdk`);
  - the index holds exactly one live comparison claim, under the same approval (`registry.record_void`; a build's unit is never voided).
- **When a void is honoured, re-checked as it is read.**
  - `registry._live` (inside `_rows_everywhere`, so `claim_draw`, its twins check and `_drawn_pins` all read it) cancels the one claim a void names. It refuses the whole index when a void names no claim, or when one claim is voided twice.
  - `compare.voided_claims` (`run_compare`'s ledger `prior` check and its design loop) honours a ledger void only while its row directly follows a $0.00 claim of that run and the run's folder still holds no draws. Otherwise it refuses.
  - The two halves are both needed: an index void alone leaves the ledger's claim live.

**WHY.**
- **(i).** A claim is spent the moment it is written. Anything that can fail before the first send must fail before the claim, and building the client is where a missing key fails. The claim's own refusals are unchanged and still come before any send.
- **The cost of (i) in the existing pins.** Ten existing tests assumed the old order: their spy raised when the client was built, as proof the claim had come first. They now use `_SendSpy`, which builds and stops at the first send, and they assert sends instead of builds. Every refusal they expect is unchanged. A refusal AT the claim (design, pins, approval, disagreeing row) now follows an offline client build, and it still comes before any send. The affected tests:
  - `test_evals_order8_round2.py`: 4 tests, 7 cases;
  - `test_evals_order8_gaps.py`: 1;
  - `test_evals_replication_default.py`: 2, whose client counts are now 4 and 6, and the refused single run's queue is shown untouched.
- **(ii).** Voiding is not re-drawing. The fund's rule is that a registration is drawn once, so its result cannot be shopped. A claim that sent nothing has no result to shop. The void is therefore allowed only where the ledger and the folder prove nothing was sent, and it is checked again every time it is read: draws written into the voided folder later refuse the next run.

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

**BOUNDARY.**
- **10 pins:** the new file at this PR's head, failing on `bbbd3d4b`.
- **410 passed, 20 skipped:** every `tests/test_evals*.py` node not marked `network`, at this PR's head, on 2026-11-20.
- **10 moved tests:** the ones that failed at head before their spy changed, counted by case, i.e. by pytest node, parametrized cases included.
- **The corpus check:** one registration (2f2314b0), its one approval's ledger (2 rows) and its one run folder, read on 2026-11-20.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Building every client up front.** A run of the panel builds 12 clients before its claim rather than one at a time. Building a client is offline and free.
- **A void is a reviewed operator action, not an automatic one.** Its index row lands on main in a PR with the run's record. Falsifier: a void honoured for a run with any draw, or any ledger row between its claim and its void. Both are refused when the void is written and when it is read, and both are pinned.
- **Not changed: the judge.** The judge's TEST claim (`claim_judge_test`) still precedes its client. A stop there does not spend it: the approval that holds the read resumes it into its own folder (`judge.run_half`).
- **After this merges.** The void row for 2f2314b0 (with the `drawn` row it voids) is committed with W85's panel record. The operator then re-draws the same registration from a checkout with the key, into a fresh folder. STATE.md's row 53 item for W85 (on #1157) records that outcome.
