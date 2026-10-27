# Screenshots — the monitor marks a resolved row at its horizon close (2026-10-27)

**A REHEARSAL, NOT THE BOOK.** Nothing here is a committed monitor day.

How the pages were produced:

1. `vinci monitor --ref 2026-10-26 --out <scratch>` ran in a scratch root on two inputs:
   - an APFS clone of the primary checkout's price cache;
   - a LEDGER COPY with two horizons shortened, so that two rows resolve inside the data: VRRM to
     119 days (2026-10-14), and IT to 80 days (2026-10-08).
2. Each written day was installed as the latest monitor day of a scratch copy of the frontend:
   - `*-before.jpg` is `origin/main` 56500bb1, the code and the day it wrote;
   - `*-after.jpg` is this branch, the code and the day it wrote.
3. The scratch copy's ledger mirror carries the same shortened horizons, so each card is
   self-consistent. The real ledger (`data/snapshots/decision_ledger.jsonl`, sha256 `43d77c50…`)
   was not touched.

| file | view | before | after |
|---|---|---|---|
| `decision-log-row-*` | Decision log, VRRM's mark row | "Current $3.09 @ Oct 26, 2026", 131/119d | "Horizon close $2.94 @ Oct 14, 2026", 119/119d |
| `spread-card-*` | Decision log, BUY−AVOID spread card | +50.41 pp, every row at Oct 26 | +43.17 pp, "resolved rows at their horizon close" |
| `panels-the-call-*` | Monitor panels, VRRM, The call | "now $3.09" | "horizon close $2.94" |
| `dossier-odds-*` | Dossier IT, implied-odds line | "at $231.03 (Oct 26, 2026)" | "at its horizon close $195.41 (Oct 8, 2026)" |

None of the changed text sits inside a `<details>`, so the collapsed and print (force-open) states
show the same line.
