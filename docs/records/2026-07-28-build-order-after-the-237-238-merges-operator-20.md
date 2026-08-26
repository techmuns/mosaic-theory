---
id: 
status: recorded
date: 2026-07-28
prs: [237, 238]
supersedes:
superseded-by:
migrated-from: STATE.md §5 archive
---

**BUILD ORDER AFTER THE #237/#238 MERGES (operator 2026-07-28): 18, THEN 22.** Together they
close the whole class of *the dossier under-representing what the fund already knows* — the
information-regression trio, the false UNKNOWN, N7's unrendered triggers and the WATCH gap. Item 1
stays BLOCKED on ingestion (though its re-spec means the contract itself is no longer unsafe
without it); **20, 21 and 23 are mechanical and may follow in any order**; 25 is priced but not
scheduled; 24 needs an operator policy line before any build encodes it.

25. **MATERIAL-DELTA TEST — the general version of item 17 (operator-specified 2026-07-28).**
    A **DELTA** test, not a level test: any line whose YEAR-OVER-YEAR CHANGE exceeds 10% of market
    cap must be surfaced. This is the better primitive and it dissolves all three false-fire
    classes that forced item 17's block scoping, WITHOUT needing block scoping at all — on SMPL it
    fires on the writedown (−60.9 → −391.9 = 36% of mcap) and on nothing else: COGS barely moves,
    the `Filing Date` serial does not move, the share count moves ~6M units. It also extends PAST
    the income statement, which item 17 cannot: balance-sheet and cash-flow lines get the same
    test, closing the capex 6 → 20 → 28 gap item 17's rename records. Price the build; if it holds
    up, item 17 becomes a special case of it rather than a parallel mechanism.
28. **~~SCENARIO-INPUT DISCLOSURE~~ — BUILT 2026-07-29 (Batch A). AND IT WAS A TWIN LAG, NOT A
    MISSING DISCLOSURE.** The mechanism pass expected a new disclosure; reading the code found the
    inputs ALREADY in `ScenarioRecord.facts`, source-stamped, and already rendered by the WEB card
    (`uw-card.js` — a `<details class="uw-inputs">` block, plus `recipeLine()` for the chain since
    schema 1.1). `render.py` printed NEITHER. The md twin lagged the web on two blocks that had
    existed there for versions — the same shape as item 22's N7 half, found in the same pass.
    **PRINTS EVERY RECORDED FACT, not a fixed shares/D&A/net-debt trio**, because the trio is
    recipe-specific: R1 records carry an absolute D&A figure, R2 records carry a D&A ratio + a
    share-growth term (+ burn-to-breakeven on MVST). A hardcoded three would print blanks on half
    the corpus and omit the inputs that actually drive the other half.
    **THE GENERAL FORM (operator, 2026-07-29 — this CORRECTS the spec, which said only "print
    shares, D&A and net debt"): INPUTS WITHOUT THEIR CHAIN ARE STILL A SYSTEM TO BE SOLVED
    BACKWARDS.** `recipe_formula` rendering nowhere is *why* the auditor reverse-solved 93.77M at
    all. Disclosure of inputs is necessary and not sufficient; the operation that combines them is
    part of the disclosure.
    **THE CHAIN SHIPPED BECAUSE THE RED FAILED — the most useful thing in this build.** The first
    cut printed the inputs and not `recipe_formula`, and the recompute test FAILED at $21.38
    against a recorded $24.24: the D&A add-back was invisible, and I made the auditor's own mistake
    while verifying the fix for it. **Inputs without their chain are still a system to be solved
    backwards**, which is precisely P7's complaint. Both now print; the recompute walks the
    document's own stated chain over the document's own printed inputs and matches every leg on
    every R1 name.
    **PRECISION IS LOAD-BEARING HERE:** `%g` at 6 significant figures renders 93.677801 as
    93.6778, and this item exists because an auditor back-solved 93.77 against that number —
    printing a rounded input would reproduce the defect in smaller type. Pinned.
    **ORIGINAL SPEC, kept for the record:**
    Print **shares, D&A and net debt inside the scenario block**, so every scenario
    value recomputes from figures on the same page. ORIGIN: the auditor could not reproduce a single
    scenario cell from anything the dossier printed — they solved the system backwards and landed on
    93.77M shares against our recorded 93.678M, which is itself the proof (the inputs were
    recoverable only by inference). Distinct from item 24, which is the SHARES-BASIS policy
    question — this is disclosure of whatever basis is chosen, and it is queued because the audit
    verified NO queue item covered it. Distinct also from queue item 2, which governs numbers
    quoted in the RECORD'S prose, not the dossier's scenario block. RED: assert every scenario
    value recomputes from figures printed in the same document.
27a. **DUPLICATE-DEFINITION DETECTOR + FROZEN BASELINE (operator split 2026-07-28; ships in the
    STATE-topology slot; SIZED UP 2026-07-28 — the prototype heredoc NEVER LANDED in the repo, so
    27a is BUILD THE DETECTOR **plus** baseline, not baseline alone).** The detector plus a BASELINE recording the ten known duplicates as
    accepted-for-now: **the build fails only on the ELEVENTH.** Zero curation, ships immediately.
    Why the split matters more than it sounds: the instance that started this was one I INTRODUCED
    WHILE FIXING THE SAME CLASS, so 27a closes the hazard against NEW instances now rather than
    after ten judgment calls. NOTE — the detector must NOT be wired un-baselined: it finds ten
    today, so wiring it bare turns the suite red on merge. That is exactly the operator's own check
    on #240 ("if it's wired to CI while finding ten unpinned duplicates the suite should be red");
    the baseline IS the answer to it.
    **FEASIBILITY, ANSWERED NOT ASSUMED (2026-07-28).** The operator asked to be told if "what the
    twins consume" is not enumerable. IT IS — a prototype detector matching string-literal sets of
    ≥3 members across py↔js twins finds **TEN duplicated sets live today, none pinned**. Proof it
    finds REAL duplicates rather than noise: the driver keyword/weight vocabulary (12 members,
    `render.py:1786` ↔ `dossier.js:466` — same words AND the same weight in two languages), plus
    `_CS_COLS` (see 27b). The prototype was a throwaway and is NOT in the repo; 27a is where it
    lands, baselined.
