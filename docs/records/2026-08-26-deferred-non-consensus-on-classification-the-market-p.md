---
id:
status: recorded
date: 2026-08-26
prs: [506]
supersedes:
superseded-by:
migrated-from: STATE.md §4 Deferred
status-note: `recorded`, not `open` — STATE.md §4 keeps the item and its unlock trigger and is the authority on whether it is still deferred; a record never is
---

# **Non-consensus on CLASSIFICATION.** The market prices a name by the wrong reference class (a

*The item and its unlock trigger stay in STATE.md §4, which remains the authority on
whether it is still deferred. This is the detail that stood beneath it, verbatim.*


**SLEEVE ARCHITECTURE — the edges become a REGISTRY, not a fork (decided 2026-08-08; build
briefed, Phase 0 is this record).** The whole dossier pipeline is hard-bound to overshoot at SEVEN
surfaces — the synthesis prompt ("two readings of a sharply de-rated name"), the proposal mapping
(`strongly-bearish → AVOID_TERMINAL`), the page headline ("What broke — and did it fall alone?"),
the two-label `Verdict` enum, the spread math (exact-identity filters at **7 sites** — 6 in
`scoring/metrics.py`, 1 in `scoring/harness.py` — so a third label would vanish from every curve
SILENTLY), the R1-shaped underwrite template, and the ledger entry gate. **Seven surfaces but NINE
code sites:** the proposal mapping and the page headline each exist in BOTH renderers
(`verdict.py` ↔ `dossier.js`, `render.py` ↔ `dossier.js`) and must move together — the twin rule. That was correct while one edge existed. It stopped being correct the day a
followed megacap was committed (UBER, PR #368): the machine now asks a de-rating question about a
name that never de-rated, and its bearish twin label would record "terminal" on a compounder — a
FALSE RECORD in an append-only ledger.
**A `sleeve` = a tagged strategy book with its own playbook, verdict labels, and attribution
curve** (the standard buy-side/allocator term; one prior prose use, `OBJECTIVE_FUNCTION.md`).
The insight that makes ONE engine serve all of them: every edge here is already defined WITH its
evil twin, and the synthesis schema (bull points / bear points / evidence balance, NO verdict
field) is ALREADY the universal shape of "case vs twin". Only the two case DEFINITIONS are
hardcoded. So a sleeve is a registry row — {case, twin, page question, proposal 3-row mapping,
verdict labels} — and adding sleeve N+1 touches no assembler, no schema, no ledger mechanics.
**The lines that do NOT move:** the machine still proposes and never concludes; the mapping stays
face-validity-frozen and never outcome-tuned; `mixed` still proposes nothing; the edge-basis gate
still runs (sleeve = WHICH BOOK, edge-basis = WHICH CLAIM — orthogonal, both required); and the
PRIMARY BUY−AVOID spread stays **screen-origin overshoot ONLY** (the 2026-08-07 segmentation
decision; pooling megacap verdicts into the fund's proof-number silently changes what it means —
the GIPS composite discipline, and what an allocator will ask for).
Four sleeves recorded; **two active in the decision ledger at v1**:
