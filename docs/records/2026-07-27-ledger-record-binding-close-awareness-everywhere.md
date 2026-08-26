---
id: 
status: recorded
date: 2026-07-27
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md governance log
---

21. **LEDGER→RECORD BINDING + CLOSE-AWARENESS EVERYWHERE — 2026-07-27 (bug, operator-spotted).**
   The operator asked why a `watch` record headlined `BUY`. It was a real defect, and bigger than
   the symptom. THE CAUSE: the ledger joined to a card **by TICKER alone** — correct while one
   ticker meant one record, broken by supersession. SMPL's BUY was decided 2026-07-21 against the
   record now ARCHIVED; the live record was reissued 2026-07-27 and **opened no position**
   (`entry_price` is None) — so the reissued card advertised a verdict it never made, and the SAME
   row displayed on two records. RULE ADOPTED: *a record owns a ledger row only if the row was
   decided during its tenure* (`underwrite_date` is the latest at-or-before `decided_at`).
   Never-superseded names are unaffected.
   **THE WIDER FINDING — the close-aware fix had reached ONE of FOUR surfaces.** The other three
   still showed a bare live BUY: the dossier Brief chip, the dossier INDEX badge, and the decision
   log — which had **no close handling at all**. Root cause was one layer down, in the JS ledger
   loader: it mapped EVERY row into `entries`, and a close row repeats the ORIGINAL verdict for
   provenance, so **the dashboard reported 5 logged / 4 BUY against a true 3 / 2** and last-row-wins
   decided which row a per-ticker lookup returned. Fixed at the loader — the JS twin of
   `vinci.monitor.decision_rows`/`pair_closes`: partition first, attach each close to the row it
   closes, derive the realized return from the two frozen prices (never stored). Every consumer
   gets close-awareness from that one place. `resolved` is deliberately untouched: a call is scored
   at its horizon whatever happened to the position — **exits never launder the track record**.
