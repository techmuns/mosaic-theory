---
status: recorded
date: 2026-11-12
prs: [1035]
supersedes:
superseded-by:
---

# The operator's three approvals of 2026-11-12, and nine reversible defaults the coordinator adopted the same day under the operator's delegation (defaults, not operator rulings)

**WHAT.** Two kinds of decision were made in chat on 2026-11-12. This record keeps them apart,
because they carry different authority.

1. **OPERATOR RULINGS.** The operator, verbatim: *"Approve all three"*. It answered the
   coordinator's ask, which covered three items:
   - **(a)** a **$35 cap** for the E2 remainder's panel check, 60 draws. Fix 4a's 60 draws cost
     $30.3130 (`docs/records/2026-11-09-fix4a-measured-on-the-panel.md`, "60 calls, none
     failed"). The run comes after order 8 merges.
   - **(b)** VRRM's 2026-12-16 scoring runs on B's machine (`/Users/work`) after a fresh price
     refresh, instead of the operator's Mac (`/Users/mac`). This replaces the 2026-11-11 ruling in
     STATE §5.0 row 38 that named `/Users/mac`'s store. The machine can change because the run
     re-seeds the ledger from the committed snapshot, whose export matched byte for byte in the
     first rehearsal (`docs/records/2026-11-11-vrrm-run-monthly-rehearsed-on-a-copy.md`), so, in
     row 38's words before this change, "only the Polygon call count differs".
   - **(c)** RUNBOOKS §o ("cross-setup validation") joins CLAUDE.md's loop list. This change makes
     that edit.

2. **COORDINATOR'S DEFAULTS UNDER THE OPERATOR'S DELEGATION.** These are **not operator rulings.**
   Earlier the same day the operator said, verbatim: *"what would a team of expert decide or use
   in the situation, search about it first instead of waiting on me"*. Under that delegation the
   coordinator researched each open call and adopted a reversible default:

   | # | STATE §5.0 | the default | who builds it |
   |---|---|---|---|
   | 1 | row 48 | the record's proposed HARD/FLAG table stands, so **nothing is HARD**; a check is promoted to HARD only after a clean record on all 27 pages | the agent, in slice 2 |
   | 2 | row 52 (3) | the material-sign flag **stays a FLAG** and is **shown on the page** | a render PR (preview first) |
   | 3 | row 53 (7) | the **replication rule becomes the default** (today `register --ship-alpha` is opt-in) | S1, after order 8 |
   | 4 | row 53 (2) | **no** production-exact baseline run (it was proposed at a $20 cap) | nothing to build |
   | 5 | row 57 (1) | **no** ORKA run (it was proposed at a $5 cap) | nothing to build |
   | 6 | row 49 | **untrack** `.claude/launch.json`, **clean** `bin/commit`, and the records **stay as written** | S4 |
   | 7 | — | the `anthropic` SDK gets an **exact pin and a lockfile** | S4 |
   | 8 | — | a **standing rule for paid caps**: expected cost from run history plus about 20%, pre-registered, drawn once | every paid run from now on |
   | 9 | row 51 (2) | the non-operating window is **anchored at the filer's latest filed quarter**, with a stale flag, and a shown run on all 27 pages | S3 |

   Each one can be reversed by the operator, and a reversal is a new record, not an edit to this
   one.

**WHY.** The operator delegated these calls so the work would not wait on them. Recording the
defaults as the coordinator's keeps the line CLAUDE.md draws: the operator approves merges and paid
runs, and a default adopted under a delegation is not one of those. Item (a) is a paid run and item
(b) moves a scoring run that writes the ledger, so both went to the operator, not into a default.

**THE SOURCES** the coordinator used for the defaults, as its tracker names them, with the links
the coordinator gave in review:
- dbt's `severity` test config, warn versus error
  (<https://docs.getdbt.com/reference/resource-configs/severity>). Read for defaults 1 and 2: a
  check starts as a warning and is promoted only on a clean record.
- Evan Miller, *Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations*,
  arXiv 2411.00640 (<https://arxiv.org/abs/2411.00640>). Read for defaults 3, 4 and 8: evals as
  experiments with stated error, decided by a pre-registered rule.
- Claude Code's settings documentation (<https://code.claude.com/docs/en/settings>), and its
  convention that `.claude/settings.local.json` is personal and not checked in. Read for default 6:
  a per-machine file stays out of git.
- Mergify, *Stop Lying to Your Dependency Resolver: The Real Rules for Python Dependency
  Management*
  (<https://mergify.com/blog/stop-lying-to-your-dependency-resolver-the-real-rules-for-python-dependency-management>).
  Read for default 7: an application pins its dependencies with `==` and uses a lockfile.
- two reports of git repositories damaged in cloud-synced folders
  (<https://nolongerset.com/version-control-and-cloud-drives/>,
  <https://hackernoon.com/a-side-effect-of-storing-a-git-repository-in-icloud-drive>). They are
  the background to (b), because `/Users/mac` keeps this repo in a folder iCloud offloads.

**HOW VERIFIED.** The quotes are the coordinator's, relayed to S1 on 2026-11-12 and matched to the
coordinator's tracker, which records both quotes verbatim. Nothing in this change runs code. The
CLAUDE.md edit is held against RUNBOOKS by
`tests/test_rg_d20_instructions_match_the_code.py::test_rg_d20_each_instruction_says_what_the_code_does[e]`:
each loop CLAUDE.md names must match exactly one live RUNBOOKS section, and "cross-setup
validation" matches `## o. CROSS-SETUP VALIDATION` and no other.

**BOUNDARY.** "$30.3130" and "60 calls" are fix 4a's paid panel run, in US dollars, as its own
record states them; "60 draws" and "$35" for the E2 remainder's check are the coordinator's ask and
the operator's approval. "All 27 pages" is the committed corpus, `data/dossiers/*/dossier.json` at
main `4b2f0cb9`. The default in item 8 would set the E2 cap at about $36.38 ($30.3130 × 1.2). The
operator approved $35, and the operator's figure governs.

**WHAT IT COSTS / WHAT IS ACCEPTED.** Each default is reversible and each is a default, not a
ruling. If the operator reverses one, the PR that built it is reverted or amended, and a new record
says so. Two defaults rest on a run over the whole corpus. Under default 1 no check turns HARD
until it has a clean record on all 27 pages. Default 9 moves R4's inputs, a decision-path change,
so S3's PR shows its run on the 27 pages before it merges.
