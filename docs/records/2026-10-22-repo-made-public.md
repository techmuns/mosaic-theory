---
id: 2026-10-22-repo-made-public
status: recorded
date: 2026-10-22
prs: []
supersedes:
superseded-by:
---

# The repo is PUBLIC by operator decision — CI runs again, no secret was ever committed, and the derived set stays committed

**WHAT.** On 2026-10-22 the operator changed `techmuns/mosaic-theory` from private to public and,
after an exposure audit, ruled to KEEP it public: the repo is not promoted anywhere, and neither the
CIQ nor the Polygon agreement requires the exposure to be reported. Three consequences, each checked:

1. **CI runs again.** Since the last green `gate` run (created 2026-10-21 11:45:49Z) every run had
   executed zero steps on a GitHub billing block — 49 failures carrying the annotation "recent account
   payments have failed or your spending limit needs to be increased", plus 17 concurrency cancels.
   GitHub-hosted runners are free for public repos, so the block no longer applies. Run 39762937618
   (the push run for `5969a48`, re-run as attempt 2) finished green at 2026-10-22 13:51:24Z: ruff
   clean, `mypy --strict vinci` clean, `pytest -m "not network"` **6279 passed, 531 skipped, 37
   deselected** in 242.91 s, frontend mirror in sync. That certifies the TIP of `main`; the 19 pushes
   that landed on `main` without CI were not each re-run.
2. **No secret was ever committed.** Every unique blob reachable from any ref was scanned for key
   shapes (Anthropic, OpenAI-style, GitHub, AWS, Slack, Google, private-key blocks, Cloudflare and
   generic `*_API_KEY/SECRET/TOKEN/PASSWORD` assignments): no match. The five real values in the
   local `.env` were searched for verbatim: none appears in any blob. No `.db`, spreadsheet,
   `data/manual/` path or `.env` file was ever added on any ref. The four secret-bearing workflows
   (`monthly-score`, `weekly-screen`, `theme-intelligence-weekly`, `validate-keys`) are
   `workflow_dispatch`-only; `gate.yml` runs on `pull_request` (a fork PR gets no secrets and a
   read-only token); no workflow uses `pull_request_target`; the repo holds no Actions artifacts.
3. **What is now world-readable, by the operator's ruling.** The derived set CLAUDE.md authorized
   for the private repo — 27 `data/dossiers/*/dossier.json` (5,684 occurrences of "ciq", e.g.
   `source_ref` "CIQ Financials→Multiples 'TEV/LTM EBITDA' Close — 38 quarters…") and their 55
   `frontend/dossiers` mirrors, `data/graph_coverage.json`, 103 `frontend/theme-intelligence` files —
   plus `data/calls` and `frontend/calls` (247 files each: one public X account's post text in
   `gold_labels.jsonl`, 3,889 scored call results, per-ticker price bars), the sealed
   `decision_ledger.jsonl`, STATE.md and `docs/`, all PR bodies, CI logs, and the commit author
   addresses. CLAUDE.md's rule "if the repo ever becomes public, the graph + dossiers revert to
   git-ignored" is OVERRIDDEN by the ruling: un-tracking now would not un-publish history.

**WHY.** CLAUDE.md and `docs/DEPLOY.md` still said "this repo is private" and instructed an agent
to un-track the dossiers if it ever went public. A rule that contradicts the operator's ruling is a
rule some session will follow; this record and the two edits make the ruling the rule.

**HOW VERIFIED.** `gh api repos/techmuns/mosaic-theory` → `"visibility":"public"`; the gate run's
step list and totals read from `gh run view 39762937618 --log`; the history scan is a stdlib Python
pass over `git rev-list --all --objects` + `git cat-file --batch` that prints pattern names and
paths only, never a value; counts from `git ls-files` and `grep -c` on the committed tree.

**BOUNDARY.** All counts at `main` = `5969a48` (2026-10-22). The CI window is the 100 most recent
`gate` runs (2026-10-20 11:50Z → 2026-10-22 11:16Z). The secret scan covers 12,127 unique blobs
reachable from every ref of the local clone on 2026-10-22; it cannot see objects only GitHub holds
(e.g. a deleted PR head). "ciq" occurrences are case-insensitive substring matches in the 27
`dossier.json` files at HEAD. GitHub traffic through 2026-10-21 showed 0 forks, 0 stars and 3
unique cloners in 14 days; 2026-10-22 was not yet reported. GitHub's event log also lists a
`PublicEvent` by `techmuns` on 2026-06-18 — the repo was public once before; how long is not visible.

**WHAT IT COSTS / WHAT IS ACCEPTED.** ACCEPTED by the operator: the derived artifacts, the calls
dataset and the fund's own records are public, in history as well as at HEAD. Open: `main` reports
`protected: true`, but the agent account (write, not admin) cannot read which checks the rule
requires — the operator confirms it requires `gate` (STATE.md §5.0 row 32, item 13, which this
record closes: Actions no longer stop on the billing block). Falsifier for
"nothing to report": a licence term the operator has not seen; the operator owns that reading.
