---
id: 2026-10-21-validate-keys-pings-the-pipeline-model
status: recorded
date: 2026-10-21
prs: [758]
supersedes:
superseded-by:
---

# validate-keys pings the model the pipelines call, and a key that cannot use it fails

**WHAT.**
- `validate-keys` checks the Anthropic key by pinging `claude-opus-4-8`, the model every pipeline
  calls, instead of `claude-haiku-4-5`. Operator, 2026-10-21: "switch the ping to opus 4.8".
- The model is one constant in the script, `PIPELINE_MODEL`.
  - The script cannot import `vinci`, because the workflow installs only `anthropic` and `httpx`.
  - So a test holds it equal to the two configured models: `Config.graph_llm_model` (dossier
    and graph) and `theme_intelligence.config.LLM_MODEL`. Both are `claude-opus-4-8` at main
    4b514dca.
- A 404 for that model (`NotFoundError`) now FAILS the run: the key cannot use the pipelines'
  model. It used to fall into the catch-all, which prints "runner→api.anthropic.com
  connectivity, NOT a key problem" and passes.
- The ping stays one output token.
- **Any other 4xx answer FAILS too**, with the API's own error type and message, the key masked.
  A 400 "credit balance too low" is the account, and the weekly run would hit it. Code review of
  #758, 2026-10-21.
  - A WARN is kept for what is transient or the runner's environment: no connection, a timeout,
    408, 429 and 5xx.
- The stale "default Claude Opus 5" text in `vinci/graph/llm.py`'s docstring and the
  `graph-test0 --model` help is corrected to `claude-opus-4-8`. The 2026-08-29 move to Opus 5 was
  reverted on 2026-09-01 (`docs/records/2026-09-01-opus5-synthesis-regression.md`).
- The key check's tests load the script through one shared helper,
  `tests/validate_keys_support.py`. Before, they imported a private helper from the
  theme-intelligence tests.

**WHY.**
- **The wrong model.** The operator asked why Haiku was used on 2026-10-21. The only Haiku calls
  in the repo were this ping: one per `validate-keys` run, runs 39565632511 and 39572152249 that
  day, on GitHub's runners.
  - A Haiku ping proves the key, not access to the model the pipelines call.
  - A key with Haiku but not Opus access would have passed and then failed the weekly run.
- **The 404 hole.** Switching the model alone would not have closed that gap, because the
  missing-model answer is a 404. The catch-all would have passed it as "connectivity", the same
  blind spot the padded key hid in from 2026-06-26 to 2026-10-20
  (`docs/records/2026-10-20-theme-intelligence-open-leads.md`).

**HOW VERIFIED.**
- **Real API, this machine, 2026-10-21:**
  - the real key on `claude-opus-4-8` gives "PASS — authenticated; claude-opus-4-8 answered";
  - the same function pointed at `claude-opus-4-8-no-such-model` gives the API's real 404
    (`not_found_error`, "model: claude-opus-4-8-no-such-model") and "FAIL — NotFoundError: this
    key cannot use …".
- **Real API, the 4xx rule:** the same check with its request emptied gets the live API's real
  400 and prints "FAIL — HTTP 400 invalid_request_error: messages: at least one message is
  required". The real key still PASSes.
- **Pins** (`tests/test_validate_keys_model.py`, 5):
  - the ping's model equals both configured models, and it is one token;
  - the real 404 shape fails the key without printing it;
  - the real 400 shape fails with the API's reason, and so does a billing message in that shape
    (the message itself not observed), the key masked;
  - NEGATIVES: a connection error, a 429 and a 529 only warn.
- **Mutation:** 11 mutants, all killed.
  - The first 5: Haiku restored, 404 handler removed, 404 passing, a 16-token ping, a connection
    error failing.
  - The 6 for the 4xx rule: 4xx passing, 429 failing, 5xx failing, the key unmasked, the API's
    reason dropped, the handler removed.
- **Actions,** run 39585936189 on this branch (ff04f549): "ANTHROPIC_API_KEY: PASS —
  authenticated; claude-opus-4-8 answered", with Polygon, Tiingo and SEC all PASS.

**BOUNDARY.**
- "Every pipeline": the four workflows that read `ANTHROPIC_API_KEY` (`weekly-screen`,
  `monthly-score`, `theme-intelligence-weekly`, `validate-keys`) and the two model settings their
  code reads, at main 4b514dca.
- The Haiku-call count covers the `validate-keys` runs created on 2026-10-21 UTC.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Cost.** One Opus 4.8 call per run: a 1-token answer to a one-word prompt, about $0.0001 at
  list price, against roughly $0.00002 on Haiku.
- **Accepted.** A 4xx raised by a bad REQUEST from this script, rather than by the key, also
  FAILS. The ping is one fixed message, so such a failure means the API changed, and that is
  worth a red run.
