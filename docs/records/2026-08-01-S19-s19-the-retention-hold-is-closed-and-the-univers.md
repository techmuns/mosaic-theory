---
id: S19
status: shipped
date: 2026-08-01
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**S19. THE RETENTION HOLD IS CLOSED, AND THE UNIVERSE SNAPSHOT IS NOW STAMPABLE (2026-08-01).**

**THE HOLD IS CLOSED — its purpose was served, and leaving it ambiguous while three runs happened
was the actual risk.** It existed to prevent evidence destruction before retention landed.
Retention landed in #293; `data/snapshots/candidate_records.jsonl` carries **13 commits** of
history; the runs themselves became tracked in #301 (they had existed only in one worktree).
Nothing it guarded is still exposed. **FUBO's separate standing rule stays ON** — no
post-combination re-assembly exists and the entity-gate build has no record.

**BUILT: `RunManifest.universe_as_of` + `CandidateRow.deciding_cap`.**
- **WHICH POPULATION WAS JUDGED.** `-01` screened the **2026-07-06** universe (1,800, set-identical
  to that snapshot) while `build_universe` wrote **2026-07-29** (1,780); 72 tickers hold rows in
  BOTH grains. The manifest recorded run_id, reference_date, screen, band, routing_policy and
  stages — everything except the population. **Every run without the stamp is permanently
  unattributable**, so this went first: a guard cannot repair the three runs on disk, a stamp
  stops the fourth joining them. Forward-binding; the three committed manifests read `None` =
  *this run did not say*, and must never be back-filled with a guess.
- **THE CAP THAT DECIDED MEMBERSHIP.** All 331 pool candidates carried `market_cap: null ("needs
  shares")` while the universe that admitted them was cap-banded 2,371 -> 1,800 on that number —
  **S3's blind spot in its ABSENT form**, harder to see than a false stamp because nothing looks
  wrong. Now a `StampedInput` carrying the SNAPSHOT's date, never the run's.
- `Store.latest_universe_as_of` / `universe_caps` expose the vintage the members alone cannot state.

**MUTATIONS, all RED** (M2 needed a second pass): cap stamped with the run date · `deciding_cap`
dropped from the row · `universe_as_of` back-filled with `reference_date`. **M2 first returned
GREEN** — the pin exercised the `_deciding_cap` helper and never asserted the field was ON the row,
so the value was computed and had nowhere to go. D22 exactly: the test could not fail on the defect
that would actually occur. Fixed with a round-trip assertion.

**REVIEW FINDING (#310) — THE WIRING WAS A NO-OP, AND IT FAILED SILENTLY.** The first cut read
the id as `getattr(rec, "internal_id", None)`. **`DataRecord` HAS NO SUCH FIELD** — it carries
`identity.internal_id`. So the lookup returned None for every name, `_deciding_cap` returned
None every time, and the whole build did nothing in production: the field existed, the helper
passed its unit test, and no row was ever populated. **A defaulting `getattr` on an untyped
object turned a wrong attribute name into None instead of an error — the S14 class, committed
in the build immediately after the sweep that counted 66 instances of it.** Fixed by threading
`sec_iid` explicitly from the `Identity` the caller already holds; join verified on real data
at **1780/1780 (100%)**.

**AND THE PIN NEEDED THREE ATTEMPTS — D22 three times in one build.** (1) The helper test used
a synthetic dict and stayed green through the defect. (2) An integration pin on the join also
stayed green, because a synthetic `Identity` cannot see how the CALLER obtains its key.
(3) Only a STRUCTURAL pin — `screen_universe` may not read `internal_id` via `getattr`, and
`_keep` must take it as a parameter — reddens on the real defect. *A test that cannot fail on
the defect that would occur is not evidence, however many of them there are.*

**THE 89 EPS-TOO-OLD REFUSALS ARE CORRECT — the alias defect does not manufacture them.**
Overlap between the 89 candidates reading *"last positive annual EPS is older than one filing
cycle"* and the alias-affected names: **0**. #298's bound is firing on real staleness, not on an
extraction artifact. (The 99-name alias defect stands on its own; 3 of its names are `eps_diluted`
and cannot be valued by G3 at all.)

**WHY THE UNIVERSE GRAIN APPEARS ONLY IN `-01`:** `build_universe` is a separate CLI subcommand and
emits the thin grain only when it RUNS. It ran once; the screen ran three times. So **the two
grains rarely co-occur** — the thin grain accumulates per universe rebuild, not per screen run, and
`-02`/`-03` are candidate-only for that reason rather than through any loss.

**VRRM's 123-DAY PANEL IS A CONSENSUS PANEL, NOT AN EXPORT ONE:** `EV/EBITDA (TEV/LTM) 8.5x as-of
2026-03-31 — trailing range 10.4-23.2x over 19 closes`. Consensus staleness PRINTS and does not
gate, so the gate is not being bypassed; the age is disclosed, which is the designed behaviour.
