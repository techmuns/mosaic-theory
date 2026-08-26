---
id:
status: open
date: 2026-08-26
prs: [507]
supersedes:
superseded-by:
---

# Pre-registered: is the cohort split informing the human, or screening for them?

**THE HALF THAT WAS PROVEN.** #501 established that the split never reaches the sort key — a re-rank
with it attached leaves the order and every score identical, verified end-to-end on the real
artifacts. That is a fact about the **code**, and it is settled.

**THE HALF THAT WAS NOT.** A `name-specific` / `industry-wide` pill sits on the queue the analyst
reads *before* choosing what to pull CIQ for. If `industry-wide` names quietly stop being worked,
the split is functioning as a **screen** whatever the sort key does — and an unsanctioned screen is
precisely what this fund's guardrails exist to prevent. The same shape is already an accepted risk
for the machine verdict proposal ("a machine proposal ANCHORS the human"), with the same remedy:
**state the falsifier before the data arrives**, so it cannot be fitted afterwards.

**THE CONFOUND, WHICH MAKES THE OBVIOUS TEST WORTHLESS.** `own` means a large residual; a large
residual means a large idiosyncratic move; and that IS the `idiosyncrasy` axis feeding the priority
score. **`own` names therefore rank higher by construction.** Measured on the live queue
2026-08-26: median rank **own 110 vs cohort 172**, with **21 vs 3** inside the top 50. Comparing raw
worked-rates would measure RANK and report it as anchoring. Every comparison is made **within a rank
band**.

**THE FALSIFIER, PRE-REGISTERED.** Inside a single rank band, the split is judged to be SCREENING if
the rate at which a name is worked differs between `own` and `cohort` by more than **20 percentage
points**, with at least **10 names per arm** and at least **5 of them worked**. Twenty points is set
on face validity — the gap at which a human reading the queue is visibly steering — and never by
trying thresholds against an outcome. "Worked" is the queue's own workflow signal: a committed
dossier, a ledger row, or a scenario record; never a scenario's verdict.

**WHAT HAPPENS IF IT FIRES.** The pill is steering rather than informing, so its PLACEMENT is
revisited: demote it to the tooltip (numbers only, no verdict word), or remove it and keep the
`industry / name` split alone. Not a data question — a surface one.

**STATE TODAY: NOT YET TESTABLE, and that is the answer, not a pass.** 268 queued names, 16 worked,
8 of them in the queue. No band clears both floors. The first cut of the script reported "within
tolerance" on a band holding **1 worked name out of 29** — a pass claimed on no information, which
reads as reassurance and is worse than no answer. The worked-count floor exists because of it.

**HOW VERIFIED.** The falsifier is shown to FIRE: simulating a human who works only `own` names in
the 101–200 band produces a **+45% gap and a FALSIFIED verdict**. A falsifier that cannot fail is
decoration. Re-run `scripts/cohort_anchoring_falsifier.py` as dossiers accumulate.
