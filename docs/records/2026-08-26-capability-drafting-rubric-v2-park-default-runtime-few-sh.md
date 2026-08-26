---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
migrated-from: STATE.md §2 Built and verified
---

# **DRAFTING RUBRIC v2 — park-default + runtime few-shot precedent (2026-07-15, fix/draft-rubric;

*The one-line summary stays in STATE.md §2; this is the detail that stood beneath it,
verbatim.*

  - **FACE-VALIDITY CHECK (one-shot, 11 LLM calls under v2, self-excluded few-shot) — VERBATIM
    RESULT: exact agreement 5/11, park-or-reject 7/11** (v1 was 0/11 park-or-reject). The two cases
    the operator named both dispositioned AWAY from keep-for-checks: **T011 (+206%) → park** ("+206% vs
    market, +242% mom — cyclical proxy, already moved"); **T034 (collapsed shells) → park**.
    **keep-for-checks survived on 4 lagging clusters the human PARKED — T006, T007, T040, T043** (all
    −24% to −73% vs market; the model found a plausible nameable driver, the human judged them
    already-moved / not-a-theme). T034 also disagreed park-vs-reject. **Below the ~9–11/11 expectation
    → NOT iterating the prompt here; a second iteration needs operator sanction.**
  - **CAVEAT (accuracy-first):** this is a SINGLE-SCAN, FROTHY-TAPE test set (nearly everything had
    "already moved") and the few-shot precedent for these 11 is dominated by the other 10 fresh
    park/reject calls — so it is a sanity read, NOT independent validation. **Confirm the park-default
    holds on a calmer sweep before trusting it.** The 4 keep-for-checks survivors are the concrete
    gap for the sanctioned next iteration. Set by FACE-VALIDITY, never forward-return tuning.
  - **Live inbox drafts NOT regenerated for display** (inbox is empty; next real use is the Aug 13
    scan). The committed `drafts.json` holds the v2 face-validity re-check of the (reviewed) Jul-14
    clusters, tagged `prompt_version: 2`; among data files ONLY `drafts.json` changed
    (reviews/inbox/log byte-identical). ruff + `mypy --strict` + pytest (643) + `node --check` green.
