---
id:
status: recorded
date: 2026-09-01
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §2 (capability entry, compacted)
date-source: the migration date — the capability is older and is dated in the body
---

# COMPONENT-A DRAFTING LAYER — operator-sanctioned LLM assist (2026-07-15, feat/themes-draft; PR open, not merged; DEPLOYS on merge).

*The one-line summary stays in STATE.md §2 with a pointer here. This is the detail that stood beneath it, verbatim.*

- **COMPONENT-A DRAFTING LAYER — operator-sanctioned LLM assist (2026-07-15, feat/themes-draft; PR open,
  not merged; DEPLOYS on merge).** The machine now DRAFTS a working name + a HYPOTHESIS + an ADVISORY
  disposition (`keep-for-checks`|`park`|`reject`) for each UNREVIEWED cluster — the human still OWNS the
  decision. `vinci/themes/drafts.py` reuses the graph LLM client (`llm.extract`), the LlmError→unassessed
  pattern, and the #123 abort-fast (3 consecutive same-4xx → `DraftAbortedError`, persists nothing). Two
  new CLIs: **`themes-draft`** (ONE LLM call per unreviewed cluster → `record_snapshot` driver_slug
  `component-a-drafts` + a `frontend/radar/drafts.json` latest-pointer; **idempotent** — reuses drafts
  whose `source` == the current snapshot basename, no double spend) and **`themes-review`** (append the
  analyst's disposition to `reviews.json`; validates the key against the latest snapshot; refuses a dup
  without `--amend`; attributes `by:"analyst"`, or `"analyst (ratified advisor draft)"` ONLY when the
  recorded decision AND reason match the draft — the advisory suggestion never becomes the decision on its
  own). build.py joins `draft_name`/`draft_read`(=terse reason)/`draft_suggested` onto UNREVIEWED inbox
  rows by member overlap (ids are per-run); the fuller hypothesis stays in `drafts.json` (machine-complete).
  The Inbox view shows the draft name + a dashed **DRAFT** chip + a muted *"draft: <suggested> — <read>
  (advisor)"* line on unreviewed rows only; reviewed rows (Log tab) keep the analyst's name, no chip.
  **VERIFIED by the one-time backfill: 11/11 unreviewed clusters drafted, 0 unassessed-error, all framed
  as hypotheses with no citations** (Crypto-Mining & AI Compute, B2B Vertical SaaS, Semi Test & Subfab,
  Copper Miners Beta, Rare Earth Miners, …); the idempotent re-run reused with no LLM spend. Every data
  file except `inbox.json` + the new `drafts.json` byte-identical; the git-ignored `component-a-drafts`
  scan-history snapshot is NOT committed. The standing SCOPE CAP re-applies verbatim after this PR. ruff +
  `mypy --strict vinci`(+tests) + pytest (614) + `node --check` green.
  - **Incident→invariant:** #123 fabricated-on-error → the LlmError→unassessed record + abort-fast are
    pinned by `test_draft_error_becomes_unassessed_never_fabricated`, `_aborts_fast_on_repeated_4xx`, and
    `_invalid_suggested_is_unassessed_not_fabricated` (a bad-enum tool result fails loud, never coerced).
