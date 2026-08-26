---
id: S9
status: recorded
date: 2026-07-31
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**S9. ROUTING STATES ITS POLICY — built 2026-07-31, solo. DEFAULT UNCHANGED.**
The gates record NOT_EVALUATED; the ROUTER ignored it. Four forward/admit points, derived:

| # | point | reads |
|---|---|---|
| 1 | `run.py` G1 forward — `if g1 is not PASS: continue` | **the gate's result** (PASS required) |
| 2 | `run.py` G2 forward — `if g2 is FAIL: continue` | **merely "not FAIL"** — UNKNOWN forwarded |
| 3 | `screen2.evaluate_screen2` admit — `FAIL not in results and G1 is PASS` | **mixed**: G1 explicit, G2/G3 "not FAIL" |
| 4 | the row's `admitted` field | records the outcome, decides nothing |

**ONE SETTING, TWO VALUES:** `RoutingPolicy.CARRY` / `.DROP`, threaded through points 2 and 3.
**CARRY is the DEFAULT and is today's behaviour exactly**, so the `-03` run reproduces. It lives in
`vinci/schemas/candidate.py` beside `GateResult` — a leaf both modules already import, so no cycle.
**The manifest records it** (`RunManifest.routing_policy`, defaulted to CARRY so a manifest written
before the field reads as what that run actually did): a pool count means nothing without it.

**AND THE MANIFEST IS BOUND TO THE RUN (review finding).** `routing_policy` was recorded on the
manifest AND passed to the runner with NOTHING binding them, so a run could execute under DROP while
its own record said CARRY — the record stating something the run did not do, which is exactly what
the manifest was added to prevent. `screen_universe` now refuses when the manifest on disk records a
different policy, and the policy travels in the returned stats so a count is never quoted without it.

**THE POOL UNDER EACH POLICY** (population: the 1,780 of run 2026-07-29-03):
CARRY **331** · DROP **49** · DROP removes **282** — 279 at G3, **3 at G2**.

**THE 3 G2 NAMES ARE OPI, ARIS AND MRLN** — the same three out-of-range start anchors #294 bounded.
The bound made G2 say "could not judge"; the router forwarded them to G3 anyway and admitted all
three. Under DROP they stop at G2. That closes the loop the anchor bound opened.

**AND THE THEME ARCHIVE PROTECTED NOTHING** (rides with this PR). `candidate_themes.jsonl` — the
only committed cluster file — was overwritten **before** the immutable snapshot was written, and
`data/scan_history/` was git-ignored, so "a monthly sweep must never clobber the prior harvest"
described an intent the sequence did not implement. Now: **archive first, pointer last**,
`--no-scan-history` with a write **REFUSED**, and the directory tracked (derived from public EOD +
EDGAR SIC; no licensed content). **Detection was NOT run.**
