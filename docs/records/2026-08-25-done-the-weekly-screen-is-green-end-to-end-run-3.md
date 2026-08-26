---
id: 
status: shipped
date: 2026-08-25
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**DONE — THE WEEKLY SCREEN IS GREEN END TO END (run 32827750106, 2026-08-25).** First clean run
since 2026-08-03. `screen_run_at` moved **2026-08-14 → 2026-08-24**; every step succeeded including
the gate, which had never once executed in this job before today. Committed as `c88962b` (snapshots
+ mirrors) and `9ad32b1` (`run status (success)`).

| | |
|---|---|
| reference_date / universe_as_of | `2026-08-24` — the last completed session, from the data |
| considered → universe → survivors → candidates | 7,667 → 1,812 → 350 → **268** (was 281) |
| price fixture | all nine series `2026-08-24`, 432 bars, one vintage |
| maintenance route | unchanged: IT, LLY, MVST, NCNO, NFLX, UBER, V, WERN |


**FIRST RUN AFTER THE FIX (32818611056, 2026-08-25) — THE SCREEN PASSED, MY OWN NEW STEP DID NOT.**
`weekly run: dating from the data — last completed session 2026-08-24` — the wall-clock fix worked
on its first real firing, and the screen completed (7,667 considered → 1,813 universe) for the
first time since 2026-08-03. The **fixture-rebuild step I added in #496 then failed**: `IT — NO
BARS in the local store`.

**WHY, AND IT WAS A DESIGN ERROR NOT A CONFIG ONE.** The job refreshes EOD for the SCREENING
UNIVERSE; the fixture covers the MAINTENANCE-ROUTE set — *by definition the names the screen does
not carry*. Checked against the committed universe snapshot: **six of the nine are outside it
entirely** — IT, LLY, NFLX, UBER, V (megacaps failing the cap band) and **IWM, the BENCHMARK**, a
synthetic `IDX-*` identity that was never an SEC issuer. `build_price_fixture.py` documents itself
as needing a populated local store and being "an operator tool, never imported by the suite"; I
wired it into a job whose store can never satisfy it. Fixed with an opt-in `--refresh` that fetches
its own bars per-symbol (nine aggregate calls, not a second market-wide pull).

**THE ATOMICITY FIX PAID FOR ITSELF IMMEDIATELY** — same PR, first production failure. `NOTHING WAS
WRITTEN`, the gate was skipped, and main's fixture was untouched. Under the previous write-in-loop
builder that abort would have committed a mixed-vintage fixture with the benchmark left behind.

**AND #495 PROVED OUT IN PRODUCTION ON ITS FIRST REAL FAILURE** — `abc0289 weekly screen: run
status (failure)` carries the attempt time, the run URL and the remediation. The four-week blind
spot is closed, verified live rather than in a preview.

**WHY IT TOOK THREE CYCLES, RECORDED SO THE PATTERN IS NOT REPEATED.** Each fix was verified only
as far as the PREVIOUS failure had reached, so every run discovered the next unproven step:
wall clock → fixture-not-rebuilt → fixture-cannot-be-rebuilt-from-that-store. The pass that ended
it walked the REMAINING steps before triggering — simulating the post-run manifest against the gate,
re-testing `--refresh` on a snapshot-seeded store with `price_frontier = None`, and reasoning about
what the re-screen does to the maintained set — and found three more failures in advance, plus two
that the #497 review caught. **The rule: verify forward to the END of the chain, not up to the last
observed failure.** A step that has never executed is not evidence, however green everything
before it is.

**ENDPOINT AGREEMENT, CHECKED NOT ASSUMED.** The refreshed fixture switches provenance from
`polygon-grouped` to `polygon-aggs`, which rewrites most rows. **OHLC is byte-identical across all
427 shared dates**; volume differs by ±1 share on 21 of them (endpoint rounding, relative error
~3e-6). No analytical content moved — the large diff is the `source` tag and five new dates.
