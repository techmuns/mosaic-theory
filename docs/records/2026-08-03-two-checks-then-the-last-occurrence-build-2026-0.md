---
id: 
status: recorded
date: 2026-08-03
prs: []
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**TWO CHECKS, THEN THE LAST-OCCURRENCE BUILD — 2026-08-03 (operator). BOTH CHECKS CAME BACK
"NOT A BUG", AND BOTH WERE WORTH RUNNING.**

**CHECK 1 — THE EXACT 2× IS A COINCIDENCE; NOTHING IS DOUBLE-COUNTED.** $24.72M measured against
the audit's $12.36M is exactly 2.000×, which would be the signature of an amendment summed beside
its original. Measured, three ways: **zero `4/A` filings exist** in the 24m window (76 filings, all
form `4`, and `recent_filings` matches the form string EXACTLY so an amendment could not enter
anyway); all **16 `S` lines are unique** on `(txn date, owner, shares, price)`; every filing lists
**exactly one** reporting owner. And the coincidence is not even improbable — **77 different subsets
of the 16 lines sum to within ±1.5% of $12.36M**, so a subset match would have been evidence of
nothing. The audit's figure is not reproducible from EDGAR and no decomposition is invented to make
it; **direction: the audit UNDERSTATED the selling.**

**CHECK 2 — THE SPLIT RE-ADJUSTMENT IS DESIGN, NOT LUCK.** `screen_universe` re-pulls a rolling
**1825-day (5-year)** window every weekly run (`screens/run.py:104–106`); `run_monthly` uses 730d.
`ingest_prices` **does not skip days already stored** — it fetches every trading day in the window —
and `INSERT OR REPLACE` overwrites, while the HTTP TTL (24h) is far shorter than the 7-day cadence,
so nothing blocks the re-fetch. **A split therefore re-adjusts every bar within 5 years on the next
Monday.** FUBO's 1,254 bars spanning exactly 2021-07-30 → 2026-07-29 are that window, not luck.
**THE BOUND, stated because nothing enforces it:** bars OLDER than the rolling window are never
re-fetched by any automated path, so a store deeper than 1825d could hold pre-split bars
indefinitely. **Measured: 0 securities sit more than 30d beyond the window** (3 sit 29d beyond, from
the documented NCNO-class `--aggs` backfill). **A COUNTING CORRECTION CAUGHT IN THE SAME BREATH:**
the first pass reported "1,461 of 1,860 securities deeper than the window", which was an artifact of
a ONE-DAY cutoff drift — the window slides daily while the bars were written at an earlier reference
date. At 30d slack the real number is **0**. A number that did not say what it covered, inside the
read about numbers that do not say what they cover.

**BUILT — THE LAST *AND LARGEST* OCCURRENCE, ALONGSIDE A WINDOW THAT NOW STATES ITSELF.**
`compose_insider_line` (extracted pure, so it is testable without EDGAR — the network path could
otherwise only be pinned with a hand-rolled stub the house rule forbids). Four rules, each with a
mutation-verified red: **the window is stated** (`sells 0` → `sells 0 — in the last 182 days`);
**the sides are NEVER netted** (the old `net +90.0K sh` is gone — latent, not live, only because no
sale fell inside the window); **counts carry people AND dollars**; **absence carries its horizon**
("no sale in the 3y scanned", never a bare none).
**THE FIRST REAL RUN KILLED THE FIRST DESIGN, and that is why it was run.** "Report the last
occurrence" ALONE reproduced the defect in smaller type: SMPL's most recent sale is **$0.11M nine
months back**, so printing only that states a trivial last sale and implies it is all there is,
while the $24.7M episode 21 months back stays hidden — **a smaller number in the same flattering
direction as the count it replaced.** The largest now prints beside it (`largest sale $8.06M,
director, 2024-11-07 (~21mo ago)`), suppressed only when it renders identically to the last.
**TWO MORE FOUND BY RUNNING IT, both invisible on SMPL:** AORT printed `See Remarks` as a ROLE —
EDGAR's own placeholder reaching the page as machine dialect; and CNXC's largest sale is
**6,000,000 sh @ $22.25 = $133.5M on 2026-04-29**, a single real transaction by a filer who is
neither officer nor director. `isTenPercentOwner` is now its own role, because **a block holder
distributing is not management selling** and a reader must not confuse them. CNXC's is INSIDE the
182-day window, so that name's line was already carrying a $133.5M sale as the bare count "1".
**A CONSTRAINT FOUND BY READING, NOT ASSUMING:** `render._fmt_insider` matches the trailing
`other X×n` segment with a **`$`-anchored** regex, so anything appended after it silently leaves raw
Form-4 codes on the page. The `other` segment stays last, pinned structurally.
**DELIVERY PATH — this is MECHANICAL, not render-only.** The label fix (`Insider activity (Form 4)`,
no horizon in the heading, since the value now carries two) reaches every name on the next deploy;
**the line itself needs a re-assembly or a refresh**, so the eleven committed dossiers keep the old
`net +90.0K sh` form until then. Nothing is re-assembled here.
**RECORDED, NOT FIXED (operator ruling): a loop-and-assert test should assert the loop RAN.**
`for c in cells: assert …` over an empty list passes exactly as loudly as a clean corpus — #290's
*"an empty parametrisation passes exactly as loudly"*, learned and not applied. The skip guard
shipped in #318 sidesteps it, and with data present the loops iterate, so it is not worth a fix.
**RECORDED — THE CI ASYMMETRY.** CI cannot hold the licensed CIQ workbooks, so **A1's fleet baseline
and A2's acceptance run LOCALLY ONLY**. A green PR check does not verify the A-track's most
important tests; `bin/commit` is the only place they execute, and it is not a second opinion.

