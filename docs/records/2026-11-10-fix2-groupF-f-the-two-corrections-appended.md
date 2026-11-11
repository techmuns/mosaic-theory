---
status: open
date: 2026-11-10
prs: []
supersedes:
superseded-by:
---

# Fix request 2, group F, RF-D7: the two corrections are APPENDED on the primary's store through the ledger CLI — R-GOOGL (340.65 on 2026-08-27) and R-VRRM-screen2-20260617 (4.44 on 2026-06-18) — and the committed ledger goes from 7 rows to 9; VRRM now matures 2026-12-15

**WHAT.**
- **The one write to the primary's `data/vinci.db` this stream makes**, as the operator approved
  on 2026-11-10. It ran after the mechanism (#954, `5ec1dc7c`) and the writer's tagging fix
  (#955, `5e3def4a`) merged, from `main` at `5e3def4a`, in a clean worktree whose `data/vinci.db`,
  `data/cache` and `.env` link to the primary's (RUNBOOKS §l). It went through the ledger CLI only:

  ```
  vinci correct-entry V-GOOGL --reason "RF-D7: the entry is the last US close completed at the decision moment (operator ruling 2026-11-09, approved 2026-11-10); the sealed close was stale"
  vinci correct-entry V-VRRM-screen2-20260617 --reason "<the same>"
  ```

  Each was run with `--dry-run` first, which printed the same rule and left the store unchanged.
- **The store.** No other process held it open, and it had no WAL or journal.

  | | When (UTC) | sha256 | Size | Ledger table |
  |---|---|---|---|---|
  | Before | 2026-11-10T12:44:57Z | `3106433fe68c98fa185b1859407ba9aa473245f5262e793e24010dadbfa4a363` | 399,147,008 | 1 row: `V-VRRM-screen2-20260617` |
  | After the dry runs | — | `3106433f…`, unchanged | — | — |
  | After | 2026-11-10T12:45:05Z | `07575ae439902c601d191347592445f7d3d8d370d392a3fd8a110ac1bbad6d00` | 399,171,584 | the 9 committed rows, equal row for row to the export |

  The other six committed rows went into its ledger table by the command's re-seed, as #954's
  record said they would. `run_monthly` re-seeds every snapshot table into this store anyway.
- **The two rows**, as written:

  | Row | Corrects | Entry | Horizon | Origin / sleeve | Appended (UTC) |
  |---|---|---|---|---|---|
  | `R-GOOGL` | `V-GOOGL` (BUY) | 340.65 @ 2026-08-27 | 199 days → 2027-03-14 | `followed` / `quality` | 12:45:04 |
  | `R-VRRM-screen2-20260617` | `V-VRRM-screen2-20260617` (AVOID_TERMINAL) | 4.44 @ 2026-06-18 | 180 days → **2026-12-15** | `screen` / `overshoot` | 12:45:05 |

- **The snapshot.** `data/snapshots/decision_ledger.jsonl` went from 7 rows to 9: the 7 committed
  lines byte-identical, plus the two. It is committed alone as an artifact commit, with no code.

**WHY.** These are the operator's ruling (2026-11-09) and approval (2026-11-10) for RF-D7's
committed rows:
`docs/records/2026-11-10-fix2-groupF-d-two-stale-seals-corrected-by-appended-rows.md` and
`docs/records/2026-11-10-fix2-groupF-e-a-correction-row-is-tagged-and-the-suite-reads-a-corrected-ledger.md`.

**HOW VERIFIED.**
- **The monitor on the corrected committed ledger** (`vinci monitor --ref 2026-11-06 --out
  <scratch>`, total return):
  - GOOGL reads 340.65 @ 08-27: −16.35%, −11.94 pts against SPY, horizon 2027-03-14.
  - VRRM reads 4.44 @ 06-18: −50.68%, −43.50 pts against IWM, horizon **2026-12-15**.
  - IT and both SMPL rows are unchanged.
  - The spread is **+66.89 pts** (price return +66.88; it was +71.55 before the correction).
  - The day carries both correction notes.
- **Scoring on a `.backup` copy of the corrected store** (as of 2026-11-10, the real Tiingo and
  Polygon sources held to the ledger's names and benchmarks; 3 live Tiingo requests: IWM, SMPL,
  VRRM):
  - Every decision is read at its corrected entry: VRRM 4.44 @ 2026-06-18 → 2026-12-15, GOOGL
    340.65 @ 2026-08-27 → 2027-03-14.
  - VRRM's interim row passes the split-basis check against the store's own 2026-06-18 close.
  - The report names both corrections. IT and GOOGL are pending only because the store holds no
    MDY or SPY bars, which `run-monthly` ingests.
- **The full offline suite on the committed 9-row ledger** passes (`bin/commit`).
  `frontend/build.py` on it changes nothing under `frontend/`.

**BOUNDARY.**
- The store's sha256 and sizes: `shasum -a 256` and `ls` on
  `/Users/mac/Documents/GitHub/mosaic-theory/data/vinci.db` at the stated UTC times.
- Row counts: the store's `decision_ledger` table, read read-only, and the committed snapshot.
- Returns and spread: the monitor at `--ref 2026-11-06`, screen-origin rows for the spread.

**WHAT IT COSTS / WHAT IS ACCEPTED.**
- **The rows are permanent.** The ledger refuses an UPDATE or DELETE, and there is one correction
  per decision. They were written only after the full suite had passed against the fixed writer's
  9-row export (#955).
- **The web still reads the sealed entry** until its own PR lands (previewed first, for the
  operator's approval): the ledger page and the card join skip a CORRECTION row but do not apply
  it.
