---
id:
status: shipped
prs: [539]
date: 2026-08-31
supersedes:
superseded-by:
---

# Sweep re-seed guard keyed on the ROW, not the file — #125 re-armed by an artifact

**WHAT.** `frontend/build.py::emit_radar_sweep`'s re-seed guard now asks whether the scan-history
manifest carries a **component-a row** (`_manifest_has_component_a`), not whether the manifest
FILE exists. An unreadable manifest counts as absent for the same reason.

**WHY — CAUGHT AT REVIEW OF THE ARTIFACT PR (#538), BEFORE IT MERGED.** The guard's premise was
"no manifest in this worktree ⇒ keep the committed sweep.json", which held only while
`data/scan_history/manifest.jsonl` was git-ignored. #538 makes it a COMMITTED artifact whose rows
are THEME scans (`ai-value-migration`, `glp1-drug-value-chain`) — and `_radar_sweep_payload`
filters to `component-a` before taking a timestamp. So the file would exist, the guard would pass,
the payload would find no component-a ts, and the bar would fall back to the seeded default.

Measured on the branch before fixing:

| | last_run | source | next_due |
|---|---|---|---|
| committed `frontend/radar/sweep.json` today | 2026-07-14 | manifest | 2026-08-13 |
| what a build with #538's manifest would write | **2026-06-17** | **seeded** | **2026-07-17** |

A real sweep date replaced by the June-17 seed, with `next_due` then reading six weeks in the
PAST — on every Cloudflare deploy, since each one runs `frontend/build.py`. That is precisely the
#125 incident whose fix this guard IS; the artifact re-armed it by a different route, because the
guard tested the container instead of the contents.

**HOW VERIFIED.**
- `tests/test_build_themes.py::test_a_theme_only_manifest_preserves_the_committed_sweep_date` —
  end-to-end at the layer that failed: a real committed sweep.json plus a manifest written by the
  REAL `record_snapshot` carrying only the two theme-scan rows from #538; `emit_radar_sweep` must
  leave the committed file byte-identical.
- `…::test_an_unreadable_manifest_counts_as_absent_not_as_source` — a corrupt manifest preserves
  the date too; re-seeding because a file failed to parse would be the same incident by another
  route.
- The existing seam tests still pass unchanged (a component-a manifest still regenerates, a later
  other-driver row still does not masquerade as the sweep's last run).
- ruff clean; full offline suite green.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- A worktree whose manifest holds ONLY theme rows now never refreshes the sweep bar — correct:
  there is nothing for that bar to read, and the committed date is the best available truth.
- The bar still refreshes normally the moment a component-a sweep runs, which is the only event
  that legitimately moves it.
- The `n_records`/`git_sha` provenance weaknesses noted on #538 are NOT addressed here; they live
  in `scan_history`'s writer and belong in their own change.
