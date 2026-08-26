---
id: 
status: recorded
date: 2026-07-31
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**S4a. RETENTION — THE DESIGN, settled 2026-07-31 so the next session builds rather than designs.**
Recorded ahead of code, per the durable-write-first rule.
- **SHAPE.** `data/snapshots/screen_runs/<run_id>.jsonl`, append-only, `run_id` = the reference date
  + a monotonic suffix so two runs on one date cannot collide. Never overwritten —
  `candidate_records.jsonl` being rewritten each run is what made the 2026-07-27 bound luck rather
  than method.
- **TWO GRAINS — REASSIGNED 2026-07-31, because the first assignment was wrong about WHERE the
  funnel narrows.** The design put the thin grain on the 1,482 and called them "filtered at the
  universe stage". Measured against the runner, they are not: `screen_universe` loads all ~1,800
  cap-band members and runs **G1 and G2 on every one of them**, so those names WERE assessed and
  carry real gate inputs and per-gate outcomes. The true funnel is three stages —
  `build_universe` (all listed → 1,800: cap band, liquidity, SIC, security type), then G1/G2
  inside the screen, then G3 + distress. Writing the assessed names thin would have discarded the
  calibration data the grain exists to capture, and left what `build_universe` drops — the actual
  blind spot, and S3's home — with no row at all. **Both are retained, reassigned:**
  - **CANDIDATE rows (~1,800/run), full** — EVERY name the screen touches, not the survivors. The
    gates ran on them, so the record says what the gates saw; a name dropped at G1 carries one gate
    rather than three.
  - **UNIVERSE rows, thin** — emitted by `build_universe` for every name it DROPS, across all eight
    enumerated stages (`no_price`, `no_shares`, `out_of_band`, `below_adv_floor`, `unknown_sic`,
    `non_operating`, `unknown_type`, `non_common_equity`). Enumerated rather than described: a stage
    missing from the grain is a stage with no evidence trail, which moves the blind spot instead of
    closing it. A shipped guard refuses the run if the emitted row count and the counted drops
    disagree.
- **THE CONFIG IS STAMPED ONCE PER RUN, NOT PER ROW** (operator). Every row carries a `run_id` and a
  row filed under another run's id is refused, so the reference already exists; copying the config
  onto ~1,800 rows buys nothing and makes one threshold change read as 1,800 changes in a diff. The
  `RunManifest` is **write-once** — rows are append-only and the manifest cannot be rewritten, so a
  completed run is immutable end to end. Rewriting it would silently RE-LABEL every row filed under
  it, the one edit that could make a whole run mean something else.
  **WHY THE UNIVERSE PASS CANNOT BE DROPPED:** a name filtered at the universe stage is also a
  DISCARDED name, and the whole premise is that a screen discarding names that later outperform has
  negative alpha. Retaining candidates only would make the universe filter unmeasurable by
  construction — and **S3 is exactly a universe-stage defect** (a falsely-stamped market cap decides
  band membership), so candidate-grain retention would leave the deepest of the five items with no
  evidence trail at all. SIZING, so this is a decision and not a surprise: ~430KB/run, ≈22MB/year
  weekly, JSONL and compressible — acceptable for a private repo, and re-check if the universe grows.
- **ROW.** `{ticker, run_id, reference_date, gate_inputs: {...each with its own as_of...},
  per_gate: {g1: PASS|FAIL|NOT_EVALUATED, g2: …}, outcome, not_evaluated_reason}`. **Gate inputs are
  stored with their OWN stamps**, not the run's — the `relative_return` frontier work is precisely
  why (a gate input claiming the reference date while its data stopped earlier is what made the
  benchmark incident invisible).
- **THREE OUTCOMES, NOT TWO.** `PASS` / `FAIL` / **`NOT_EVALUATED`** with its reason (item 22 on the
  screen path): a name whose window was start-truncated could not be assessed and must never look
  like one that was assessed and rejected. This is S1's split-on-cause landing in the data model.
- **WHY CALIBRATION, NOT FORENSICS.** The reject set is the population for measuring whether the
  gates select for return at all. A screen discarding names that later outperform has NEGATIVE alpha
  and nothing in the current design would show it — survivors-only retention can only ever confirm.
- **THE GUARDRAIL THAT BINDS HERE.** Retention is READ-ONLY evidence: no threshold, weight or gate
  may ever be set from it (validate forward, never tune on outcomes). The rows exist to FALSIFY the
  screen, never to fit it — a fitted gate is the replicable signal this fund is not.
- **THE READ-ONLY RULE, IN ITS OPERABLE FORM** (operator 2026-07-31, replacing "no threshold may
  ever be set from it" — right in intent, unenforceable in fact, since any redesign is informed by
  something):
  > **Retention may FALSIFY a design. Any parameter chosen after looking at it must be validated
  > FORWARD, on runs retention had not recorded when the choice was made.**
  Permits *"the screen's rejections have positive alpha, so the design is wrong."* Forbids *"tune
  the threshold to what would have worked."* And it is CHECKABLE, which the first form was not: a
  parameter change carries the date it was made and the runs it was tested on.
- **BOTH GRAINS STAMP THE CONFIGURATION, not only the inputs** — gate thresholds, benchmark
  identity and lookback on candidate rows; the band rule and its cap threshold on universe rows.
  Without it, comparing two runs compares two different screens and nothing says so: if G2's ceiling
  moves off −15%, every earlier row silently means something else. **The record must say what TEST
  was applied, not only what went into it** — the stamp rule (a stamp belongs to what it names)
  applied to the screen's own parameters.
- **BOTH GRAINS MUST BE JOINABLE TO OUTCOMES** — ticker + run date against the price store, for THIN
  rows as much as full ones. Calibration only pays if a discarded name's later return is
  recoverable, and the universe rows are where it matters most: that is the filter nothing has ever
  measured. Verify the join on the first real run rather than assuming it.
- **BUILD ORDER INSIDE THE PIECE:** writer + schema + round-trip pin → wire the screen to emit BOTH
  grains → one real run, on which the outcome-join is verified → then the hold lifts only after
  piece three.
- **SCALE OF WHAT WAS UNMEASURED:** 1,482 of 1,800 names are filtered at the universe stage against
  318 reaching the screen. **The biggest filter in the funnel discards 82% of the universe and had
  no evidence trail** — which is why `universe.py` (S3) was called the deepest of the five, and why
  candidate-only retention would have left it unmeasurable by construction.