**THE GATE IS NOW ENFORCED WHERE A REVIEWER CAN SEE IT — `.github/workflows/gate.yml`, 2026-08-03
(review finding on #318).** The reviewer's point: every PR body carried *"ruff clean · mypy --strict
clean · full offline suite green"* while **the only check on the PR was the Cloudflare deploy**, so
the claim was unfalsifiable at review time. That is this repo's own rule — *verify by showing real
runs, not asserting* — pointed at its own process. `bin/commit` closed the AUTHOR's version of this
hole (D16, after three red pushes); it never closed the REVIEWER's, because a local run reaches them
only as pasted text.
**MEASURED BEFORE BUILDING, on a committed-files-only tree (`git archive HEAD` — no
`data/manual/ciq/`, no `vinci.db`, no `.env`): a naive gate would have been PERMANENTLY RED.** ruff
clean, mypy clean, **pytest 12 FAILED — every one in `tests/test_consensus_rows.py`.** A permanent
red is the precise condition that makes *"some tests fail"* the normal state, which is how the three
red pushes got past a gate that was working correctly.
**THE BLOCKER WAS MINE, AND IT IS A GUARD THAT COULD NOT FIRE — the fourth instance of that class.**
`_bundle` skipped inside `except Exception`, and **nothing raises**: with the licensed CIQ absent
`files()` returns `[]` without raising, `CiqBundle.from_files` accepts an empty list, and
`consensus_rows` swallows `CiqUnavailableError` and returns `[]`. Same shape as item 1's completeness
gate, the absence-reason guard naming the wrong object, and #310's no-op `getattr` wiring.
**AND THE FAILURES WERE THE LESS INTERESTING HALF: 11 TESTS IN THAT FILE PASSED VACUOUSLY.** The
range check loops `for c in cells` over an empty list and asserts nothing, so a clean runner reported
**11 green tests that checked nothing** — the hollow-test class, live and unnoticed.
**FIX: condition the skip on the FILE LIST, which is the convention every sibling already used**
(`test_no_backfill.py`, `test_segment_absence_and_relationship_route.py`: *"licensed CIQ bundle for X
unavailable (never committed)"*). This file was the outlier; nothing new was invented.
**VERIFIED BOTH DIRECTIONS** (the offline-fixture precedent): clean tree BEFORE → *12 failed, 11
passed (vacuous)*; clean tree AFTER → **23 skipped, honest**; this worktree WITH the licensed export
→ **23 passed, unchanged**.
**THE CI RUN IS THE EVIDENCE, not a claim about it** — run `30809566256`, all three steps green:
`All checks passed!` · `Success: no issues found in 117 source files` · **`1515 passed, 49 skipped,
13 deselected`, 0 failed.**
**`fetch-depth: 0` IS LOAD-BEARING, and verified rather than assumed:** `test_state_identifiers.py`
validates the S/D lint against the REAL historical collision at `c112f25` and skips when that commit
is unreachable — measured, **5 passed with history vs 4 passed / 1 skipped without**. At GitHub's
default depth-1 the test guarding STATE.md would silently skip on every PR that edits STATE.md,
which is this entry's own defect class shipped into the fix for it.
**IT IS A FLOOR, NOT A REPLACEMENT — do not read a green PR as a full gate.** The runner cannot have
the licensed CIQ workbooks, the working store, or any key (security non-negotiable; the workflow
references NO secrets), so the CIQ-bound extraction pins — A1's fleet baseline among them — run
**only** where the export exists. **`bin/commit` stays mandatory before a push.** One gate, two
places: the workflow runs the same three commands in the same order, and a change to either must
change both.
