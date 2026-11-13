---
status: shipped
date: 2026-11-13
prs: [1045]
supersedes:
superseded-by:
---

# The local-path guard reads the theme desk's committed logs and STATE.md too; the one run log's scratchpad path and STATE row 38's seven machine folders are rewritten, and the records stay as written (operator: "Guard them too (Recommended)")

**WHAT.**
- **The ruling.** The operator, 2026-11-13, verbatim: *"Guard them too (Recommended)"*. The
  option it answered proposed "a small $0 follow-up PR [that] scrubs the run log's paths, rewrites
  row 38's machine names as roles (operator's Mac, B's machine), and extends the guard". This
  follows #1042, which left those two files outside the guard and said so
  (`docs/records/2026-11-12-the-preview-config-leaves-git-and-the-guard-reads-claude-and-bin.md`).
- **The run log.** `docs/theme_intelligence/state-pull-ledger-2026-10-11/run-log.txt` line 16 quoted
  the `--path` of a synthetic input under a Claude session's scratchpad. It now reads
  `--path <scratchpad>/input/synthetic-grid-ledger-note.md`. The file name, flags and everything
  else on the line are unchanged. It is a committed log, not a record.
- **STATE row 38.** Its seven mentions of the two machines' user folders now name roles: "the
  operator's Mac" and "B's machine". Each sentence keeps its claim; only the name changes.
- **The guard.** `tests/test_no_local_paths.py`'s `SCANNED` gains `docs/theme_intelligence` and
  `STATE.md`. `docs/records/` stays outside it.
- **The records stay as written.** At main `f2e31cea`, 27 of the 796 tracked records hold 52 hits.
  They are listed below and not changed.

**WHY.** A record's body is immutable once merged, so a path in one stays and is listed. The run
log and STATE.md are not records. One is a committed artifact, and the other is the snapshot every
build edits, so the next build that writes a machine's folder into STATE.md now fails the guard.

**HOW VERIFIED.** All on branch `claude/leftover-local-paths`, cut from main `f2e31cea`:
- **The pin failed first.**
  `test_the_theme_desk_logs_and_state_are_read_and_the_records_are_not` builds a scratch repo
  holding a STATE.md, a theme-desk run log, a record and another `docs/` file, each carrying a
  path. On base `SCANNED` it failed (`assert set() == {'STATE.md', …/run-log.txt'}`). It passes
  once the two scopes are added.
- **Corpus before synthetic.** The widened matcher over main `f2e31cea`'s blobs for the two new
  scopes found **9 hits in 2 of 597 files**: STATE.md 7, the run log 2. The run log's 2 are the
  one path, matched once as a root and once in its dashed project-folder form. On this tree the
  whole guard reads **0 in 2,037 files**.
- **Mutants, four, all killed:**
  - `STATE.md` dropped from `SCANNED`: the new pin fails;
  - `docs/theme_intelligence` dropped: the new pin fails;
  - `docs/theme_intelligence` widened to all of `docs`: the new pin, the folder pin and the live
    guard fail, because records would then be read;
  - one row-38 folder name restored: the live guard fails.

**BOUNDARY.**
- "9 hits in 2 of 597 files" is the guard's matcher over every tracked blob under
  `docs/theme_intelligence/` plus STATE.md at main `f2e31cea`. "0 in 2,037 files" is the whole
  guard (all eight scopes, tracked plus untracked-not-ignored) on this branch's tree.
- "52 hits in 27 files" is the same matcher over the 796 tracked files under `docs/records/` at
  main `f2e31cea`. The records holding hits, by file and count, left as written:

  | record | hits |
  |---|---|
  | `2026-07-27-stale-checkout-runbook-line-both-channels-hit-it.md` | 1 |
  | `2026-09-10-googl-axis-methods-ratified.md` | 1 |
  | `2026-09-10-orka-onboarding-blocked-on-ciq.md` | 1 |
  | `2026-10-14-theme-intelligence-exposure-and-thesis-page.md` | 1 |
  | `2026-10-14-theme-intelligence-ms-batch-citi-links.md` | 1 |
  | `2026-10-17-artifact-pass-desk-for-experts.md` | 3 |
  | `2026-10-26-latest-quarter-alias-at-quarterly-grain.md` | 1 |
  | `2026-10-26-peer-descriptor-cut-and-live-pins.md` | 1 |
  | `2026-10-26-review-gate-counts-only-opened-prs.md` | 1 |
  | `2026-10-27-a-retagged-annual-leg-is-read-from-its-new-tag.md` | 1 |
  | `2026-10-27-annual-readers-withhold-a-stale-annual.md` | 1 |
  | `2026-10-27-codex-rereviews-the-fix.md` | 1 |
  | `2026-10-27-combined-annual-figures-read-one-fiscal-year.md` | 1 |
  | `2026-10-27-the-anchors-dep-amort-reads-the-guarded-line.md` | 1 |
  | `2026-10-30-a-filings-window-reads-every-submissions-page-it-overlaps.md` | 1 |
  | `2026-11-02-inputs-are-cut-at-the-pages-price-date.md` | 2 |
  | `2026-11-05-no-committed-page-carries-a-local-path.md` | 11 |
  | `2026-11-07-fix3a-measured-on-the-panel.md` | 1 |
  | `2026-11-07-fix4a-the-gap-test.md` | 1 |
  | `2026-11-09-fix3b-stale-buyback-legs-and-one-self-funding-read.md` | 1 |
  | `2026-11-09-m-gap-gold-and-metric.md` | 1 |
  | `2026-11-09-the-layer-cuts-releases-and-ciq-guidance-at-the-price-date.md` | 1 |
  | `2026-11-10-fix2-groupF-f-the-two-corrections-appended.md` | 1 |
  | `2026-11-11-the-vote-rule-implemented.md` | 1 |
  | `2026-11-11-vrrm-run-monthly-rehearsed-on-a-copy.md` | 10 |
  | `2026-11-12-fix2-s3-row42a-the-theme-desks-filings-walk-names-the-page-it-could-not-read.md` | 1 |
  | `2026-11-12-operator-delegation-and-defaults.md` | 4 |

- This record adds none.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **Git history still holds the old run log and every earlier STATE.md**, as it holds the
  price-store paths. No history rewrite is proposed.
- **The 52 hits in records stay in the current tree** by the same rule that keeps a record's body
  immutable.
- **A build that writes a machine's folder into STATE.md now fails the gate.** That is the point.
  Its fix is to name the machine by role.
