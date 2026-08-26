---
id: 
status: recorded
date: 2026-07-27
prs: [194, 212, 212]
supersedes:
superseded-by:
migrated-from: STATE.md governance log
---

1. **Divergence recorded.** Nineteen PRs (#194–#212) ran outside the advisory thread. #212 nulled
   the live BUY on an **unverified** staleness alarm; verification subsequently refuted ~80% of
   that premise while confirming real deterioration. The executor's STOP sequence and the
   status-provenance gate caught the divergence **before the record could contradict the ledger**.
   The close was **LEDGER-ONLY** (operator-confirmed): no market trade, no realized P&L.
   *Divergence continued during the amendment pass itself: PRs #213–#215 merged out-of-chat
   mid-exchange (origin/main 25afc96 → 8dd83c7, including the report re-design diagnosis and the
   operator capacity parameters); the same-day reporting rule applies from today. Shape-read of
   #194–#215 queued (queue item 3).*
