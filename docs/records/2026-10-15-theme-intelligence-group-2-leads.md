---
id: 2026-10-15-theme-intelligence-group-2-leads
status: recorded
date: 2026-10-15
prs: []
supersedes:
superseded-by:
---

# Theme intelligence — group 2 of the verified review leads (money): U23a, U23b, U23c

**WHAT.** Operator, 2026-10-15: "fix group 1 as one PR and the move to group 2". Group 2 is the
money leads not yet fixed, from `docs/records/2026-10-14-theme-intelligence-unverified-leads-verified.md`:
- U3, U4 and U26 are in PR #715 (`docs/records/2026-10-15-theme-intelligence-u3-u4-u26-u29.md`).
- U23d was fixed with company matching (#711).
- That leaves U23a–c. This branch is stacked on #715, because both edit the spend guard and the
  extraction.

| Lead | Defect | Fix |
|---|---|---|
| U23a | `reask-part --max-cost 1.00` refused a $0.90 call ("limit $0.85"). The one re-asked part is a completeness call, so the guard held it to a retry's 85% share of the limit the operator set for that one call. | `SpendGuard.begin_document(retry_share=)`: a document's retry share is its own. `reask-part` passes the whole limit (1.0); every other document keeps 85%. |
| U23b | `enrich --refresh` "asks again" (the flag's help, the run's note, the docs), and made no model call. | The behaviour stands: it is the repo's rule for paid answers ("paid once, never asked again — set that file aside to have the model asked anew"), and a test pins it. What changes is the wording. The flag, the note and the docs now say what it does: the pass runs again, the paid answer comes from the cache, and every name is checked against the SEC again as of `--as-of`. |
| U23c | A truncation marker written at a 16,384-token cap still forced COMPACT after the cap was raised to 64,000. Neither the marker nor the cache key looked at the cap. | `extract.marker_holds`: a marker holds at the cap it records. A client whose cap is higher asks the full request again, in extraction and completeness alike. A marker or a client that states no cap holds, as before: never a paid re-ask on a guess. An already-cached compact answer is still reused, never bought again. The client states its cap (`AnthropicLlmClient.max_tokens`), and the spend guard passes it through. |

**WHY.** U23a refuses a call the operator paid for in advance. U23b's flag promised a model call
it never makes. U23c makes raising the cap useless for any document that has already truncated.

**HOW VERIFIED.**
- **The verifier's reproductions, against the base (PR #715's head, 8d9ce177):**
  - **U23c:** at the base, the call after a raised cap was COMPACT; on this branch it is the full
    request and the result is not compact.
  - **U23a:** the verifier's script calls the guard directly, below the fix, so it is shown end to
    end instead. A supplied report's completeness call is re-asked with `--max-cost` sized so the
    call takes 90% of it: the base refuses it, this branch sends it.
- **Real data** (under the boundary below):
  - **U23a:** the one real paid re-ask (Gridlock part 4, run R-20261012T073736Z-ingest) was bounded
    at $0.9769 and billed $0.5278. Under the 85% share it needed `--max-cost` of at least $1.15;
    now $0.98 suffices. The two refusals stored are re-asks run deliberately at `--max-cost 0.01`,
    and they stay refused.
  - **U23c:** 4 distinct truncation markers are held, all extraction markers, all written at
    21,333, which is today's cap. They all still hold: no stored document is re-asked, and no cost
    changes.
- **Pins:** `tests/test_theme_intelligence_group2.py`, 12 tests, each fix with its negative.
  - Against the base, 6 fail. The 6 that pass are negatives:
    - a re-ask over its limit;
    - a marker at the same, a lower or an unstated cap, and a client stating none;
    - a completeness marker at the same cap.
  - U23a is pinned end to end through `reask_part`, the call site, not only at the guard.
- **Mutants: 13 of 13 killed.** An unmutated baseline passes.
- Ruff and `mypy --strict vinci` clean; the offline suite result is in the PR.

**BOUNDARY.**
- Code: PR #715's head 8d9ce177 against this branch, 2026-10-15.
- Real data: every `registry.db` and LLM cache under the `theme-intelligence` worktree's
  `data/theme_intelligence/` (backups excluded).
- Re-asks are the ledger rows whose purpose ends `-reask` (3 rows, one paid), with their runs'
  guarded calls.
- Markers are distinct by file name.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- $0; no model or SEC requests.
- **U23b is a wording fix by choice.** The operator can ask for a flag that re-buys an answer;
  none exists, and none is added here.
- **U23c spends once a cap is raised.** Each document whose marker records a lower cap is asked the
  full request again, and that request is bounded by the guard like any other. No stored marker
  qualifies today.
- `vinci/graph/llm.py` (shared with the graph track) gains a read-only `max_tokens` property. No
  behaviour changes there.
