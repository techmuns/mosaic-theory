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

# Component-A scans now NON-OVERWRITING via scan_history (2026-07-13, `feat/component-a-history`; closes the audit-followup gap at `cli.py` ~521-525).

*The one-line summary stays in STATE.md §2 with a pointer here. This is the detail that stood beneath it, verbatim.*

- **Component-A scans now NON-OVERWRITING via scan_history (2026-07-13, `feat/component-a-history`;
  closes the audit-followup gap at `cli.py` ~521-525).** `_cmd_themes` computes the dump ONCE and writes
  it BOTH to `candidate_themes.jsonl` (the "latest" pointer, same bytes) AND to an always-on timestamped
  `scan_history` snapshot (`driver_slug=component-a`, `tier_field=None`), mirroring the exposure/assay
  pattern — a monthly sweep can no longer clobber the prior harvest (the delta/monitor diffs against
  immutable snapshots). `record_snapshot` gained an ADDITIVE `tier_field: str | None = "exposure_basis"`:
  the default path is byte-identical (exposure/assay manifest lines unchanged, still fail-loud on a
  missing key), and `None` gives Component-A records (no `exposure_basis`) an empty `tier_counts` instead
  of a KeyError — pinned by a Component-A-shape test + an exposure-default regression test. Parity flags
  `--scan-history-dir` / `--no-scan-history` added. **BACKUP NOTE:** the June-17 `candidate_themes.jsonl`
  OUTPUT was absent at first-build time (untracked / never committed; removed when the primary left
  `feat/own-history-line`), then the raw June-17 output was RESTORED 2026-07-13 from the operator's
  off-repo copy (35 clusters, first `T000`) → backup `candidate_themes.2026-06-17.backup.jsonl` MADE. The
  timestamped archive + committable latest-pointer prevent recurrence. **Monthly sweep SANCTIONED; cron
  AUTHORED + verified, PUSH STILL BLOCKED 2026-07-13 — the token at `~/.mosaic_gh_token` reports only
  `repo` scope (NOT `workflow`) despite the re-scope precondition, so the push was rejected again; the
  file is committed-ready locally, awaiting a `workflow`-scoped token in that file (or a keychain
  refresh):**
  `.github/workflows/monthly-themes.yml` (cron `0 7 3 * *` + `workflow_dispatch`), mirroring
  monthly-score.yml — runs `python -m vinci.cli themes` (documented defaults basis r2 / window 365d /
  min-breadth 3; the exact June-17 flag string was UNRECORDED, SAID SO in the workflow), job-summary
  prints snapshot path + manifest line, commits the `candidate_themes.jsonl` pointer (git history = the CI
  archive; `data/scan_history/` stays git-ignored/local). Evidence: the June-17 harvest = 35 proposals → 2
  advances (entry below). Backend + workflow only — NOTHING deploys. On `feat/component-a-history`; PR to
  be opened, NOT merged.
- _Suite green (ruff + mypy --strict clean; `pytest -m "not network"` = 573 passed; +2 scan_history
  tests). Dry-run: two Component-A sweeps → 2 immutable snapshots, prior untouched, `tier_counts: {}`._
